# shop/models.py
from django.db import models
from django.conf import settings # For accessing User model

class Property(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_properties')
    title = models.CharField(max_length=200)
    description = models.TextField()
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2) # Or price_per_month
    location = models.CharField(max_length=255) # City, neighborhood
    address = models.CharField(max_length=255, blank=True, null=True) # Exact address
    number_of_beds = models.IntegerField(default=1)
    number_of_baths = models.DecimalField(max_digits=3, decimal_places=1, default=1.0)
    area_sqft = models.IntegerField(blank=True, null=True)
    available_from = models.DateField()
    available_to = models.DateField(blank=True, null=True) # For long-term rentals or availability range
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Properties"

class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='property_images/')
    caption = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Image for {self.property.title}"

# Booking model with new fields (full_name and number_of_guests)
class Booking(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings_made')
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    number_of_guests = models.PositiveIntegerField(default=1) # New field
    full_name = models.CharField(max_length=255) # New field
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    class Meta:
        unique_together = ('property', 'check_in_date', 'check_out_date')
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking for {self.property.title} by {self.user.email} from {self.check_in_date} to {self.check_out_date}"