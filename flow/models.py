from django.conf import settings
from django.db import models

class SupervisorAssignment(models.Model):
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='supervised_staff'
    )
    staff = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assigned_supervisor'
    )
    assigned_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.staff.first_name} assigned to {self.supervisor.first_name}"