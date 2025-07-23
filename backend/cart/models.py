# cart/models.py
from django.db import models
from django.conf import settings
from decimal import Decimal # برای محاسبات دقیق پولی
from django.core.exceptions import ValidationError
from django.utils import timezone

# مهم: اطمینان حاصل کنید که مدل Property از اپ shop به درستی ایمپورت شده است.
# اگر اپ shop شما نام دیگری دارد یا مدل Property نام دیگری دارد، آن را تصحیح کنید.
from shop.models import Property

class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="کاربر",
        related_name="cart" # اضافه کردن related_name برای دسترسی راحت‌تر از User به Cart
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ آخرین به‌روزرسانی")

    def __str__(self):
        return f"سبد خرید کاربر: {self.user.email}"

    @property
    def total_price(self):
        """محاسبه مجموع قیمت کل آیتم‌های رزرو در سبد."""
        total = sum(item.total_price for item in self.items.all()) # استفاده از related_name 'items'
        return total if total is not None else Decimal('0.00')

    @property
    def item_count(self):
        """تعداد آیتم‌های موجود در سبد خرید."""
        return self.items.count() # استفاده از related_name 'items'

    class Meta:
        verbose_name = "سبد خرید"
        verbose_name_plural = "سبدهای خرید"
        ordering = ['-created_at']


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        verbose_name="سبد خرید",
        related_name="items" # related_name برای دسترسی از Cart به CartItem ها
    )
    # این فیلد باید به مدل خانه/ملک شما در اپ shop اشاره کند.
    property_item = models.ForeignKey(
        Property,
        on_delete=models.CASCADE, # یا SET_NULL اگر می‌خواهید آیتم باقی بماند حتی اگر ملک حذف شود (نیاز به null=True)
        verbose_name="ملک (خانه)",
        related_name="cart_items"
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantity (usually 1 for reservation)")

    # اطلاعات رزرو
    check_in_date = models.DateField(verbose_name="Check-in Date")
    check_out_date = models.DateField(verbose_name="Check-out Date")
    number_of_guests = models.PositiveIntegerField(default=1, verbose_name="تعداد مهمانان")

    # اطلاعات رزرو کننده (اختیاری، می‌تواند از کاربر لاگین شده یا فرم گرفته شود)
    full_name_booking = models.CharField(max_length=255, verbose_name="Full Name of Booker", blank=True, null=True)
    email_booking = models.EmailField(verbose_name="Booker Email", blank=True, null=True)
    phone_number_booking = models.CharField(max_length=20, verbose_name="Booker Phone Number", blank=True, null=True)

    price_per_night_at_booking = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="قیمت هر شب (در زمان افزودن به سبد)"
    )
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ اضافه شدن")

    def __str__(self):
        property_title = self.property_item.title if self.property_item else "ملک نامشخص"
        return f"رزرو {property_title} از {self.check_in_date} تا {self.check_out_date}"

    def clean(self):
        """اعتبارسنجی‌های سطح مدل."""
        super().clean()
        if self.check_in_date and self.check_out_date:
            if self.check_in_date >= self.check_out_date:
                raise ValidationError("تاریخ خروج باید بعد از تاریخ ورود باشد.")
            if self.check_in_date < timezone.now().date():
                raise ValidationError("تاریخ ورود نمی‌تواند در گذشته باشد.")
        if self.quantity <= 0:
            raise ValidationError("تعداد باید حداقل ۱ باشد.")
        if self.number_of_guests <= 0:
            raise ValidationError("تعداد مهمانان باید حداقل ۱ باشد.")

    @property
    def num_nights(self):
        """Calculate the number of nights of stay."""
        if self.check_in_date and self.check_out_date and self.check_out_date > self.check_in_date:
            return (self.check_out_date - self.check_in_date).days
        return 0

    @property
    def total_price(self):
        """محاسبه قیمت کل این آیتم رزرو."""
        if self.price_per_night_at_booking is not None and self.num_nights > 0:
            return self.price_per_night_at_booking * Decimal(self.num_nights) * Decimal(self.quantity)
        return Decimal('0.00')

    class Meta:
        verbose_name = "آیتم سبد خرید (رزرو)"
        verbose_name_plural = "آیتم‌های سبد خرید (رزروها)"
        # جلوگیری از رزروهای کاملا یکسان (همان ملک، همان تاریخ‌ها) در سبد یک کاربر
        unique_together = ('cart', 'property_item', 'check_in_date', 'check_out_date')
        ordering = ['-added_at']


