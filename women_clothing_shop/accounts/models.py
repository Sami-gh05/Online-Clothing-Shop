"""
Account-related data models.

Defines the custom user model used by the project.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):

    """
    Extends the default Django User model (AbstractUser).

    This allows us to use Django's built-in authentication
    while adding custom fields like a profile picture and phone number.
    """
    phone_number = models.CharField(max_length=15, null=True, blank=True, verbose_name="Phone Number")

    def __str__(self):
        """String representation, used in Admin panel and debugging."""
        return self.username