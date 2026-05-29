"""
Shop application forms.

Provides product management forms: ClotheForm for creating/editing main
product details (title, description, pricing, category), ClotheVariantForm
for managing product variants (size, color, stock), CategoryForm for
product categories, and ColorForm for color definitions. Used by admin
interfaces for product administration.
"""
import re
from django import forms
from .models import Clothe, ClotheVariant, Category, Color

class ClotheForm(forms.ModelForm):
    """
    A comprehensive form for Admins to create and edit Clothes.
    """

    class Meta:
        model = Clothe
        # Include all fields from the Clothe model
        # except ones that are auto-set (like created_at)
        fields = ['title', 'description', 'price', 'discount_percentage', 'category', 'image']

        # Customize the widgets for a better admin UI
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'image': forms.FileInput(),
        }


class ClotheVariantForm(forms.ModelForm):
    """
    Create / edit variant (color+size+stock) for a given Clothe.
    Usually you set clothe in the view (or use inline formset in admin/panel).
    """

    class Meta:
        model = ClotheVariant
        fields = ["color", "size", "stock"]

    def clean_stock(self):
        stock = self.cleaned_data.get("stock")
        if stock is None:
            return 0
        if stock < 0:
            raise forms.ValidationError("موجودی نمی‌تواند منفی باشد.")
        return stock


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]
        
        widgets = {
            "name": forms.TextInput(attrs={"class": "input", "placeholder": "نام دسته‌بندی"}),
        }
        


HEX6_RE = re.compile(r"^#[0-9a-fA-F]{6}$")

class ColorForm(forms.ModelForm):
    class Meta:
        model = Color
        fields = ["name", "color_code"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "input",
                "placeholder": "نام رنگ (مثلاً قرمز)",
            }),
            "color_code": forms.TextInput(attrs={
                "type": "color",   # color picker
                "class": "input",
                "style": "width: 72px; height: 42px; padding: 0;",
            }),
        }

