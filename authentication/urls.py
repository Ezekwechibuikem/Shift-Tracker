from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    path('home/', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/verify-otp/', views.verify_otp, name='verify_otp'),
    path('password-reset/set-new-password/', views.set_new_password, name='set_new_password'),
    
    # # Admin and management
    # path('admin-panel/', views.admin_panel_view, name='admin_panel'),
    # path('manage-users/', views.manage_users_view, name='manage_users'),
]