"""
Custom context processors for the application.

Context processors are functions that add variables to the context
of every template rendered. This is useful for data that is needed
on every page, such as a shopping cart or navigation links.

To enable these, you must add the path to these functions
(e.g., 'core.context_processors.cart') to the 'CONTEXT_PROCESSORS'
list in your Django settings.py.
"""

from purchase.cart import Cart
from shop.models import Category


def cart(request):
    """
    Makes the session cart object available in all templates.

    This allows any template to access `{{ cart }}` to display
    cart details, such as the item count.

    Args:
        request: The current HttpRequest object.

    Returns:
        dict: A dictionary containing the 'cart' instance.
    """
    # Instantiate the Cart class with the current request's session
    return {'cart': Cart(request)}


def categories_nav(request):
    """
    Makes categories available in all templates for navigation.
    """
    categories = Category.objects.all().order_by("name")
    return {"nav_categories": categories}
