from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import RegexValidator

class UserType(models.IntegerChoices):

    customer = 1 ,'customer'
    admin = 2, 'admin'

 
class UserManager(BaseUserManager):
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("The Email must be set"))

        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_verified", False)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_verified", True)

        if not extra_fields.get("is_staff"):
            raise ValueError(_("Superuser must have is_staff=True."))
        if not extra_fields.get("is_superuser"):
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model that uses email instead of username.
    """
    email = models.EmailField(_("email address"), unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    type = models.BigIntegerField(choices=UserType.choices, default=UserType.customer.value)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

# Create a Profile class
class Profile(models.Model):
    """
    This is a Profile model to complete user's information.
    It gets email from User model and then put it in the user
    variable below.
    """

    user = models.OneToOneField("User", on_delete=models.CASCADE)
    username = models.CharField(max_length=100)
    full_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=11, validators=[
        RegexValidator(
            regex=r"^09\d{9}$",
            message="Enter a valid Iranian cellphone number.",
            code="invalid_phone_number",
        ),
    ])
    image = models.ImageField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.email
    
    def get_full_name(self):
        return f"{self.full_name} - {self.created_date}"
    
# Create profile for a new user
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Ensures a Profile exists for every User.
    If a User is newly created, it ensures an empty Profile record is there.
    It does NOT set initial data from the form; the form's save method will handle that.
    """
    if created:
        Profile.objects.get_or_create(user=instance)
