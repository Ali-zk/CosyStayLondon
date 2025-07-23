from django.contrib import admin
from .models import Property, PropertyImage, Booking

class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'location', 'price_per_night', 'is_available', 'created_at')
    list_filter = ('is_available', 'location', 'price_per_night')
    search_fields = ('title', 'description', 'location', 'address')
    inlines = [PropertyImageInline]

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('property', 'user', 'check_in_date', 'check_out_date', 'total_price', 'is_confirmed', 'created_at')
    list_filter = ('is_confirmed', 'check_in_date', 'check_out_date')
    search_fields = ('property__title', 'user__username')
    list_editable = ('is_confirmed',)