"""
Accounts application URL routing.

Defines URL patterns for user authentication (register, login, logout),
personal account management (dashboard, edit profile, change password),
order history, and admin/staff management interfaces (user list, product
management, order management, sales reports).
"""

from django.urls import path

from . import views
from shop.views import clothe_add, clothe_delete, clothe_edit, quick_add_category, quick_add_color

# urlpatterns is a list of all valid URL patterns for this app.
urlpatterns = [
    # --- Authentication URLs ---
    path('register/', views.register, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('manage/login/', views.admin_login, name='admin-login'),
    path('manage/', views.admin_dashboard, name='admin-dashboard'),

    # --- User Account URLs ---
    path('account/', views.user_dashboard, name='user-dashboard'),
    path('account/edit/', views.edit_account, name='edit-account'),
    path('account/password/', views.change_password, name='change-password'),
    path('account/orders/', views.my_orders, name='my-orders'),

    # --- Admin/Management URLs ---

    # Product Management
    path('manage/product/add/', clothe_add, name='clothe-add'),
    path('manage/product/edit/<int:clothe_id>/', clothe_edit, name='clothe-edit'),
    path('manage/product/delete/<int:clothe_id>/', clothe_delete, name='clothe-delete'),
    path("manage/quick-add/category/", quick_add_category, name="quick-add-category"),
    path("manage/quick-add/color/", quick_add_color, name="quick-add-color"),
    
    # Order Management
    path('manage/orders/', views.admin_all_orders, name='admin-all-orders'),

    # User Management
    path('manage/users/', views.admin_user_list, name='admin-user-list'),
    path('manage/users/edit/<int:user_id>/', views.admin_user_edit, name='admin-user-edit'),

    # Reporting
    path('manage/reports/', views.admin_sales_report, name='admin-sales-report'),
]
