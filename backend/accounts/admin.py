# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Profile

@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ('email', 'is_staff', 'is_active', 'is_verified', 'type', 'created_date')
    list_filter = ('is_staff', 'is_active', 'is_verified', 'type') 

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Information', {'fields': ('type',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login',)}),
    )

    search_fields = ('email',)

    ordering = ('email',)

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', ), 
        }),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'type', 'groups', 'user_permissions')}),
    )
    
    filter_horizontal = ('groups', 'user_permissions',) 
    
# Custom profile admin panel
@admin.register(Profile)
class CustomProfileAdmin(admin.ModelAdmin):
    """ Configure profile admin panel """
    list_display = ("user", "full_name", "phone_number")
    searching_field = ("user", "full_name", "phone_number")
    