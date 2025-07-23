from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils.dateparse import parse_date 
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import stripe
import json
import logging

from .models import Cart, CartItem, Order, OrderItem, Payment, PaymentWebhook
from .payment_service import stripe_service
from shop.models import Property, Booking

logger = logging.getLogger(__name__) 


@login_required
def add_from_session(request):
    """
    Reads booking information from session and adds it to user's cart.
    Then removes the information from session.
    This view is called (redirected) by shop.views.product_detail.
    """
    booking_data = request.session.get('temp_booking_data')

    if not booking_data:
        messages.error(request, "Booking information not found for adding to cart. Please try again from the property page.")
        return redirect('shop:product_list')

    property_id = booking_data.get('property_id')
    check_in_str = booking_data.get('check_in_date')
    check_out_str = booking_data.get('check_out_date')
    num_guests = booking_data.get('number_of_guests')
    full_name = booking_data.get('full_name')
    email = booking_data.get('email')
    phone_number = booking_data.get('phone_number')
    price_str = booking_data.get('price_at_addition')

    if not all([property_id, check_in_str, check_out_str, num_guests, price_str]):
        messages.error(request, "Booking information is incomplete. Please try again.")
        if 'temp_booking_data' in request.session:
            del request.session['temp_booking_data']
        return redirect('shop:product_list')

    try:
        property_obj = get_object_or_404(Property, pk=property_id)
        check_in_date = parse_date(check_in_str)
        check_out_date = parse_date(check_out_str)
        price_at_addition = Decimal(price_str)
        num_guests = int(num_guests)
    except (Property.DoesNotExist, ValueError, TypeError) as e:
        messages.error(request, f"Error processing booking information from session: {e}")
        if 'temp_booking_data' in request.session:
            del request.session['temp_booking_data']
        return redirect('shop:product_detail', pk=property_id) if property_id else redirect('shop:product_list')

    if not check_in_date or not check_out_date or check_in_date >= check_out_date:
        messages.error(request, "Booking dates are invalid. Check-out date must be after check-in date.")
        if 'temp_booking_data' in request.session:
            del request.session['temp_booking_data']
        return redirect('shop:product_detail', pk=property_obj.id)

    cart, _ = Cart.objects.get_or_create(user=request.user)

    conflicting_bookings_db = Booking.objects.filter(
        property=property_obj,
        check_in_date__lt=check_out_date,
        check_out_date__gt=check_in_date,
        status__in=['pending', 'confirmed']
    ).exists()

    if conflicting_bookings_db:
        messages.error(request, f"Unfortunately, property '{property_obj.title}' is no longer available for the selected dates (already booked by another user).")
        if 'temp_booking_data' in request.session:
            del request.session['temp_booking_data']
        return redirect('shop:product_detail', pk=property_obj.id)
    
    if check_in_date < property_obj.available_from or \
       (property_obj.available_to and check_out_date > property_obj.available_to):
        messages.error(request, f"Property '{property_obj.title}' is no longer available for your selected dates (outside the owner's availability window). Please choose different dates.")
        if 'temp_booking_data' in request.session:
            del request.session['temp_booking_data']
        return redirect('shop:product_detail', pk=property_obj.id)

    try:
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            property_item=property_obj,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            defaults={
                'number_of_guests': num_guests,
                'full_name_booking': full_name,
                'email_booking': email,
                'phone_number_booking': phone_number,
                'price_per_night_at_booking': price_at_addition,
                'quantity': 1
            }
        )
        if created:
            messages.success(request, f"Reservation for '{property_obj.title}' from {check_in_date.strftime('%Y-%m-%d')} to {check_out_date.strftime('%Y-%m-%d')} has been added to your cart.")
        else:
            cart_item.number_of_guests = num_guests
            cart_item.full_name_booking = full_name
            cart_item.email_booking = email
            cart_item.phone_number_booking = phone_number
            cart_item.price_per_night_at_booking = price_at_addition
            cart_item.save()
            messages.info(request, f"Reservation information for '{property_obj.title}' in your cart has been updated.")

    except Exception as e:
        messages.error(request, f"Error adding to cart: {e}")
        if 'temp_booking_data' in request.session:
            del request.session['temp_booking_data']
        return redirect('shop:product_detail', pk=property_obj.id)

    if 'temp_booking_data' in request.session:
        del request.session['temp_booking_data']
    request.session.modified = True

    return redirect('cart:view_cart')


