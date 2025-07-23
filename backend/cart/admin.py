# cart/admin.py
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Cart, CartItem, Order, OrderItem

# کلاس Inline برای نمایش آیتم‌های سبد خرید در صفحه جزئیات سبد خرید
class CartItemInline(admin.TabularInline):
    model = CartItem
    fields = ('property_link_display', 'check_in_date', 'check_out_date', 'number_of_guests', 'price_per_night_at_booking', 'quantity', 'total_price_display')
    readonly_fields = ('property_link_display', 'price_per_night_at_booking', 'total_price_display')
    extra = 0
    raw_id_fields = ('property_item',) # استفاده از raw_id برای انتخاب Property

    def property_link_display(self, obj):
        if obj.property:
            # اطمینان حاصل کنید که app_label و model_name برای Property صحیح است
            link = reverse(f"admin:{obj.property_item._meta.app_label}_{obj.property_item._meta.model_name}_change", args=[obj.property_item.id])
            return format_html('<a href="{}">{}</a>', link, obj.property_item.title)
        return "ملک حذف شده یا نامشخص"
    property_link_display.short_description = 'ملک'

    def total_price_display(self, obj):
        return f"{obj.total_price:,.0f} تومان"
    total_price_display.short_description = 'مجموع آیتم'

    # برای جلوگیری از ویرایش مستقیم در اینلاین اگر منطق پیچیده‌ای دارید
    # def has_change_permission(self, request, obj=None):
    #     return False
    # def has_add_permission(self, request, obj=None):
    #     return False
    # def has_delete_permission(self, request, obj=None):
    #     return False


