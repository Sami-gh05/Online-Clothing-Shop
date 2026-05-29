"""
Purchase application views.

Handles shopping cart operations (view, add items, update quantities,
remove items, clear cart), checkout process, order creation, and order
history display. Integrates session-based cart management with order
database persistence.
"""

from django import forms
from django.contrib import messages
from django.db import transaction
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

# Internal imports
from purchase.cart import Cart
from shop.models import ClotheVariant
from .models import OrderItem
from .forms import OrderCreateForm


def cart_detail(request):
    """
    Renders the main shopping cart page.
    The cart object is fetched from the session via the Cart class.
    """
    cart = Cart(request)
    context = {
        'cart': cart
    }
    return render(request, 'purchase/cart_detail.html', context)


# View to add items to the cart
@require_POST  # Decorator ensures this view only accepts POST requests
def add_to_cart(request, variant_id):
    """
    Handles adding a variant to the cart (or updating its quantity).
    This view is POST-only.

    It validates the requested quantity against the variant's stock
    and the quantity already in the cart.
    """
    if request.user.is_staff or request.user.is_superuser:
        messages.warning(request, "ادمین اجازه خرید ندارد.")
        return redirect(request.META.get('HTTP_REFERER', '/'))
        
        
    cart = Cart(request)
    variant = get_object_or_404(
        ClotheVariant.objects.select_related("clothe", "color"),
        id=variant_id
    )
    
    # Get and validate the quantity from the form
    try:
        quantity = int(request.POST.get('quantity', 1))
        if quantity <= 0:
            quantity = 1
    except ValueError:
        quantity = 1

    # --- Stock Validation ---
    variant_id_str = str(variant.id)
    # Check how many of this item are *already* in the cart
    current_in_cart = int(cart.cart.get(variant_id_str, {}).get('quantity', 0))
    # Calculate the total quantity if we add the new amount
    potential_quantity = current_in_cart + quantity

    if potential_quantity > variant.stock:
        # The user is trying to add more than is available
        remaining_stock = variant.stock - current_in_cart
        if variant.stock == 0:
            messages.error(request, f'متاسفانه "{variant.clothe.title}" ( {variant.color.name} / {variant.size} ) تمام شده است.')
        elif current_in_cart == variant.stock:
            messages.warning(request,
                             f'شما قبلاً به حداکثر موجودی ({variant.stock} عدد) از این لباس در سبد خرید خود رسیده‌اید.')
        else:
            messages.error(request,
                           f'امکان اضافه کردن این تعداد وجود ندارد. شما فقط می‌توانید {remaining_stock} عدد دیگر از این محصول اضافه کنید.')
    else:
        # Stock is sufficient, add to cart
        cart.add(variant=variant, quantity=quantity)
        messages.success(request, f'"{variant.clothe.title}" ( {variant.color.name} / {variant.size} ) به سبد خرید شما اضافه شد.')

    # Redirect back to the page the user came from (e.g., clothes detail)
    return redirect(request.META.get('HTTP_REFERER', 'clothe-detail'))

# View to remove items from the cart
def remove_from_cart(request, variant_id):
    """
    Removes a variant line item entirely from the cart.
    Redirects back to the cart detail page.
    """
    cart = Cart(request)
    variant = get_object_or_404(ClotheVariant, id=variant_id)
    cart.remove(variant)
    messages.success(request, "آیتم مربوطه از سبد خرید حذف شد")
    return redirect('cart-detail')

@require_POST
def update_cart(request, variant_id):
    """
    Updates the quantity of a specific item in the cart.
    Used by the form in the cart detail page.
    """
    cart = Cart(request)
    variant = get_object_or_404(
        ClotheVariant.objects.select_related("clothe", "color"),
        id=variant_id
    )

    try:
        quantity = int(request.POST.get('quantity', 1))
    except ValueError:
        quantity = 1

    # 1. Validate minimum quantity
    if quantity < 1:
        quantity = 1

    # 2. Validate maximum stock
    if quantity > variant.stock:
        messages.warning(
            request,
            f'موجودی ناکافی است. حداکثر تعداد قابل سفارش برای "{variant.clothe.title}" '
            f'({variant.color.name} / {variant.size}) {variant.stock} عدد است.'
        )
        # Set quantity to the max available stock
        quantity = variant.stock
    else:
        messages.success(request, 'تعداد محصول در سبد خرید به‌روز شد.')

    # 3. Update the cart (Notice update_quantity=True)
    cart.add(variant=variant, quantity=quantity, update_quantity=True)

    return redirect('cart-detail')

@login_required
def checkout(request):
    """
    Handles the checkout process and order creation.
    GET: Displays the shipping form (OrderCreateForm) and cart summary.
    POST: Validates the form, creates an Order, creates OrderItems
          from the cart, clears the cart, and redirects.
    """
    cart = Cart(request)

    # Don't allow checkout if cart is empty
    if len(cart) == 0:
        messages.error(request, "سبد خرید شما خالی است. امکان رفتن به صفحه پرداخت وجود ندارد.")
        return redirect('cart-detail')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Create Order, but don't save yet
                    order = form.save(commit=False)
                    order.user = request.user  # Assign the logged-in user
                    order.save()  # Save to DB to get an 'order.id'
                    
                    # 2. lock all variants involved (prevents overselling)
                    cart_items = list(cart)
                    variant_ids = [i["variant"].id for i in cart_items]
                    locked_variants = {
                        v.id: v
                        for v in ClotheVariant.objects.select_for_update()
                        .select_related("clothe")
                        .filter(id__in=variant_ids)
                    }
                
                    # 3. Create OrderItem objects for each item in the cart
                    for item in cart_items:
                        variant = locked_variants.get(item["variant"].id)
                        qty = int(item["quantity"])
                        
                        if variant is None:
                            raise forms.ValidationError("یکی از محصولات انتخابی دیگر موجود نیست.")

                        if qty > variant.stock:
                            raise forms.ValidationError(
                                f'موجودی کافی نیست برای "{variant.clothe.title}" '
                                f'({variant.color.name} / {variant.size}). موجودی: {variant.stock}'
                            )
                        
                        # Fianl price by considering discount
                        price = variant.clothe.final_price
                        
                        OrderItem.objects.create(
                            order=order,
                            clothe_variant=variant,
                            price=price,  # Store the final price at time of purchase (not necessarily price of the cart)
                            quantity=qty
                        )
                        
                        variant.stock -= qty
                        variant.save(update_fields=["stock"])
                    
                    # 4. clear the session cart
                    cart.clear()

                    messages.success(request, 'سفارش شما با موفقیت ثبت شد!')
                    return redirect('my-orders')  # Redirect to user's order history
            except forms.ValidationError as e:
                messages.error(request, e.message)
            except Exception as e:
                messages.error(request, f"خطا در ثبت سفارش: {e}")
                
    else:
        # GET request: Show a blank form
        form = OrderCreateForm()

    context = {
        'cart': cart,
        'form': form
    }
    return render(request, 'purchase/checkout.html', context)
