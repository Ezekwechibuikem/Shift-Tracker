from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    path('home/', views.home, name='home'),
    path('staff-list/', views.staff_list, name='staff_list'),
    path('profile/', views.profile, name='profile'),
    path('intro/', views.intro, name='intro'),
    path('admin-contact/', views.admin_contact, name='admin_contact'),
    
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/verify-otp/', views.verify_otp, name='verify_otp'),
    path('password-reset/set-new-password/', views.set_new_password, name='set_new_password'),
    
]