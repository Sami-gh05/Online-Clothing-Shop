"""
Core application views.

Provides main website pages: home page displays featured products,
about page provides company information.
"""
from django.shortcuts import render

from shop.models import Clothe

def home(request):
    """
    Renders the homepage.
    Fetches the 4 most recently created Clothes to display.
    """
    # Query for the 4 newest Clothes
    newest_clothes = Clothe.objects.order_by('-created_at')[:4]
    highest_discounts = Clothe.objects.order_by("-discount_percentage")[:4]
    context = {
        'newest_clothes': newest_clothes, 'highest_discounts': highest_discounts
    }
    return render(request, 'core/home.html', context)


def about_us(request):
    """
    Renders the static 'About Us' page.
    """
    # This view simply renders a static template.
    return render(request, 'core/about_us.html')