class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # اگر کاربر حذف شد، سفارش باقی بماند
        null=True, # اجازه می‌دهد کاربر null باشد (مثلا برای سفارش‌های مهمان)
        blank=True,
        verbose_name="کاربر",
        related_name="orders"
    )
    # اطلاعات تماس برای سفارش (حتی اگر کاربر لاگین نکرده باشد یا متفاوت باشد)
    billing_full_name = models.CharField(max_length=255, verbose_name="نام کامل (صورتحساب)", blank=True)
    billing_email = models.EmailField(verbose_name="ایمیل (صورتحساب)", blank=True)
    billing_phone = models.CharField(max_length=20, verbose_name="تلفن (صورتحساب)", blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت سفارش")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ آخرین به‌روزرسانی")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="مبلغ کل")

    STATUS_CHOICES = [
        ('pending', 'در انتظار پرداخت/تایید'),
        ('processing', 'در حال پردازش'), # برای مواردی که نیاز به تایید دستی است
        ('confirmed', 'تایید شده/پرداخت شده'),
        ('completed', 'تکمیل شده (اقامت انجام شد)'),
        ('cancelled', 'لغو شده'),
        ('failed', 'ناموفق'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="وضعیت سفارش"
    )
    # می‌توانید فیلدهای دیگری مانند آدرس IP، شناسه تراکنش پرداخت و ... اضافه کنید.
    transaction_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="شناسه تراکنش پرداخت")

    def __str__(self):
        return f"سفارش #{self.id} - کاربر: {self.user.email if self.user else self.billing_email or 'مهمان'}"

    def update_total_amount(self):
        """مبلغ کل سفارش را بر اساس آیتم‌هایش به‌روزرسانی می‌کند."""
        self.total_amount = sum(item.item_total_price for item in self.order_items.all()) # استفاده از related_name
        self.save(update_fields=['total_amount'])

    class Meta:
        verbose_name = "سفارش (رزرو)"
        verbose_name_plural = "سفارش‌ها (رزروها)"
        ordering = ['-created_at']


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE, # اگر سفارش حذف شد، آیتم‌هایش هم حذف شوند
        verbose_name="سفارش",
        related_name="order_items" # نام مناسب‌تر برای related_name
    )
    property_item = models.ForeignKey(
        Property,
        on_delete=models.SET_NULL, # اگر ملک حذف شد، آیتم سفارش باقی بماند و به ملک null اشاره کند
        null=True,
        blank=False, # ملک باید مشخص باشد، مگر اینکه حذف شده باشد
        verbose_name="ملک (خانه)",
        related_name="order_items_property" # یک related_name متفاوت از CartItem
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantity (usually 1 for reservation)")

    # Finalized reservation information at order time
    check_in_date = models.DateField(verbose_name="Check-in Date")
    check_out_date = models.DateField(verbose_name="Check-out Date")
    number_of_guests = models.PositiveIntegerField(verbose_name="Number of Guests")
    
    # Contact information of the booker for this specific item (can be copied from main order or CartItem)
    full_name_booking = models.CharField(max_length=255, verbose_name="Full Name of Booker", blank=True, null=True)
    email_booking = models.EmailField(verbose_name="Booker Email", blank=True, null=True)
    phone_number_booking = models.CharField(max_length=20, verbose_name="Booker Phone Number", blank=True, null=True)

    price_per_night_at_order = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Price per Night (at order time)"
    )

    def __str__(self):
        property_title = self.property_item.title if self.property_item else "Deleted Property"
        return f"Reservation {property_title} in order #{self.order.id}"

    @property
    def num_nights(self):
        """Calculate the number of nights of stay."""
        if self.check_in_date and self.check_out_date and self.check_out_date > self.check_in_date:
            return (self.check_out_date - self.check_in_date).days
        return 0

    @property
    def item_total_price(self):
        """Calculate the total price of this order item."""
        if self.price_per_night_at_order is not None and self.num_nights > 0:
            return self.price_per_night_at_order * Decimal(self.num_nights) * Decimal(self.quantity)
        return Decimal('0.00')

    class Meta:
        verbose_name = "Order Item (Reservation)"
        verbose_name_plural = "Order Items (Reservations)"
        ordering = ['order', 'property_item']


