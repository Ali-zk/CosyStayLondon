from django import forms
from shop.models import Property, PropertyImage

class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        # فیلدهایی که می‌خواهید در فرم نمایش داده شوند
        fields = [
            'owner', 'title', 'description', 'price_per_night', 'location',
            'address', 'number_of_beds', 'number_of_baths', 'area_sqft',
            'available_from', 'available_to', 'is_available'
        ]
        widgets = {
            'available_from': forms.DateInput(attrs={'type': 'date'}),
            'available_to': forms.DateInput(attrs={'type': 'date'}),
        }

class PropertyImageForm(forms.ModelForm):
    class Meta:
        model = PropertyImage
        fields = ['image', 'caption']

# This formset will allow handling multiple images in one form
PropertyImageFormSet = forms.inlineformset_factory(
    Property,
    PropertyImage,
    form=PropertyImageForm,
    extra=1,  # Number of empty forms to display
    can_delete=True
)