"""
Forms used in the purchase workflow.

Includes checkout form and order status update form.
"""

from django import forms
from .models import Order


class OrderCreateForm(forms.ModelForm):
    """
    A form to collect shipping information during checkout.
    This form will be used to create a new Order object.
    """

    # We can explicitly define fields here to override their
    # default widget or add validation.
    shipping_address = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'آدرس پستی خود را وارد کنید...'}),
        required=True,
        label="آدرس ارسال"
    )

    class Meta:
        model = Order
        # We only ask for fields that the user needs to fill out.
        # The 'user' will be set from request.user in the view.
        fields = ['shipping_address']


class OrderStatusUpdateForm(forms.ModelForm):
    """
    A simple form for an admin to update an order's status.
    """

    class Meta:
        model = Order
        fields = ['status']  # Only allow changing the 'status' field