@login_required
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    # Fetch cart items and prefetch related property and its images for efficiency
    cart_items = cart.items.all().select_related('property_item').prefetch_related('property_item__images')
    
    # Prepare cart data for Alpine.js
    cart_items_data = []
    for item in cart_items:
        # Get the first image, or a default placeholder if no images
        image_url = ''
        if item.property_item.images.first():
            image_url = item.property_item.images.first().image.url

        cart_items_data.append({
            'id': item.id,
            'title': item.property_item.title,
            'location': item.property_item.location,
            'image': image_url,
            'checkin': item.check_in_date.strftime('%Y-%m-%d'),
            'checkout': item.check_out_date.strftime('%Y-%m-%d'),
            'guests': item.number_of_guests,
            'nights': item.num_nights,
            'pricePerNight': str(item.price_per_night_at_booking), # Convert Decimal to string
            'totalPrice': str(item.total_price), # Convert Decimal to string
        })

    # Get contact info for pre-filling the form, if available
    billing_full_name = request.user.email if request.user.is_authenticated else ''
    billing_email = request.user.email if request.user.is_authenticated else ''
    # Assuming phone number is not directly on the User model for simplicity, or fetch if it is
    billing_phone = '' 

    return render(request, 'cart/cart.html', {
        'cart': cart,
        'cart_items': cart_items, # Keep for potential Django rendering
        'cart_items_json': cart_items_data, # Pass JSON data for Alpine.js
        'billing_full_name': billing_full_name,
        'billing_email': billing_email,
        'billing_phone': billing_phone,
    })


@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if request.method == 'POST':
        property_name = cart_item.property_item.title
        cart_item.delete()
        messages.info(request, f"Reservation for '{property_name}' has been removed from your cart.")
    else:
        messages.warning(request, "Invalid operation. Please use the appropriate button to remove items.")
    return redirect('cart:view_cart')


@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = cart.items.all().select_related('property_item')

    if not cart_items:
        messages.warning(request, 'Your cart is empty for checkout.')
        return redirect('cart:view_cart')

    if request.method == 'POST':
        billing_full_name = request.POST.get('full_name')
        billing_email = request.POST.get('email')
        billing_phone = request.POST.get('phone')
        billing_country = request.POST.get('country', 'DE')  # Default to Germany

        if not all([billing_full_name, billing_email, billing_phone]):
            messages.error(request, "Please enter all required contact information.")
            return render(request, 'cart/checkout.html', {
                'cart': cart,
                'cart_items': cart_items,
                'billing_full_name': billing_full_name,
                'billing_email': billing_email,
                'billing_phone': billing_phone,
                'countries': get_eu_countries(),
                'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
            })

        try:
            with transaction.atomic():
                # Validate availability
                for item in cart_items:
                    conflicting_bookings = Booking.objects.filter(
                        property=item.property_item,
                        check_in_date__lt=item.check_out_date,
                        check_out_date__gt=item.check_in_date,
                        status__in=['pending', 'confirmed']
                    ).exclude(pk=item.id if hasattr(item, 'id') else None).exists()

                    if conflicting_bookings:
                        messages.error(request, f"Unfortunately, property '{item.property_item.title}' is no longer available for dates {item.check_in_date.strftime('%Y-%m-%d')} to {item.check_out_date.strftime('%Y-%m-%d')}.")
                        return redirect('cart:view_cart')
                    
                    if not item.property_item.is_available or \
                       item.check_in_date < item.property_item.available_from or \
                       (item.property_item.available_to and item.check_out_date > item.property_item.available_to):
                        messages.error(request, f"Property '{item.property_item.title}' is no longer available for your selected dates.")
                        return redirect('cart:view_cart')

                # Create order
                order = Order.objects.create(
                    user=request.user,
                    total_amount=cart.total_price,
                    status='pending',
                    billing_full_name=billing_full_name,
                    billing_email=billing_email,
                    billing_phone=billing_phone,
                )

                # Create order items
                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        property_item=item.property_item,
                        quantity=item.quantity,
                        check_in_date=item.check_in_date,
                        check_out_date=item.check_out_date,
                        number_of_guests=item.number_of_guests,
                        full_name_booking=item.full_name_booking,
                        email_booking=item.email_booking,
                        phone_number_booking=item.phone_number_booking,
                        price_per_night_at_order=item.price_per_night_at_booking
                    )

                # Create Stripe Payment Intent
                payment_result = stripe_service.create_payment_intent(
                    order=order,
                    currency='eur',
                    billing_country=billing_country
                )

                if payment_result['success']:
                    # Clear cart
                    CartItem.objects.filter(cart=cart).delete()
                    
                    # Redirect to payment page
                    return redirect('cart:payment_page', order_id=order.id)
                else:
                    # Payment intent creation failed
                    order.status = 'failed'
                    order.save()
                    messages.error(request, f"Error creating payment: {payment_result.get('error', 'Unknown error')}")
                    return redirect('cart:view_cart')
            
        except Exception as e:
            logger.error(f"Checkout error: {e}")
            messages.error(request, f"An error occurred while finalizing the order: {e}")
            return redirect('cart:view_cart')
            
    return render(request, 'cart/checkout.html', {
        'cart': cart,
        'cart_items': cart_items,
        'billing_full_name': request.user.email if request.user.is_authenticated else '',
        'billing_email': request.user.email if request.user.is_authenticated else '',
        'billing_phone': '',
        'billing_country': 'DE',  # Default country
        'countries': get_eu_countries(),
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
    })


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at').prefetch_related('order_items__property_item', 'payments')
    return render(request, 'cart/my_orders.html', {'orders': orders})


