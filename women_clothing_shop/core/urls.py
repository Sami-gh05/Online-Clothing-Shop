"""
URL configuration for the core application.

Defines home and about page routes.
"""

from django.urls import path

from . import views

# urlpatterns is a list of all valid URL patterns for this app.
urlpatterns = [
    # --- Main Page URLs ---
    path('', views.home, name='home'),
    path('about/', views.about_us, name='about-us'),
]
