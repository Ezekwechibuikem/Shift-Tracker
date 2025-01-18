from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    # Authentication URLs
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    
    # Password Reset Flow
    path('password/reset/', views.password_reset_request, name='password_reset_request'),
    path('password/verify-otp/', views.verify_otp, name='verify_otp'),
    path('password/set-new/', views.set_new_password, name='set_new_password'),
    
    # Dashboard & Profile
    path('', views.home, name='home'),
    path('profile/', views.update_profile, name='profile'),
    
    # User Management
    path('users/', views.user_list, name='user_list'),
    path('users/<int:user_id>/update/', views.user_update, name='user_update'),
    
    # Team Management
    path('teams/', views.team_list, name='team_list'),
    path('teams/create/', views.team_create, name='team_create'),
    path('teams/<int:team_id>/', views.team_details, name='team_details'),
    path('teams/<int:team_id>/update/', views.team_update, name='team_update'),
    
    # Team Member Management
    path('teams/<int:team_id>/members/', views.team_member_list, name='team_members'),
    path('teams/<int:team_id>/members/add/', views.add_team_member, name='add_team_member'),
    path('teams/<int:team_id>/members/<int:member_id>/remove/', 
         views.remove_team_member, name='remove_team_member'),
    
    # AJAX Endpoints for Dynamic Dropdowns
    path('ajax/units/', views.get_units, name='ajax_units'),
    path('ajax/supervisors/', views.get_supervisors, name='ajax_supervisors'),
    path('ajax/available-staff/', views.get_available_staff, name='ajax_available_staff'),
    path('ajax/filter-users/', views.filter_users, name='ajax_filter_users'),
]