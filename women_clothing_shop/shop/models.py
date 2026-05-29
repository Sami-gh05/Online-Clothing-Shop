"""
Shop application data models.

Defines product and inventory models: Category (product classifications),
Size and Color enumerations for product variants, Clothe (main product
entity with pricing and descriptions), ClotheVariant (specific product
combinations with size/color/stock), ClotheImage (gallery images), and
Admin-specific fields for inventory management.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal, ROUND_HALF_UP

class Category(models.Model):
    """
    Each clothe will be in a category (e.g T-shirt or hoodie)
    """
    name = models.CharField(max_length=100, verbose_name="Clothing Category")
    slug = models.SlugField(unique=True, null=True, blank=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name
    
    
class Size(models.TextChoices): #enum
    S = "S", "Small"
    M = "M", "Medium"
    L = "L", "large"
    XL = "XL", "Extra large"
    XXL = "XXL", "Doubly extra large"
    
    
class Color(models.Model):
    """
    Each clothe may have different colors
    """
    name = models.CharField(max_length=50, verbose_name="Color Name")
    color_code = models.CharField(max_length=7, help_text="Hexadecimal color code, e.g. #FF0000", verbose_name="Color Code")
    
    class Meta:
        verbose_name = "Color"
        verbose_name_plural = "Colors"

    def __str__(self):
        return self.name
    
    
class Clothe(models.Model):
    """
    The main model for a clothe in the shop.
    """
    title = models.CharField(max_length=255, verbose_name="Product Title")
    description = models.TextField(verbose_name="Description")
    price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Price")
    discount_percentage = models.SmallIntegerField(default=0
                                    , validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="Discount Percentage")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="clothes", verbose_name="Category")
    image = models.ImageField(upload_to='clothe_images/', null=True, blank=True, verbose_name="Product Image")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)  # Set on creation
    updated_at = models.DateTimeField(auto_now=True)  # Set on every save

    # When the user completes the purchase, this method subtracts the discount from the base price (if there is a discount)
    @property
    def final_price(self):
        if self.discount_percentage >  0:
            final = self.price - ((self.price * Decimal(self.discount_percentage)) / Decimal('100'))
            return final.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        else:
            return self.price
    
    @property
    def image_url(self):
        """
        A safe way to get the clothe's image URL.
        Returns a default placeholder if no image is set.
        """
        if self.image:
            return self.image.url
        # Return path to a default image in your static files
        return '/static/img/default.png'

    class Meta:
        verbose_name = "Clothing Item"
        verbose_name_plural = "Clothing Items"
        # Default ordering for clothe queries (newest first)
        ordering = ['-created_at']

    def __str__(self):
        return self.title
    

class ClotheVariant(models.Model):
    """
    We consider the combination of a clothe, its size and its color as a distinct
    entity in order to have stock for each of these combinations
    - we consider a same price between different combinations of one clothe
    """
    # one to many relationship because of each combination has only one clothe and color but each clothe or color can be related to many variants
    clothe = models.ForeignKey(Clothe, on_delete=models.CASCADE, related_name="variants")
    color = models.ForeignKey(Color, on_delete=models.CASCADE, verbose_name="Color")
    size = models.CharField(max_length=3, choices=Size.choices, verbose_name="Size")
    stock = models.PositiveIntegerField(default=0, verbose_name="Stock")
    
    class Meta:
        constraints = [models.UniqueConstraint(fields=['clothe', 'color', 'size'], name='unique_variant')]

    def __str__(self):
        return f"{self.clothe.title} - {self.color.name} - Size {self.get_size_display()}"
    

class ClotheImage(models.Model):
    """
    An individual gallery image linked to a clothe.
    This creates a one-to-many relationship:
    One Clothe can have Many clotheImages.
    """
    # 'on_delete=models.CASCADE' means if a clothe is deleted,
    # all its associated images are deleted too.
    clothe = models.ForeignKey(Clothe, on_delete=models.CASCADE, related_name='images',
                                verbose_name="Clothing Item")
    image = models.ImageField(upload_to='clothe_images/gallery/', verbose_name="Gallery Image")

    class Meta:
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"

    def __str__(self):
        return f"Image for {self.clothe.title}"

