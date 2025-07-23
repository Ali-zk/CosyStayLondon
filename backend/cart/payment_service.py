# cart/payment_service.py
import stripe
import logging
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from typing import Dict, Any, Optional, Tuple
from .models import Payment, Order, PaymentRefund

logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripePaymentService:
    """Service class for handling Stripe payments with European compliance"""
    
    def __init__(self):
        self.stripe = stripe
        
    def get_vat_rate(self, country_code: str) -> Decimal:
        """Get VAT rate for a country"""
        return Decimal(str(settings.EU_VAT_RATES.get(country_code, 0)))
    
    def calculate_vat(self, amount: Decimal, country_code: str) -> Tuple[Decimal, Decimal]:
        """Calculate VAT amount and net amount"""
        vat_rate = self.get_vat_rate(country_code)
        # Amount includes VAT, calculate net and VAT amounts
        vat_amount = amount * vat_rate / (1 + vat_rate)
        net_amount = amount - vat_amount
        return vat_amount, net_amount
    
    def create_payment_intent(
        self, 
        order: Order, 
        payment_method_types: list = None,
        currency: str = 'eur',
        billing_country: str = None
    ) -> Dict[str, Any]:
        """Create Stripe Payment Intent with European compliance"""
        
        if payment_method_types is None:
            # Default European payment methods
            payment_method_types = ['card', 'sepa_debit', 'klarna', 'ideal', 'bancontact']
        
        try:
            # Calculate VAT if country provided
            vat_amount = Decimal('0.00')
            vat_rate = Decimal('0.0000')
            
            if billing_country:
                vat_rate = self.get_vat_rate(billing_country)
                vat_amount, _ = self.calculate_vat(order.total_amount, billing_country)
            
            # Convert to cents (Stripe uses smallest currency unit)
            amount_cents = int(order.total_amount * 100)
            
            # Create Payment Intent
            intent = self.stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency.lower(),
                payment_method_types=payment_method_types,
                metadata={
                    'order_id': str(order.id),
                    'user_email': order.billing_email,
                    'vat_rate': str(vat_rate),
                    'vat_amount': str(vat_amount),
                    'billing_country': billing_country or '',
                },
                receipt_email=order.billing_email,
                description=f'Property Booking - Order #{order.id}',
                # European compliance settings
                automatic_payment_methods={
                    'enabled': True,
                    'allow_redirects': 'always'  # For European payment methods
                },
                # Enable SCA (Strong Customer Authentication)
                confirmation_method='automatic',
                confirm=False,
            )
            
            # Create Payment record
            payment = Payment.objects.create(
                order=order,
                amount=order.total_amount,
                currency=currency.upper(),
                payment_method='stripe_card',  # Will be updated based on actual method used
                stripe_payment_intent_id=intent.id,
                billing_country=billing_country,
                vat_rate=vat_rate,
                vat_amount=vat_amount,
                sca_required=True,  # Assume SCA required for European transactions
                provider_response=intent
            )
            
            logger.info(f"Payment intent created for order {order.id}: {intent.id}")
            
            return {
                'success': True,
                'payment_intent': intent,
                'payment_id': payment.id,
                'client_secret': intent.client_secret,
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment intent for order {order.id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'stripe_error'
            }
        except Exception as e:
            logger.error(f"Unexpected error creating payment intent for order {order.id}: {e}")
            return {
                'success': False,
                'error': 'An unexpected error occurred',
                'error_type': 'system_error'
            }
    
    def confirm_payment(self, payment_intent_id: str) -> Dict[str, Any]:
        """Confirm a payment and update order status"""
        try:
            # Retrieve the payment intent
            intent = self.stripe.PaymentIntent.retrieve(payment_intent_id)
            
            # Find the payment record
            try:
                payment = Payment.objects.get(stripe_payment_intent_id=payment_intent_id)
            except Payment.DoesNotExist:
                logger.error(f"Payment record not found for intent {payment_intent_id}")
                return {
                    'success': False,
                    'error': 'Payment record not found'
                }
            
            # Update payment status based on intent status
            if intent.status == 'succeeded':
                payment.status = 'completed'
                payment.completed_at = timezone.now()
                payment.sca_completed = True
                
                # Update order status
                payment.order.status = 'confirmed'
                payment.order.save()
                
                # Update all bookings related to this order
                for order_item in payment.order.order_items.all():
                    # Update the booking status in shop.models.Booking
                    from shop.models import Booking
                    bookings = Booking.objects.filter(
                        property=order_item.property_item,
                        user=payment.order.user,
                        check_in_date=order_item.check_in_date,
                        check_out_date=order_item.check_out_date,
                        status='pending'
                    )
                    bookings.update(status='confirmed', is_confirmed=True)
                
                logger.info(f"Payment confirmed for order {payment.order.id}")
                
            elif intent.status == 'requires_action':
                payment.status = 'processing'
                payment.sca_required = True
                
            elif intent.status in ['canceled', 'payment_failed']:
                payment.status = 'failed'
                payment.failure_reason = intent.last_payment_error.get('message', '') if intent.last_payment_error else ''
                
                # Update order status
                payment.order.status = 'failed'
                payment.order.save()
            
            # Update payment method based on actual method used
            if intent.charges and intent.charges.data:
                charge = intent.charges.data[0]
                payment_method = charge.payment_method_details.type
                payment.payment_method = f'stripe_{payment_method}'
            
            payment.provider_response = intent
            payment.save()
            
            return {
                'success': True,
                'payment': payment,
                'status': intent.status,
                'requires_action': intent.status == 'requires_action',
                'client_secret': intent.client_secret if intent.status == 'requires_action' else None
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error confirming payment {payment_intent_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'stripe_error'
            }
        except Exception as e:
            logger.error(f"Unexpected error confirming payment {payment_intent_id}: {e}")
            return {
                'success': False,
                'error': 'An unexpected error occurred',
                'error_type': 'system_error'
            }
    
    def create_refund(self, payment: Payment, amount: Optional[Decimal] = None, reason: str = '') -> Dict[str, Any]:
        """Create a refund for a payment"""
        try:
            refund_amount = amount or payment.amount
            refund_amount_cents = int(refund_amount * 100)
            
            # Create Stripe refund
            refund = self.stripe.Refund.create(
                payment_intent=payment.stripe_payment_intent_id,
                amount=refund_amount_cents,
                reason='requested_by_customer',
                metadata={
                    'order_id': str(payment.order.id),
                    'reason': reason,
                }
            )
            
            # Create refund record
            payment_refund = PaymentRefund.objects.create(
                payment=payment,
                amount=refund_amount,
                reason=reason,
                stripe_refund_id=refund.id,
                status='processing',
                provider_response=refund
            )
            
            logger.info(f"Refund created for payment {payment.id}: {refund.id}")
            
            return {
                'success': True,
                'refund': refund,
                'refund_id': payment_refund.id,
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating refund for payment {payment.id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'stripe_error'
            }
        except Exception as e:
            logger.error(f"Unexpected error creating refund for payment {payment.id}: {e}")
            return {
                'success': False,
                'error': 'An unexpected error occurred',
                'error_type': 'system_error'
            }
    
    def handle_webhook_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Stripe webhook events"""
        try:
            if event_type == 'payment_intent.succeeded':
                payment_intent = event_data['object']
                result = self.confirm_payment(payment_intent['id'])
                return result
                
            elif event_type == 'payment_intent.payment_failed':
                payment_intent = event_data['object']
                try:
                    payment = Payment.objects.get(stripe_payment_intent_id=payment_intent['id'])
                    payment.status = 'failed'
                    payment.failure_reason = payment_intent.get('last_payment_error', {}).get('message', '')
                    payment.save()
                    
                    # Update order status
                    payment.order.status = 'failed'
                    payment.order.save()
                    
                    logger.info(f"Payment failed for order {payment.order.id}")
                    
                except Payment.DoesNotExist:
                    logger.warning(f"Payment not found for failed intent {payment_intent['id']}")
                
                return {'success': True, 'processed': True}
                
            elif event_type == 'charge.dispute.created':
                # Handle chargebacks
                charge = event_data['object']
                logger.warning(f"Chargeback created for charge {charge['id']}")
                return {'success': True, 'processed': True}
                
            else:
                logger.info(f"Unhandled webhook event type: {event_type}")
                return {'success': True, 'processed': False}
                
        except Exception as e:
            logger.error(f"Error handling webhook event {event_type}: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Singleton instance
stripe_service = StripePaymentService()