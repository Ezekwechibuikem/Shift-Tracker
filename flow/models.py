from django.db import models
from authentication.models import CustomUser

class StaffMember(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    supervisor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='supervised_team')
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
    
    @property
    def team(self):
        return self.user.team

class WeeklySchedule(models.Model):
    staff_member = models.ForeignKey(StaffMember, on_delete=models.CASCADE)
    start_date = models.DateField()
    created_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='created_schedules'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['staff_member', 'start_date']

    def __str__(self):
        return f"Schedule for {self.staff_member} - {self.start_date}"

class DayShift(models.Model):
    SHIFT_STATUS = [
        ('WORKING', 'Working'),
        ('OFF', 'Off Day'),
    ]
    
    schedule = models.ForeignKey(WeeklySchedule, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=20, choices=SHIFT_STATUS)
    
    class Meta:
        unique_together = ['user', 'date']

    def __str__(self):
        return f"{self.user} - {self.date} - {self.status}"

class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected')
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='leave_requests')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    reviewed_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='reviewed_leaves'
    )
    reviewed_at = models.DateTimeField(null=True)

    def __str__(self):
        return f"{self.user} - {self.start_date} to {self.end_date}"

class DailyReport(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='daily_reports')
    date = models.DateField()
    report_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'date']

    def __str__(self):
        return f"{self.user} - {self.date}"

class ReportComment(models.Model):
    report = models.ForeignKey(DailyReport, on_delete=models.CASCADE, related_name='comments')
    supervisor = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='report_comments'
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.supervisor} on {self.report}"