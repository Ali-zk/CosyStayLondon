from django.contrib.auth import forms as auth_forms
from django import forms
from django.utils.translation import gettext_lazy as _
from accounts.models import User, Profile, UserType
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
class AdminPasswordChangeForm(auth_forms.PasswordChangeForm):
    error_messages = {
       "password_inccorect": _(
           "your old password was entered incorrectly.please enter it again."
        ),
        'password_mismatch': _('the two password fields didnt match.'),
    }

    def __init__(self , *args , **kwargs):
        super().__init__(*args,**kwargs)
        self.fields['old_password'].widget.attrs['class'] = 'form-control text-center'
        self.fields['new_password1'].widget.attrs['class'] = 'form-control text-center'
        self.fields['new_password2'].widget.attrs['class'] = 'form-control text-center'
        
        self.fields['old_password'].widget.attrs['placeholder'] = 'Enter your old password'
        self.fields['new_password1'].widget.attrs['placeholder'] = 'Enter your new password'
        self.fields['new_password2'].widget.attrs['placeholder'] = 'Re-enter your new password'

        
# User Creation form
class UserProfileCreationForm(forms.ModelForm):
    """
    Custom form for creating new users. Only includes User model fields.
    Profile creation is handled by a post_save signal.
    """
    email = forms.EmailField(label="Email address", max_length=255,
                             widget=forms.EmailInput(attrs={'placeholder': 'Enter email address'}))
    is_staff = forms.BooleanField(label="Is Staff", required=False)
    is_active = forms.BooleanField(label="Is Active", required=False, initial=True)
    is_verified = forms.BooleanField(label="Is Verified", required=False, initial=False) # Added as requested

    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter password'}),
        strip=False,
    )
    password2 = forms.CharField(
        label="Password confirmation",
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password'}),
        strip=False,
    )

    class Meta:
        model = User
        fields = ('email', 'is_staff', 'is_active', 'is_verified') 

    def clean_password2(self):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')

        if password and password2 and password != password2:
            raise forms.ValidationError("Passwords don't match")
        
        if password:
            try:
                validate_password(password, self.instance)
            except ValidationError as e:
                self.add_error('password', e)

        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.is_verified = self.cleaned_data["is_verified"] 
        
        if commit:
            user.save() 
        return user


class UserProfileChangeForm(forms.ModelForm):
    """
    A custom form for updating existing users and their profiles.
    This form handles fields from both User and Profile models.
    """
    # User model fields
    email = forms.EmailField(label="Email address", max_length=255,
                             widget=forms.EmailInput(attrs={'placeholder': 'Enter email address'}))
    is_staff = forms.BooleanField(label="Is Staff", required=False)
    is_active = forms.BooleanField(label="Is Active", required=False)
    is_verified = forms.BooleanField(label="Is Verified", required=False)
    type = forms.ChoiceField(label="User Type", choices=UserType.choices)


    # Profile model fields
    username = forms.CharField(label="Profile Username", max_length=100, required=True,
                               widget=forms.TextInput(attrs={'placeholder': 'Enter profile username'}))
    full_name = forms.CharField(label="Full Name", max_length=200, required=False,
                                widget=forms.TextInput(attrs={'placeholder': 'Enter full name'}))
    phone_number = forms.CharField(label="Phone Number", max_length=11, required=False,
                                   widget=forms.TextInput(attrs={'placeholder': 'Enter phone number (e.g., 09123456789)'}))
    image = forms.ImageField(label="Profile Image", required=False)
    address = forms.CharField(label="Address", widget=forms.Textarea(attrs={'rows': 3}), required=False)
    description = forms.CharField(label="Description", widget=forms.Textarea(attrs={'rows': 3}), required=False)

    class Meta:
        model = User
        fields = ('email', 'is_staff', 'is_active', 'is_verified', 'type', 'groups', 'user_permissions')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance: 
            self.fields['email'].initial = self.instance.email
            self.fields['is_staff'].initial = self.instance.is_staff
            self.fields['is_active'].initial = self.instance.is_active
            self.fields['is_verified'].initial = self.instance.is_verified
            self.fields['type'].initial = self.instance.type

            if hasattr(self.instance, 'profile'):
                profile = self.instance.profile
                self.fields['username'].initial = profile.username
                self.fields['full_name'].initial = profile.full_name
                self.fields['phone_number'].initial = profile.phone_number
                self.fields['image'].initial = profile.image
                self.fields['address'].initial = profile.address
                self.fields['description'].initial = profile.description

        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.EmailInput, forms.NumberInput, forms.Select)):
                field.widget.attrs.update({'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2.5'})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2.5'})
            elif isinstance(field.widget, forms.CheckboxInput):
                 field.widget.attrs.update({'class': 'h-4 w-4 text-blue-600 border-gray-300 rounded'})


    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_verified = self.cleaned_data['is_verified'] # Update is_verified
        user.type = self.cleaned_data['type'] # Update user type

        if commit:
            user.save() # Save User instance
            # Update groups and user_permissions if present in the form (handled by super().save())
            self.save_m2m() # Important for ManyToMany fields like groups/user_permissions

            # Update Profile instance
            profile, created = Profile.objects.get_or_create(user=user) # Get or create profile
            profile.username = self.cleaned_data['username']
            profile.full_name = self.cleaned_data['full_name']
            profile.phone_number = self.cleaned_data['phone_number']
            profile.image = self.cleaned_data['image']
            profile.address = self.cleaned_data['address']
            profile.description = self.cleaned_data['description']
            profile.save()
        return user

class MyProfileForm(forms.ModelForm):
    """
    Form for the current user's profile, explicitly for the Profile model.
    """
    class Meta:
        model = Profile
        fields = ['username', 'full_name', 'phone_number', 'image', 'address', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply styling to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.EmailInput, forms.NumberInput, forms.Select)):
                field.widget.attrs.update({'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2.5'})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2.5', 'rows': 3})
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'mt-1 block w-full text-gray-700 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'})