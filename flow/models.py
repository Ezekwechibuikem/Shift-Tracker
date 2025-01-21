from django.conf import settings
from django.db import models
from django.utils import timezone
from datetime import timedelta

class SupervisorAssignment(models.Model):
    supervisor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='supervised_staff')
    staff = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assigned_supervisor')
    assigned_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.staff.first_name} assigned to {self.supervisor.first_name}"
    
class WeeklySchedule(models.Model):
    supervisor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_schedules')
    start_date = models.DateField()
    end_date = models.DateField()
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Schedule for week of {self.start_date}"

    def save(self, *args, **kwargs):
        if not self.end_date:
            self.end_date = self.start_date + timedelta(days=6)
        super().save(*args, **kwargs)

class StaffShift(models.Model):
    schedule = models.ForeignKey(WeeklySchedule, on_delete=models.CASCADE, related_name='shifts')
    staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shifts')
    date = models.DateField()
    is_off_day = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['staff', 'date']

    def __str__(self):
        return f"{self.staff.first_name} - {self.date} ({'Off' if self.is_off_day else 'Working'})"

class Holiday(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_holidays')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['date', 'name']

    def __str__(self):
        return f"{self.name} on {self.date}"

class Attendance(models.Model):
    staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='attendance')
    date = models.DateField()
    time_in = models.DateTimeField()
    time_out = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['staff', 'date']

    def __str__(self):
        return f"{self.staff.first_name} - {self.date}"

    @property
    def duration(self):
        if self.time_out:
            return self.time_out - self.time_in
        return None