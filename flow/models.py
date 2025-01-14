from django.db import models
from django.conf import settings
from django.utils import timezone

class StaffSupervisor(models.Model):
    staff = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='staff_supervisor')
    supervisor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='supervised_staff')
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='supervisor_assignments')
    assigned_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.staff.get_full_name()} - {self.supervisor.get_full_name()}"