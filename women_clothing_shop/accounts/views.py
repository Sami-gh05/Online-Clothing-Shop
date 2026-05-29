"""
Accounts application views.

Handles user authentication (registration, login, logout), personal account
management (profile editing, password changes, order history), and admin
dashboard views for user and order management.
"""

from django.contrib import messages
from django.db.models.functions import TruncDay
from django.db.models import Sum, F, Q
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import PasswordChangeForm, AuthenticationForm
from django.contrib.auth import update_session_auth_hash, login, authenticate, logout

# Internal imports
from .models import CustomUser
from shop.models import Clothe, ClotheVariant
from purchase.models import Order, OrderItem


from .forms import (
    CustomUserCreationForm, CustomUserEditForm,
    AdminUserEditForm
)
from purchase.forms import OrderStatusUpdateForm

from decimal import Decimal


def register(request):
    """
    Handles new user registration.
    GET: Displays the registration form.
    POST: Processes the registration form.
    On success, creates the user, logs them in, and redirects to 'home'.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Save the new user object
            login(request, user)  # Log the new user in
            messages.success(request, 'ثبت نام شما با موفقیت انجام شد!')
            return redirect('home')
    else:
        # GET request: Show a blank form
        form = CustomUserCreationForm()

    context = {'form': form}
    return render(request, 'accounts/register.html', context)


def login_user(request):
    """
    Handles user login.
    GET: Displays the login form.
    POST: Authenticates the user.
    On success, logs the user in and redirects. If a 'next'
    parameter exists (from @login_required), redirects there.
    """
    if request.method == 'POST':
        # AuthenticationForm is a built-in form
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            # Get cleaned data from the form
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            # Authenticate the user
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)  # Log the user into the session

                # Handle 'next' parameter for redirects (e.g., from checkout)
                next_page = request.POST.get('next') or request.GET.get('next')
                if next_page:
                    return redirect(next_page)
                if user.is_staff:
                    return redirect('admin-dashboard')
                return redirect('home')
            else:
                messages.error(request, 'نام کاربری یا رمز عبور اشتباه است.')
    else:
        form = AuthenticationForm()

    context = {'form': form}
    return render(request, 'accounts/login.html', context)


def admin_login(request):
    """
    Separate admin login panel.
    Only users with is_staff=True may sign in here.
    """
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_staff:
                    login(request, user)
                    next_page = request.POST.get('next') or request.GET.get('next')
                    return redirect(next_page or 'admin-dashboard')
                messages.error(request, 'این حساب دسترسی مدیریت ندارد.')
            else:
                messages.error(request, 'نام کاربری یا رمز عبور اشتباه است.')
    else:
        form = AuthenticationForm()

    context = {
        'form': form,
        'next': request.GET.get('next', ''),
    }
    return render(request, 'accounts/admin_login.html', context)


# Logout Logic
def logout_user(request):
    """
    Logs the current user out and redirects to the homepage.
    """
    logout(request)
    messages.info(request, 'شما با موفقیت خارج شدید.')
    return redirect('home')


@login_required  # Redirects to 'login' if user is not authenticated
def user_dashboard(request):
    """
    Renders the main user dashboard/account page.
    This view is protected and requires login.
    """
    context = {
        'page_title': 'داشبورد من'
    }
    return render(request, 'accounts/account_dashboard.html', context)


@login_required
def admin_dashboard(request):
    """
    Admin landing page for staff users.
    """
    if not request.user.is_staff:
        messages.error(request, "شما اجازه دسترسی به این صفحه را ندارید.")
        return redirect('home')

    context = {
        'page_title': 'پنل مدیریت',
        'product_count': ClotheVariant.objects.count(),
        'order_count': Order.objects.count(),
        'pending_order_count': Order.objects.filter(status='processing').count(),
        'user_count': CustomUser.objects.count(),
    }
    return render(request, 'accounts/admin_dashboard.html', context)


@login_required
def edit_account(request):
    """
    Handles user profile editing (username, email, phone, etc.).
    GET: Displays the CustomUserEditForm pre-filled with user's data.
    POST: Validates and saves changes to the user's profile.
    """
    if request.method == 'POST':
        # Pass 'instance=request.user' to update the current user
        form = CustomUserEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'پروفایل شما با موفقیت به‌روز شد!')
            return redirect('user-dashboard')
    else:
        # GET request: Show form pre-filled with current user's data
        form = CustomUserEditForm(instance=request.user)

    context = {
        'page_title': 'ویرایش حساب کاربری',
        'form': form
    }
    return render(request, 'accounts/edit_account.html', context)


@login_required
def change_password(request):
    """
    Handles user password changes.
    GET: Displays the PasswordChangeForm.
    POST: Validates the old password and sets the new password.

    On success, 'update_session_auth_hash' is called to
    prevent the user from being logged out.
    """
    if request.method == 'POST':
        # This form requires the 'request.user' object
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # CRITICAL: Update the session auth hash
            # Otherwise, the user will be logged out after changing password
            update_session_auth_hash(request, user)
            messages.success(request, 'رمز عبور شما با موفقیت تغییر کرد!')
            return redirect('user-dashboard')
        else:
            messages.error(request, 'لطفا خطاهای زیر را اصلاح کنید.')
    else:
        form = PasswordChangeForm(request.user)

    context = {
        'page_title': 'تغییر رمز عبور',
        'form': form
    }
    return render(request, 'accounts/change_password.html', context)


@login_required
def my_orders(request):
    """
    Renders the "My Orders" page for a logged-in user.
    Displays a list of all orders placed by this user.
    """
    # Filter orders to only those belonging to the current user
    orders = Order.objects.filter(user=request.user)
    context = {
        'orders': orders,
        'page_title': 'سفارش‌های من'
    }
    return render(request, 'accounts/my_orders.html', context)


@login_required
def admin_all_orders(request):
    """
    Renders the admin page for viewing all customer orders.
    GET: Displays a list of all orders, each with a status update form.
    POST: Handles the submission of an OrderStatusUpdateForm
          for a specific order.
    """
    if not request.user.is_staff:
        messages.error(request, "شما اجازه دسترسی به این صفحه را ندارید.")
        return redirect('home')

    # Handle status update (POST)
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        order = get_object_or_404(Order, id=order_id)
        # Pass 'instance=order' to update the correct order
        form = OrderStatusUpdateForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, f'وضعیت سفارش {order.id} به‌روز شد.')
            return redirect('admin-all-orders')

    # GET request: Display all orders
    all_orders = Order.objects.all().order_by('-created_at')

    # To show a form for *each* order, we create a list of
    # (order, form_instance) tuples to loop over in the template.
    orders_with_forms = []
    for order in all_orders:
        form = OrderStatusUpdateForm(instance=order)
        orders_with_forms.append((order, form))

    context = {
        'page_title': 'مدیریت تمام سفارش‌ها',
        'orders_with_forms': orders_with_forms,
    }
    return render(request, 'accounts/admin_all_orders.html', context)


@login_required
def admin_user_list(request):
    """
    Renders the admin page for listing all users (Admin/Staff only).
    Handles search via a GET 'q' parameter.
    """
    if not request.user.is_staff:
        messages.error(request, "شما اجازه دسترسی به این صفحه را ندارید.")
        return redirect('home')

    search_query = request.GET.get('q')
    if search_query:
        users = CustomUser.objects.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query)
        ).order_by('username')
    else:
        users = CustomUser.objects.all().order_by('username')

    context = {
        'page_title': 'مدیریت تمام کاربران',
        'users': users,
        'search_query': search_query,
    }
    return render(request, 'accounts/admin_user_list.html', context)


@login_required
def admin_user_edit(request, user_id):
    """
    Handles editing a specific user's details (Admin/Staff only).
    This uses the AdminUserEditForm which includes permission fields.
    GET: Displays the form pre-filled with the user's data.
    POST: Validates and saves changes.
    """
    if not request.user.is_staff:
        messages.error(request, "شما اجازه دسترسی به این صفحه را ندارید.")
        return redirect('home')

    # Get the user to be edited
    user_to_edit = get_object_or_404(CustomUser, id=user_id)

    if request.method == 'POST':
        form = AdminUserEditForm(request.POST, request.FILES, instance=user_to_edit)
        if form.is_valid():
            form.save()
            messages.success(request, f'کاربر "{user_to_edit.username}" با موفقیت به‌روز شد.')
            return redirect('admin-user-list')
    else:
        # GET request: Pre-fill form
        form = AdminUserEditForm(instance=user_to_edit)

    context = {
        'page_title': f'ویرایش کاربر: {user_to_edit.username}',
        'form': form,
        'user_to_edit': user_to_edit,
    }
    return render(request, 'accounts/admin_user_edit.html', context)


@login_required
def admin_sales_report(request):
    """
    Displays various sales statistics (Admin/Staff only).

    Calculates:
    1. Total revenue from 'shipped' orders.
    2. Total count of 'shipped' orders.
    3. Top 5 best-selling clothes.
    4. Daily sales totals for the last 10 days.
    """
    if not request.user.is_staff:
        messages.error(request, "شما اجازه دسترسی به این صفحه را ندارید.")
        return redirect('home')

    # Base query for 'completed' sales
    completed_orders = Order.objects.filter(status='shipped')

    # 1. Total Revenue
    # Sum the (price * quantity) of all OrderItems
    # that belong to 'shipped' orders.
    total_revenue = OrderItem.objects.filter(order__in=completed_orders).aggregate(
        total=Sum(F('price') * F('quantity'))  # F() refers to model fields
    )['total'] or Decimal('0')  # Use 'or 0' to handle None if no sales

    # 2. Total Sales Count
    total_sales_count = completed_orders.count()

    # 3. Top 5 Best-Selling clothes
    top_selling_products = Clothe.objects.annotate(
        # Sum the quantity of order_items, but *only*
        # for items in 'shipped' orders.
        total_sold=Sum('variants__order_items__quantity',
                       filter=Q(variants__order_items__order__status='shipped'))
    ).filter(total_sold__gt=0).order_by('-total_sold')[:5]

    # 4. Daily Sales (last 10 days)
    daily_sales = OrderItem.objects.filter(order__status='shipped') \
        .annotate(day=TruncDay('order__created_at')) \
        .values('day') \
        .annotate(daily_total=Sum(F('price') * F('quantity'))) \
        .order_by('-day')[:10]

    context = {
        'page_title': 'گزارش‌های فروش',
        'total_revenue': total_revenue,
        'total_sales_count': total_sales_count,
        'top_selling_products': top_selling_products,
        'daily_sales': daily_sales,
    }
    return render(request, 'accounts/admin_sales_report.html', context)
