from django.urls import path
from . import views

app_name = 'flow'

urlpatterns = [
    path('schedules/create/', views.create_weekly_schedule, name='create_schedule'),
    
]