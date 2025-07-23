from django.core.exceptions import ValidationError
from django.contrib.auth import forms as auth_forms


class AuthenticationForm(auth_forms.AuthenticationForm):
    def confirm_login_allowed(self, user):
        pass