# کلاس ادمین برای مدل Cart
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_link_display', 'item_count_display', 'total_price_display', 'created_at', 'updated_at')
    list_filter = ('user', 'created_at', 'updated_at')
    search_fields = ('user__email', 'id')
    readonly_fields = ('id', 'user_link_display', 'created_at', 'updated_at', 'total_price_display', 'item_count_display')
    inlines = [CartItemInline]
    fieldsets = (
        (None, {'fields': ('user_link_display', 'created_at', 'updated_at')}),
        ('خلاصه سبد', {'fields': ('item_count_display', 'total_price_display')}),
    )

    def user_link_display(self, obj):
        if obj.user:
            link = reverse(f"admin:{obj.user._meta.app_label}_{obj.user._meta.model_name}_change", args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', link, obj.user.email)
        return "-"
    user_link_display.short_description = "کاربر"

    def total_price_display(self, obj):
        return f"{obj.total_price:,.0f} تومان"
    total_price_display.short_description = "مجموع قیمت سبد"

    def item_count_display(self, obj):
        return obj.item_count
    item_count_display.short_description = "تعداد آیتم‌ها"


# کلاس ادمین برای مدل CartItem (اگر می‌خواهید جداگانه هم مدیریت شود)
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart_link_display', 'property_link_display', 'check_in_date', 'check_out_date', 'number_of_guests', 'total_price_display', 'added_at')
    list_filter = ('cart__user', 'property_item', 'check_in_date', 'added_at')
    search_fields = ('property__title', 'cart__user__email', 'cart__id')
    readonly_fields = ('id', 'added_at', 'total_price_display')
    raw_id_fields = ('property_item', 'cart')
    autocomplete_fields = ['property_item', 'cart'] # برای جستجوی بهتر ForeignKey ها

    def cart_link_display(self, obj):
        if obj.cart:
            link = reverse(f"admin:{obj.cart._meta.app_label}_{obj.cart._meta.model_name}_change", args=[obj.cart.id])
            return format_html('<a href="{}">سبد #{} ({})</a>', link, obj.cart.id, obj.cart.user.email)
        return "-"
    cart_link_display.short_description = 'سبد خرید'

    def property_link_display(self, obj): # کپی از اینلاین برای نمایش یکسان
        if obj.property_item:
            link = reverse(f"admin:{obj.property_item._meta.app_label}_{obj.property_item._meta.model_name}_change", args=[obj.property_item.id])
            return format_html('<a href="{}">{}</a>', link, obj.property_item.title)
        return "ملک حذف شده یا نامشخص"
    property_link_display.short_description = 'ملک'

    def total_price_display(self, obj):
        return f"{obj.total_price:,.0f} تومان"
    total_price_display.short_description = "مجموع قیمت آیتم"


# کلاس Inline برای نمایش آیتم‌های سفارش در صفحه جزئیات سفارش
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    fields = ('property_link_display', 'check_in_date', 'check_out_date', 'number_of_guests', 'price_per_night_at_order', 'quantity', 'item_total_price_display')
    readonly_fields = ('property_link_display','price_per_night_at_order', 'item_total_price_display')
    extra = 0
    raw_id_fields = ('property_item',)

    def property_link_display(self, obj): # کپی از CartItemInline
        if obj.property:
            link = reverse(f"admin:{obj.property_item._meta.app_label}_{obj.property_item._meta.model_name}_change", args=[obj.property_item.id])
            return format_html('<a href="{}">{}</a>', link, obj.property_item.title)
        return "ملک حذف شده یا نامشخص"
    property_link_display.short_description = 'ملک'

    def item_total_price_display(self, obj):
        return f"{obj.item_total_price:,.0f} تومان"
    item_total_price_display.short_description = "مجموع قیمت آیتم"

# کلاس ادمین برای مدل Order
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_or_billing_info', 'created_at', 'total_amount_display', 'status', 'transaction_id')
    list_filter = ('status', 'user', 'created_at')
    search_fields = ('user__email', 'billing_email', 'billing_full_name', 'id', 'transaction_id')
    readonly_fields = ('id', 'user_link_display', 'created_at', 'updated_at', 'total_amount_display') # total_amount باید توسط متد محاسبه شود
    inlines = [OrderItemInline]
    date_hierarchy = 'created_at'
    actions = ['mark_confirmed', 'mark_processing', 'mark_completed', 'mark_cancelled', 'recalculate_total_amount']
    fieldsets = (
        ("اطلاعات سفارش", {'fields': ('id', 'status', 'transaction_id', 'created_at', 'updated_at')}),
        ("اطلاعات مشتری", {'fields': ('user_link_display', 'billing_full_name', 'billing_email', 'billing_phone')}),
        ("مبلغ", {'fields': ('total_amount_display',)}),
    )

    def user_or_billing_info(self, obj):
        if obj.user:
            return obj.user.email
        return obj.billing_email or obj.billing_full_name or "مهمان"
    user_or_billing_info.short_description = "مشتری"

    def user_link_display(self, obj):
        if obj.user:
            link = reverse(f"admin:{obj.user._meta.app_label}_{obj.user._meta.model_name}_change", args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', link, obj.user.email)
        return "-"
    user_link_display.short_description = "کاربر (در صورت وجود)"

    def total_amount_display(self, obj):
        return f"{obj.total_amount:,.0f} تومان"
    total_amount_display.short_description = "مبلغ کل سفارش"

    def mark_confirmed(self, request, queryset):
        updated_count = queryset.update(status='confirmed')
        self.message_user(request, f"{updated_count} سفارش به 'تایید شده/پرداخت شده' تغییر وضعیت دادند.")
    mark_confirmed.short_description = "علامت‌گذاری به عنوان تایید شده/پرداخت شده"

    def mark_processing(self, request, queryset):
        updated_count = queryset.update(status='processing')
        self.message_user(request, f"{updated_count} سفارش به 'در حال پردازش' تغییر وضعیت دادند.")
    mark_processing.short_description = "علامت‌گذاری به عنوان در حال پردازش"
    
    def mark_completed(self, request, queryset):
        updated_count = queryset.update(status='completed')
        self.message_user(request, f"{updated_count} سفارش به 'تکمیل شده' تغییر وضعیت دادند.")
    mark_completed.short_description = "علامت‌گذاری به عنوان تکمیل شده"

    def mark_cancelled(self, request, queryset):
        updated_count = queryset.update(status='cancelled')
        self.message_user(request, f"{updated_count} سفارش به 'لغو شده' تغییر وضعیت دادند.")
    mark_cancelled.short_description = "علامت‌گذاری به عنوان لغو شده"

    def recalculate_total_amount(self, request, queryset):
        for order_obj in queryset:
            order_obj.update_total_amount()
        self.message_user(request, f"مبلغ کل برای {queryset.count()} سفارش مجدداً محاسبه شد.")
    recalculate_total_amount.short_description = "محاسبه مجدد مبلغ کل سفارش(ها)"


# کلاس ادمین برای مدل OrderItem (اگر می‌خواهید جداگانه هم مدیریت شود)
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_link_display', 'property_link_display', 'check_in_date', 'check_out_date', 'number_of_guests', 'item_total_price_display')
    list_filter = ('order__user', 'property_item', 'check_in_date', 'order__status')
    search_fields = ('property__title', 'order__id', 'order__user__email')
    readonly_fields = ('id', 'item_total_price_display')
    raw_id_fields = ('order', 'property_item')
    autocomplete_fields = ['order', 'property_item']

    def order_link_display(self, obj):
        if obj.order:
            link = reverse(f"admin:{obj.order._meta.app_label}_{obj.order._meta.model_name}_change", args=[obj.order.id])
            return format_html('<a href="{}">سفارش #{}</a>', link, obj.order.id)
        return "-"
    order_link_display.short_description = 'سفارش'

    def property_link_display(self, obj): # کپی از CartItemAdmin
        if obj.property:
            link = reverse(f"admin:{obj.property_item._meta.app_label}_{obj.property_item._meta.model_name}_change", args=[obj.property_item.id])
            return format_html('<a href="{}">{}</a>', link, obj.property_item.title)
        return "ملک حذف شده یا نامشخص"
    property_link_display.short_description = 'ملک'

    def item_total_price_display(self, obj):
        return f"{obj.item_total_price:,.0f} تومان"
    item_total_price_display.short_description = "مجموع قیمت آیتم"