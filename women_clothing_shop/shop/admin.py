"""
Admin configuration for the shop application.

Registers shop models and configures inline editing and model displays.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Category,
    Color,
    Clothe,
    ClotheVariant,
    ClotheImage,
)
from .forms import ClotheForm


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ("name", "color_swatch", "color_code")
    search_fields = ("name", "color_code")

    def color_swatch(self, obj):
        if not obj.color_code:
            return "-"
        return format_html(
            '<span style="display:inline-block;width:16px;height:16px;'
            'border:1px solid #999;border-radius:3px;background:{};"></span>',
            obj.color_code,
        )

    color_swatch.short_description = "Color"


class ClotheImageInline(admin.TabularInline):
    model = ClotheImage
    extra = 1


class ClotheVariantInline(admin.TabularInline):
    model = ClotheVariant
    extra = 1
    autocomplete_fields = ("color",)
    fields = ("color", "size", "stock")
    # UniqueConstraint in the model prevents duplicate variant combinations


@admin.register(Clothe)
class ClotheAdmin(admin.ModelAdmin):
    form = ClotheForm
    inlines = [ClotheVariantInline, ClotheImageInline]

    list_display = ("title", "category", "price", "discount_percentage", "final_price_display", "created_at")
    list_filter = ("category", "created_at")
    search_fields = ("title", "description", "category__name")
    ordering = ("-created_at",)

    readonly_fields = ("final_price_display", "image_preview")
    fields = (
        "title",
        "description",
        "category",
        "price",
        "discount_percentage",
        "image",
        "image_preview",
        "final_price_display",
    )

    def final_price_display(self, obj):
        # obj.final_price returns a Decimal value
        try:
            val = obj.final_price
        except Exception:
            return "-"
        return f"{val:,.0f} تومان"

    final_price_display.short_description = "Final Price"

    def image_preview(self, obj):
        if not getattr(obj, "image", None):
            return "-"
        try:
            url = obj.image.url
        except Exception:
            return "-"
        return format_html('<img src="{}" style="max-height:80px;border-radius:6px;" />', url)

    image_preview.short_description = "Main Image"


# Optional: manage variants standalone too (handy for quick stock edits)
@admin.register(ClotheVariant)
class ClotheVariantAdmin(admin.ModelAdmin):
    list_display = ("clothe", "color", "size", "stock")
    list_filter = ("size", "color")
    search_fields = ("clothe__title", "color__name")
    autocomplete_fields = ("clothe", "color")
    list_editable = ("stock",)
