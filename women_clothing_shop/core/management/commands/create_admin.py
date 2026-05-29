"""
Django management command to create or update a superuser account.

Creates a default superuser (admin) account or updates an existing one.
Supports environment variable configuration and optional password updates.
Idempotent operation - safe to run multiple times.
"""
import os
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create or update a default superuser (safe & idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("--username", default=os.getenv("DJ_ADMIN_USERNAME", "admin"))
        parser.add_argument("--email", default=os.getenv("DJ_ADMIN_EMAIL", "admin@example.com"))
        parser.add_argument("--password", default=os.getenv("DJ_ADMIN_PASSWORD", "admin123"))
        parser.add_argument(
            "--update-password",
            action="store_true",
            help="If user exists, update its password too.",
        )

    def handle(self, *args, **options):
        User = get_user_model()

        username = options["username"]
        email = options["email"]
        password = options["password"]
        update_password = options["update_password"]

        self.stdout.write(self.style.NOTICE("Running createadmin..."))

        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email},
        )

        # If user already exists, also set email if empty or different
        if not created and email and getattr(user, "email", None) != email:
            user.email = email

        # Ensure user is staff and superuser
        changed_flags = False
        if not user.is_staff:
            user.is_staff = True
            changed_flags = True
        if not user.is_superuser:
            user.is_superuser = True
            changed_flags = True
        if hasattr(user, "is_active") and not user.is_active:
            user.is_active = True
            changed_flags = True

        if created or update_password:
            user.set_password(password)
            user.save()
            if created:
                self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" created.'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" updated (password/flags).'))
        else:
            if changed_flags:
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" flags updated (staff/superuser).'))
            else:
                self.stdout.write(self.style.WARNING(f'Superuser "{username}" already exists. Nothing to do.'))
