"""
Purchase application data models.

Defines order and cart-related models: Order (customer orders with status
tracking and timestamps), OrderItem (individual items within an order with
pricing and quantity), and Cart (session-based shopping cart management).
Handles order lifecycle from creation through fulfillment.
"""

from django.db import models
from django.conf import settings
from decimal import Decimal

from shop.models import ClotheVariant

class Order(models.Model):
    """
    Represents a customer's order.
    This acts as a container for the OrderItems and stores
    customer info, shipping details, and status.
    """
    STATUS_CHOICES = (
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('cancelled', 'Cancelled'),
    )

    # Use settings.AUTH_USER_MODEL for foreign keys to your User model.
    # This is Django's recommended best practice.
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders',
                             verbose_name="User")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing', verbose_name="Order Status")

    shipping_address = models.TextField(verbose_name="Shipping Address", blank=True)

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"

    @property
    def total_price(self):
        """
        Calculates the total price of the order.
        It sums the 'total_price' of all related OrderItems.
        'self.items.all()' works because of 'related_name="items"'
        in the OrderItem model.
        """
        return sum((item.total_price for item in self.items.all()), Decimal('0'))


class OrderItem(models.Model):
    """
    Represents a single "line item" within an Order.
    This links a specific Clothe to an Order, storing the
    quantity and price *at the time of purchase*.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Order")

    # on_delete=models.SET_NULL is important!
    # If a clothe variant is deleted, we don't want to delete the OrderItem.
    # This preserves the order history. The clothe_variant field will just become NULL.
    clothe_variant = models.ForeignKey(
        ClotheVariant,
        on_delete=models.SET_NULL,
        null=True,
        related_name='order_items',
        verbose_name="Product"
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantity")

    # CRITICAL: Store the price at purchase time.
    # This prevents the order total from changing if the
    # Clothe.price is updated later.
    price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Price (at purchase time)")

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def __str__(self):
        # Check if clothe still exists
        clothe_name = self.clothe_variant.clothe.title if self.clothe_variant else "Deleted Product"
        return f"{self.quantity} x {clothe_name}"

    @property
    def total_price(self):
        """Calculates the total for this specific line item."""
        return self.quantity * self.price