class Payment(models.Model):
    """Payment model to track all payment transactions"""
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
        ('partially_refunded', 'Partially Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('stripe_card', 'Credit/Debit Card (Stripe)'),
        ('stripe_sepa', 'SEPA Direct Debit'),
        ('stripe_klarna', 'Klarna'),
        ('stripe_ideal', 'iDEAL'),
        ('stripe_bancontact', 'Bancontact'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    CURRENCY_CHOICES = [
        ('EUR', 'Euro (€)'),
        ('GBP', 'British Pound (£)'),
        ('USD', 'US Dollar ($)'),
        ('CHF', 'Swiss Franc'),
        ('NOK', 'Norwegian Krone'),
        ('SEK', 'Swedish Krona'),
        ('DKK', 'Danish Krone'),
    ]
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Order'
    )
    
    # Payment provider details
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    stripe_payment_method_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    paypal_transaction_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Payment details
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Payment Amount')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='EUR')
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # European compliance
    sca_required = models.BooleanField(default=False, verbose_name='Strong Customer Authentication Required')
    sca_completed = models.BooleanField(default=False, verbose_name='SCA Completed')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    # Billing information (for EU VAT compliance)
    billing_country = models.CharField(max_length=2, blank=True, null=True, help_text='ISO 2-letter country code')
    vat_rate = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('0.0000'), help_text='VAT rate applied')
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text='VAT amount')
    
    # Additional metadata
    failure_reason = models.TextField(blank=True, null=True)
    provider_response = models.JSONField(blank=True, null=True, help_text='Full response from payment provider')
    
    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stripe_payment_intent_id']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f'Payment #{self.id} - Order #{self.order.id} - {self.get_status_display()}'
    
    @property
    def is_successful(self):
        return self.status == 'completed'
    
    @property
    def net_amount(self):
        """Amount excluding VAT"""
        return self.amount - self.vat_amount


class PaymentRefund(models.Model):
    """Track payment refunds for cancelled bookings"""
    
    REFUND_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='refunds',
        verbose_name='Original Payment'
    )
    
    # Refund details
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Refund Amount')
    reason = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=REFUND_STATUS_CHOICES, default='pending')
    
    # Provider details
    stripe_refund_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    paypal_refund_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    # Additional metadata
    failure_reason = models.TextField(blank=True, null=True)
    provider_response = models.JSONField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Payment Refund'
        verbose_name_plural = 'Payment Refunds'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Refund #{self.id} - Payment #{self.payment.id} - {self.amount} {self.payment.currency}'


class PaymentWebhook(models.Model):
    """Log webhook events from payment providers"""
    
    WEBHOOK_STATUS_CHOICES = [
        ('received', 'Received'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
        ('ignored', 'Ignored'),
    ]
    
    provider = models.CharField(max_length=50, choices=[('stripe', 'Stripe'), ('paypal', 'PayPal')])
    event_type = models.CharField(max_length=100)
    event_id = models.CharField(max_length=255, unique=True)
    
    # Webhook data
    raw_data = models.JSONField()
    status = models.CharField(max_length=20, choices=WEBHOOK_STATUS_CHOICES, default='received')
    
    # Processing details
    processed_at = models.DateTimeField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    
    # Related objects (if identified)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Payment Webhook'
        verbose_name_plural = 'Payment Webhooks'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['provider', 'event_type']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f'{self.provider.title()} Webhook - {self.event_type} - {self.get_status_display()}'