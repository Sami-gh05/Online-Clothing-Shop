"""
URL configuration for the shop application.

Defines routes for product browsing and shop management.
"""

from django.urls import path

from . import views

# urlpatterns is a list of all valid URL patterns for this app.
urlpatterns = [
    # --- Product URLs ---
    path('products/', views.clothes_list, name='clothes-list'),
    path('product/<int:clothe_id>/', views.clothe_detail, name='clothe-detail'),
]
