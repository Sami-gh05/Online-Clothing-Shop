"""
Admin registration for the custom user model.

Configures the Django admin interface for CustomUser.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser
from .forms import (
    CustomUserEditForm,
    CustomUserCreationForm,
)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    form = CustomUserEditForm
    add_form = CustomUserCreationForm
    model = CustomUser

    list_display = ("username", "email", "phone_number", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active", "groups")
    search_fields = ("username", "email", "phone_number")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Personal info",
            {"fields": ("first_name", "last_name", "email", "phone_number", "profile_picture")},
        ),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("username", "email", "password", "password2")}),
    )
