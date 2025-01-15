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
    
    # path('register/', views.register, name='register'),
    # path('api/units/<int:department_id>/', views.get_units_for_department, name='get_units'),
    # path('api/supervisors/<int:department_id>/<int:unit_id>/', 
    #      views.get_supervisors_for_unit, name='get_supervisors'),
    # path('teams/', views.team_list, name='team_list'),
    # path('teams/create/', views.team_create, name='team_create'),
    # path('teams/<int:pk>/update/', views.team_update, name='team_update'),
    
    # path('users/', views.UserListView.as_view(), name='user_list'),
    # path('users/create/', views.UserCreateView.as_view(), name='user_create'),
    # path('users/<int:pk>/update/', views.UserUpdateView.as_view(), name='user_update'),
    # path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
    
    # path('teams/', views.TeamListView.as_view(), name='team_list'),
    # path('teams/create/', views.TeamCreateView.as_view(), name='team_create'),
    # path('teams/<int:pk>/update/', views.TeamUpdateView.as_view(), name='team_update'),
    # path('teams/<int:pk>/delete/', views.TeamDeleteView.as_view(), name='team_delete'),
    
    # path('reset-password/', views.PasswordResetView.as_view(), name='password_reset'),
    # path('reset-password/confirm/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]