def get_eu_countries():
    """Get list of European countries for billing"""
    return [
        ('AT', 'Austria'),
        ('BE', 'Belgium'),
        ('BG', 'Bulgaria'),
        ('HR', 'Croatia'),
        ('CY', 'Cyprus'),
        ('CZ', 'Czech Republic'),
        ('DK', 'Denmark'),
        ('EE', 'Estonia'),
        ('FI', 'Finland'),
        ('FR', 'France'),
        ('DE', 'Germany'),
        ('GR', 'Greece'),
        ('HU', 'Hungary'),
        ('IE', 'Ireland'),
        ('IT', 'Italy'),
        ('LV', 'Latvia'),
        ('LT', 'Lithuania'),
        ('LU', 'Luxembourg'),
        ('MT', 'Malta'),
        ('NL', 'Netherlands'),
        ('PL', 'Poland'),
        ('PT', 'Portugal'),
        ('RO', 'Romania'),
        ('SK', 'Slovakia'),
        ('SI', 'Slovenia'),
        ('ES', 'Spain'),
        ('SE', 'Sweden'),
        ('GB', 'United Kingdom'),
        ('CH', 'Switzerland'),
        ('NO', 'Norway'),
    ]


@login_required
def payment_page(request, order_id):
    """Payment page with Stripe Elements"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Get the payment intent
    try:
        payment = order.payments.filter(status__in=['pending', 'processing']).first()
        if not payment:
            messages.error(request, 'Payment session not found.')
            return redirect('cart:my_orders')
            
        # Get client secret from Stripe
        try:
            intent = stripe.PaymentIntent.retrieve(payment.stripe_payment_intent_id)
            client_secret = intent.client_secret
        except stripe.error.StripeError:
            client_secret = None
            messages.error(request, 'Error loading payment information.')
            
        return render(request, 'cart/payment.html', {
            'order': order,
            'payment': payment,
            'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
            'client_secret': client_secret,
        })
        
    except Exception as e:
        logger.error(f"Payment page error for order {order_id}: {e}")
        messages.error(request, 'Error loading payment page.')
        return redirect('cart:my_orders')


@login_required
@require_POST
def confirm_payment(request):
    """AJAX endpoint to confirm payment"""
    try:
        data = json.loads(request.body)
        payment_intent_id = data.get('payment_intent_id')
        
        if not payment_intent_id:
            return JsonResponse({'success': False, 'error': 'Payment intent ID required'})
        
        # Confirm payment with Stripe service
        result = stripe_service.confirm_payment(payment_intent_id)
        
        if result['success']:
            if result.get('requires_action'):
                return JsonResponse({
                    'success': True,
                    'requires_action': True,
                    'client_secret': result.get('client_secret')
                })
            else:
                # Create bookings after successful payment
                payment = result['payment']
                for order_item in payment.order.order_items.all():
                    Booking.objects.update_or_create(
                        property=order_item.property_item,
                        user=payment.order.user,
                        check_in_date=order_item.check_in_date,
                        check_out_date=order_item.check_out_date,
                        defaults={
                            'number_of_guests': order_item.number_of_guests,
                            'full_name': order_item.full_name_booking,
                            'email': order_item.email_booking,
                            'phone_number': order_item.phone_number_booking,
                            'total_price': order_item.item_total_price,
                            'status': 'confirmed',
                            'is_confirmed': True,
                        }
                    )
                
                return JsonResponse({
                    'success': True,
                    'payment_status': result['status'],
                    'redirect_url': '/cart/payment-success/'
                })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Payment confirmation failed')
            })
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        logger.error(f"Payment confirmation error: {e}")
        return JsonResponse({'success': False, 'error': 'Server error'})


@login_required
def payment_success(request):
    """Payment success page"""
    return render(request, 'cart/payment_success.html')


@login_required
def payment_failed(request):
    """Payment failed page"""
    return render(request, 'cart/payment_failed.html')


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Handle Stripe webhooks for payment events"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        logger.error("Invalid payload in Stripe webhook")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature in Stripe webhook")
        return HttpResponse(status=400)
    
    # Log webhook event
    webhook_log = PaymentWebhook.objects.create(
        provider='stripe',
        event_type=event['type'],
        event_id=event['id'],
        raw_data=event
    )
    
    try:
        # Handle the event
        result = stripe_service.handle_webhook_event(event['type'], event['data'])
        
        if result['success']:
            webhook_log.status = 'processed'
            webhook_log.processed_at = timezone.now()
        else:
            webhook_log.status = 'failed'
            webhook_log.error_message = result.get('error', 'Unknown error')
            
        webhook_log.save()
        
        return HttpResponse(status=200)
        
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        webhook_log.status = 'failed'
        webhook_log.error_message = str(e)
        webhook_log.save()
        return HttpResponse(status=500)