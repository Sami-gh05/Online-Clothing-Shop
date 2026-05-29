"""
Accounts application forms.

Provides custom user authentication forms: CustomUserCreationForm for new
user registration, CustomUserEditForm for profile editing, and AdminUserEditForm
for admin-level user modifications. These forms extend Django's built-in auth
forms and are customized for the CustomUser model.
"""

from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    """
    A custom form for creating new users.

    It inherits from the base UserCreationForm and simply
    updates the Meta class to use our CustomUser model.
    """

    class Meta(UserCreationForm.Meta):
        # Tell the form to use our custom user model
        model = CustomUser
        # Specify the fields to show on the registration form.
        # 'username' and 'passwords' are included by default.
        fields = ('username', 'email')


class CustomUserEditForm(UserChangeForm):
    """
    A form for users to edit their own profile information
    in their account dashboard.
    """
    # We must clear the password field.
    # Otherwise, UserChangeForm will show a non-editable
    # hash of the password, which is confusing and insecure.
    # Password changes should be handled by a separate form.
    password = None

    class Meta:
        model = CustomUser
        # Specify the exact fields the user is allowed to edit
        fields = ('username', 'email', 'phone_number')
  

class AdminUserEditForm(UserChangeForm):
    """
    A form for an admin to edit *any* user's profile.

    This is more powerful than CustomUserEditForm because
    it includes permission fields.
    """
    password = None  # Admins shouldn't edit passwords this way

    class Meta:
        model = CustomUser
        # Include all fields an admin should be able to control
        fields = [
            'username',
            'email',
            'phone_number',
            'is_active',  # Can the user log in?
            'is_staff',  # Can the user access the admin?
            'is_superuser'  # Do they have all permissions?
        ]
