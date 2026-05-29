"""
Manages the shopping cart using Django's session framework.

This module defines the `Cart` class, which provides a high-level
interface to store and manage clothes in the user's session.
It handles adding, updating, removing, and iterating over cart items.
"""

from decimal import Decimal
from django.conf import settings

from .models import ClotheVariant




class Cart:
    """
    A class to manage the shopping cart using Django sessions.

    The cart is stored in the session as a dictionary:
    {
        'variant_id_1': {'quantity': 2, 'price': '99.99'},
        'variant_id_2': {'quantity': 1, 'price': '45.00'}
    }

    The `variant_id` is stored as a string because JSON, which
    Django uses for session serialization, only supports string keys.
    """

    def __init__(self, request):
        """
        Initialize the cart.

        Gets the cart from the current session or creates a new,
        empty cart if one doesn't exist.
        """
        self.session = request.session
        # Try to get the cart from the session using the key
        # defined in settings (e.g., 'cart')
        cart = self.session.get(settings.CART_SESSION_ID)

        if not cart:
            # If no cart is found, create an empty dictionary
            # and save it in the session.
            cart = self.session[settings.CART_SESSION_ID] = {}

        self.cart = cart

    def add(self, variant, quantity=1, update_quantity=False):
        """
        Add a variant to the cart or update its quantity.

        Args:
            variant (ClothVariant): The variant instance to add.
            quantity (int): The quantity to add.
            update_quantity (bool): If True, the quantity is replaced.
                                    If False (default), it's added.
        """
        # Session keys must be strings (e.g., for JSON serialization)
        variant_id = str(variant.id)
        
        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            quantity = 1

        # If the variant isn't in the cart, initialize it
        if variant_id not in self.cart:
            self.cart[variant_id] = {'quantity': 0, 'price': str(variant.clothe.final_price)} #to be checked

        # Update or add to the quantity
        if update_quantity:
            self.cart[variant_id]['quantity'] = quantity
        else:
            self.cart[variant_id]['quantity'] += quantity

        # --- Stock Check ---
        # Ensure the cart quantity does not exceed available stock
        if self.cart[variant_id]['quantity'] > variant.stock:
            self.cart[variant_id]['quantity'] = variant.stock

        # Save the changes to the session
        self.save()

    def remove(self, variant):
        """
        Remove a variant from the cart.

        Args:
            variant (ClotheVariant): The variant instance to remove.
        """
        variant_id = str(variant.id)
        if variant_id in self.cart:
            # Remove the item from the cart dictionary
            del self.cart[variant_id]
            # Save the updated session
            self.save()

    def save(self):
        """
        Mark the session as "modified" to make sure it gets saved.

        This is crucial because we are modifying a mutable
        dictionary *within* the session. Django won't know the
        session data has changed unless we explicitly tell it.
        """
        self.session.modified = True

    def __iter__(self):
        """
        Iterate over the items in the cart (from the session) and
        get the related ClothVariant objects from the database.

        This allows looping over the cart in templates like:
        {% for item in cart %}
            {{ item.variant.clothe.title }}
            {{ item.quantity }}
            {{ item.total_price }}
        {% endfor %}

        Yields:
            dict: A cart item dictionary with 'variant', 'quantity',
                  'price', and 'total_price' keys.
        """
        # Get all variant IDs from the cart
        variant_ids = self.cart.keys()

        # Make one database query to get all ClotheVariant objects
        variants = (
            ClotheVariant.objects
            .filter(id__in=variant_ids)
            .select_related("clothe", "color")  # size is CharField so no select_related needed
        )
        # Create a copy of the session cart to work with
        cart = self.cart.copy()

        # Add the 'variant' object to each item in the copied cart
        for variant in variants:
            cart[str(variant.id)]['variant'] = variant

        # Now, iterate over the copied cart and prepare data
        for item in cart.values():
            if "variant" not in item:
                continue
            
            item["quantity"] = int(item["quantity"])
            # Convert price back to Decimal for calculations
            item['price'] = Decimal(item['price'])
            # Calculate the total price for this line item
            item['total_price'] = item['price'] * item['quantity']
            # 'yield' turns this method into a generator
            yield item

    def __len__(self):
        """
        Count all items in the cart.

        This returns the total number of *individual items*
        (e.g., 2 of item A, 3 of item B = 5), not the number
        of *variant lines* (which would be 2).
        """
        return sum(int(item['quantity']) for item in self.cart.values())

    def get_total_price(self):
        """
        Calculate the total price of all items in the cart.
        """
        return sum(Decimal(item['price']) * int(item['quantity']) for item in self.cart.values())

    def clear(self):
        """
        Remove the entire cart from the session.
        """
        # Delete the cart key from the session dictionary
        self.session.pop(settings.CART_SESSION_ID, None)
        self.save()
