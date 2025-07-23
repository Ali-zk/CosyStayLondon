# shop/forms.py

from django import forms
from .models import Property
from datetime import date, timedelta
from decimal import Decimal # Added

# Your current PropertyForm
class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = [
            'title', 'description', 'price_per_night', 'location', 'address',
            'number_of_beds', 'number_of_baths', 'area_sqft',
            'available_from', 'available_to', 'is_available'
        ]
        widgets = {
            'available_from': forms.DateInput(attrs={'type': 'date'}),
            'available_to': forms.DateInput(attrs={'type': 'date'}),
        }
        
# Booking form
class ProductBookingForm(forms.Form):
    check_in_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    check_out_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    number_of_guests = forms.IntegerField(min_value=1, max_value=10, widget=forms.NumberInput(attrs={'min': 1, 'max': 10}))
    full_name = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'placeholder': 'Enter your full name'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'your@example.com'}))
    phone_number = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'placeholder': 'e.g., +1 (555) 123-4567'}))
    property = forms.IntegerField(widget=forms.HiddenInput()) # To pass property_id

    def clean(self):
        cleaned_data = super().clean()
        check_in_date = cleaned_data.get('check_in_date')
        check_out_date = cleaned_data.get('check_out_date')
        property_id = cleaned_data.get('property')

        if check_in_date and check_out_date:
            if check_in_date < date.today():
                raise forms.ValidationError("Check-in date cannot be in the past.")

            if check_in_date >= check_out_date:
                raise forms.ValidationError("Check-out date must be after check-in date.")
            
            if property_id:
                try:
                    property_obj = Property.objects.get(pk=property_id)
                    if check_in_date < property_obj.available_from or \
                       (property_obj.available_to and check_out_date > property_obj.available_to):
                        raise forms.ValidationError(
                            f"The property is available from {property_obj.available_from} "
                            f"to {property_obj.available_to if property_obj.available_to else 'indefinitely'}."
                        )
                except Property.DoesNotExist:
                    raise forms.ValidationError("Selected property does not exist.")
        return cleaned_data
