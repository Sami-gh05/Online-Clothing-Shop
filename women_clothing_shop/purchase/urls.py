"""
URL configuration for the purchase application.

Includes cart and checkout routes.
"""

from django.urls import path

from . import views

# urlpatterns is a list of all valid URL patterns for this app.
urlpatterns = [
    # --- Cart & Checkout URLs ---
    path('cart/', views.cart_detail, name='cart-detail'),
    path('cart/add/<int:variant_id>/', views.add_to_cart, name='cart-add'),
    path('cart/update/<int:variant_id>/', views.update_cart, name='cart-update'),
    path('cart/remove/<int:variant_id>/', views.remove_from_cart, name='cart-remove'),
    path('checkout/', views.checkout, name='checkout'),
]
