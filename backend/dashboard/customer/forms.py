# dashboard/customer/forms.py

from django import forms
from django.contrib.auth import forms as auth_forms
from django.utils.translation import gettext_lazy as _

# Assuming your Profile model is in accounts.models
from accounts.models import Profile

class CustomerPasswordChangeForm(auth_forms.PasswordChangeForm):
    """
    Form for changing password in the customer dashboard.
    """
    error_messages = {
        "password_incorrect": "Your old password was entered incorrectly. Please enter it again.",
        'password_mismatch': 'The two password fields did not match.',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply consistent Tailwind classes to all fields
        for field_name in self.fields:
            self.fields[field_name].widget.attrs['class'] = 'block py-2.5 px-0 w-full text-sm text-gray-900 bg-transparent border-0 border-b-2 border-gray-300 appearance-none focus:outline-none focus:ring-0 focus:border-blue-600 peer'

        self.fields['old_password'].widget.attrs['placeholder'] = 'Enter your old password'
        self.fields['new_password1'].widget.attrs['placeholder'] = 'Enter your new password'
        self.fields['new_password2'].widget.attrs['placeholder'] = 'Re-enter your new password'

class CustomerProfileEditForm(forms.ModelForm):
    """
    Form for editing customer's profile information.
    """
    class Meta:
        model = Profile
        fields = ['username', 'full_name', 'phone_number', 'image', 'address', 'description']
        # You might want to make some fields required=True here if they are in your model definition.
        # e.g., if username cannot be blank:
        # widgets = {
        #     'username': forms.TextInput(attrs={'required': True}),
        # }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply consistent Tailwind classes to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.EmailInput, forms.NumberInput, forms.Select)):
                field.widget.attrs.update({'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2.5'})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2.5', 'rows': 3})
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'mt-1 block w-full text-gray-700 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'})