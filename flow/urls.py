from django.urls import path
from . import views

app_name = 'flow'

urlpatterns = [
    path('supervisors/', views.supervisor_dashboard, name='supervisor_dashboard'),
    path('supervisor/<int:supervisor_id>/assign/', views.assign_staff, name='assign_staff'),
    path('supervisor/<int:supervisor_id>/remove/<int:staff_id>/', 
         views.remove_staff_assignment, name='remove_staff_assignment'),
    path('team-staff/', views.team_staff_list, name='team_staff_list'),
]