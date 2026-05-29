"""
Shop application views.

Provides public-facing product views (listing, detail, search, filtering)
and admin/staff product management views (create, edit, delete products
and variants, manage categories and colors, quick-add API endpoints).
Handles both customer browsing and inventory management.
"""

from django import forms
from django.contrib import messages
from django.urls import reverse

from django.forms import inlineformset_factory
from django.db import transaction
from django.db.models import Q, F, Value, ExpressionWrapper, DecimalField
from django.core.paginator import Paginator
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404

# Internal imports
from .models import Clothe, ClotheVariant, ClotheImage, Category
from .forms import ClotheForm, ClotheVariantForm, CategoryForm, ColorForm


# An inline formset factory is used to manage related objects (ClotheImage and ClotheVariant)
# on the same page as the parent object (Clothe).
ClotheImageFormSet = inlineformset_factory(
    Clothe,  # Parent model
    ClotheImage,  # Child model
    fields=('image',),  # Fields from ClotheImage to include in the form
    extra=1,  # Number of empty forms to display for adding new images
    can_delete=True  # Allows users to mark existing images for deletion
)

ClotheVariantFormSet = inlineformset_factory(
    Clothe,
    ClotheVariant,
    form=ClotheVariantForm,
    fields=("color", "size", "stock"),
    extra=1,
    can_delete=True,
)


def clothes_list(request):
    clothes = Clothe.objects.all().select_related("category")

    search_query = request.GET.get('q')
    if search_query:
        clothes = clothes.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    sort_by = request.GET.get('sort', 'newest')

    # Calculate final price in the database so sorting by final price works correctly.
    clothes = clothes.annotate(
        final_price_order=ExpressionWrapper(
            F('price') - (F('price') * F('discount_percentage') / Value(100)),
            output_field=DecimalField(max_digits=12, decimal_places=0)
        )
    )

    if sort_by == 'price_asc':
        clothes = clothes.order_by('final_price_order')
    elif sort_by == 'price_desc':
        clothes = clothes.order_by('-final_price_order')
    elif sort_by == 'name_asc':
        clothes = clothes.order_by('title')
    elif sort_by == 'name_desc':
        clothes = clothes.order_by('-title')
    else:
        clothes = clothes.order_by('-created_at')

    categories = Category.objects.all()
    
    category_id = request.GET.get("category", "").strip()
    if category_id:
        clothes = clothes.filter(category_id=category_id)

    paginator = Paginator(clothes, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    query_params = query_params.urlencode()

    return render(request, 'shop/clothes_list.html', {
        'clothes': page_obj,
        'page_obj': page_obj,
        'query_params': query_params,
        'categories': categories,
        'search_query': search_query,
        'current_sort': sort_by,
    })


def clothe_detail(request, clothe_id):
    clothe = get_object_or_404(
        Clothe.objects.prefetch_related("variants__color", "images"),
        id=clothe_id
    )
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("clothe-edit", clothe_id=clothe.id)
    return render(request, 'shop/clothe_detail.html', {"clothe": clothe})


@staff_member_required
def quick_add_category(request):
    form = CategoryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        next_url = request.GET.get("next") or reverse("clothes-list")
        return redirect(next_url)
    return render(request, "shop/quick_add_simple.html", {"form": form, "title": "افزودن دسته‌بندی"})

@staff_member_required
def quick_add_color(request):
    form = ColorForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        next_url = request.GET.get("next") or reverse("clothes-list")
        return redirect(next_url)
    return render(request, "shop/quick_add_simple.html", {"form": form, "title": "افزودن رنگ"})

@staff_member_required
def clothe_add(request):
    """
    Handles adding a new clothe (Admin/Staff only).
    GET: Displays the ClotheForm and an empty ClotheImageFormSet and an empty ClotheVariantFormSet.
    POST: Validates and saves both the form and the formset.
    """
    # Staff check
    if not request.user.is_staff:
        messages.error(request, "شما اجازه دسترسی به این صفحه را ندارید.")
        return redirect('home')

    if request.method == 'POST':
        form = ClotheForm(request.POST, request.FILES)
        # Initialize the formset with the POST data
        variant_formset = ClotheVariantFormSet(request.POST)
        image_formset = ClotheImageFormSet(request.POST, request.FILES)

        if form.is_valid() and variant_formset.is_valid() and image_formset.is_valid():
            try:
                with transaction.atomic():
                    clothe = form.save()

                    variant_formset.instance = clothe
                    variant_formset.save()

                    image_formset.instance = clothe
                    image_formset.save()

                messages.success(request, "محصول، انواع و گالری با موفقیت اضافه شد!")
                return redirect('clothes-list')
            except forms.ValidationError as e:
                messages.error(request, f"{e.message}")
    else:
        form = ClotheForm()
        # Create an empty formset for a new (unsaved) clothe
        variant_formset = ClotheVariantFormSet()
        image_formset = ClotheImageFormSet()

    context = {
        "form": form,
        "variant_formset": variant_formset,
        "image_formset": image_formset,
        "page_title": "افزودن محصول جدید",
    }
    return render(request, 'shop/clothe_add.html', context)


@staff_member_required
def clothe_edit(request, clothe_id):
    """
    Handles editing an existing clothe (Admin/Staff only).
    GET: Displays ClotheForm, ClotheImageFormSet and ClotheVariantFormSet pre-filled.
    POST: Validates and saves changes to clothe and its gallery and its variants.
    """
    if not request.user.is_staff:
        messages.error(request, "شما اجازه دسترسی به این صفحه را ندارید.")
        return redirect('home')

    clothe = get_object_or_404(Clothe, id=clothe_id)

    if request.method == 'POST':
        form = ClotheForm(request.POST, request.FILES, instance=clothe)
        # Initialize formset with POST data and the existing clothe
        variant_formset = ClotheVariantFormSet(request.POST, instance=clothe)
        image_formset = ClotheImageFormSet(request.POST, request.FILES, instance=clothe)
        
        if form.is_valid() and variant_formset.is_valid() and image_formset.is_valid():
            try:
                form.save()
                variant_formset.save()
                image_formset.save()

                messages.success(request, "محصول، انواع و گالری با موفقیت به‌روز شد!")
                return redirect("clothes-list")
            except forms.ValidationError as e:
                messages.error(request, f"{e.message}")
    else:
        # GET request: Pre-fill form and formset with existing data
        form = ClotheForm(instance=clothe)
        variant_formset = ClotheVariantFormSet(instance=clothe)
        image_formset = ClotheImageFormSet(instance=clothe)

    context = {
        "form": form,
        "variant_formset": variant_formset,
        "image_formset": image_formset,
        "clothe": clothe,
        "page_title": "ویرایش محصول",
    }
    return render(request, 'shop/clothe_form.html', context)


@staff_member_required
def clothe_delete(request, clothe_id):
    """
    Handles clothe deletion (Admin/Staff only).
    This view is POST-only for safety (though it could
    be improved with a confirmation page).
    """
    if not request.user.is_staff:
        messages.error(request, "شما اجازه دسترسی به این صفحه را ندارید.")
        return redirect('home')

    clothe = get_object_or_404(Clothe, id=clothe_id)

    if request.method == 'POST':
        clothe_name = clothe.title
        clothe.delete()  # This deletes the clothe
        messages.success(request, f'محصول "{clothe_name}" با موفقیت حذف شد.')
        return redirect('clothes-list')

    # If GET, just redirect. A proper implementation
    # would show a confirmation page.
    return redirect('clothes-list')
