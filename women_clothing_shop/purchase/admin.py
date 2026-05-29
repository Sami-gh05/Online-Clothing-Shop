"""
Purchase application Django admin configuration.

Registers Order and OrderItem models in the Django admin interface.
Configures inline editing of order items within order admin pages,
displays key order information (date, status, customer), and provides
read-only views of order details and associated items.
"""


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Order, OrderItem
from .forms import OrderStatusUpdateForm

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    autocomplete_fields = ("clothe_variant",)

    fields = ("clothe_variant", "price", "quantity", "get_total_price")
    readonly_fields = ("clothe_variant", "price", "quantity", "get_total_price")

    def get_total_price(self, obj):
        try:
            return f"{obj.total_price:,.0f} تومان"
        except Exception:
            return "-"

    get_total_price.short_description = "Item Total"

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    form = OrderStatusUpdateForm
    inlines = [OrderItemInline]

    list_display = ("id", "user", "status", "created_at", "total_price_display")
    list_filter = ("status", "created_at")
    search_fields = ("id", "user__username", "user__email")
    date_hierarchy = "created_at"

    readonly_fields = ("user", "shipping_address", "created_at", "total_price_display")
    fieldsets = (
        (None, {"fields": ("status",)}),
        ("Order Details", {"fields": ("id", "user", "shipping_address", "created_at", "total_price_display")}),
    )

    def total_price_display(self, obj):
        try:
            return f"{obj.total_price:,.0f} تومان"
        except Exception:
            return "-"

    total_price_display.short_description = "Total Price"

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ("id",)
        return self.readonly_fields
