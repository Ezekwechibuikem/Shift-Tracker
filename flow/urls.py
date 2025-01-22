from django.urls import path
from . import views

app_name = 'flow'

urlpatterns = [
    path('supervisors/', views.supervisor_dashboard, name='supervisor_dashboard'),
    path('supervisor/<int:supervisor_id>/assign/', views.assign_staff, name='assign_staff'),
    path('supervisor/<int:supervisor_id>/remove/<int:staff_id>/', 
         views.remove_staff_assignment, name='remove_staff_assignment'),
    path('team-staff/', views.team_staff_list, name='team_staff_list'),
    
    path('schedule/generate/', views.generate_schedule, name='generate_schedule'),
    path('schedule/view/<int:schedule_id>/', views.view_schedule, name='view_schedule'),
    path('schedule/view/', views.view_schedule, name='current_schedule'),
    path('schedule/edit/<int:schedule_id>/', views.edit_schedule, name='edit_schedule'),
    path('holidays/', views.manage_holidays, name='manage_holidays'),
    path('attendance/', views.check_attendance, name='check_attendance'),
    
    path('clear-message/', views.clear_message, name='clear_message'),
    
]