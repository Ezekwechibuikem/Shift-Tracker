from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Count
from django.utils.translation import gettext_lazy as _
from django.core.validators import EmailValidator, RegexValidator
from django.utils import timezone
import re

class CustomUserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        if not first_name:
            raise ValueError('First name is required')
        if not last_name:
            raise ValueError('Last name is required')
        if not password:
            raise ValueError('Password is required')
            
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'ADMIN')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            **extra_fields
        )

class Department(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Za-z0-9\s-]+$',
                message='Department name can only contain letters, numbers, spaces and hyphens'
            )
        ]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active'])
        ]

    def __str__(self):
        return self.name

    def clean(self):
        self.name = self.name.strip()
        if not self.name:
            raise ValidationError('Department name cannot be empty or just whitespace')

class Unit(models.Model):
    name = models.CharField(
        max_length=100,
        validators=[
            RegexValidator(
                regex=r'^[A-Za-z0-9\s-]+$',
                message='Unit name can only contain letters, numbers, spaces and hyphens'
            )
        ]
    )
    department = models.ForeignKey(
        Department, 
        on_delete=models.PROTECT,
        related_name='units'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['name', 'department']
        ordering = ['department', 'name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active'])
        ]

    def __str__(self):
        return f"{self.name} ({self.department.name})"

    def clean(self):
        self.name = self.name.strip()
        if not self.name:
            raise ValidationError('Unit name cannot be empty or just whitespace')
        if not self.department.is_active:
            raise ValidationError('Cannot create unit in inactive department')

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('SUPERVISOR', 'Supervisor'),
        ('STAFF', 'Staff'),
    )
    
    username = None
    email = models.EmailField(_('email address'), unique=True, validators=[EmailValidator()])
    first_name = models.CharField(max_length=30, validators=[
            RegexValidator(regex=r'^[A-Za-z\s-]+$', message='First name can only contain letters, spaces and hyphens')])
    last_name = models.CharField(max_length=30, validators=[
            RegexValidator(regex=r'^[A-Za-z\s-]+$', message='Last name can only contain letters, spaces and hyphens')])
    department = models.ForeignKey(Department, on_delete=models.PROTECT, null=True)
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STAFF')
    supervisor = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='supervised_users')
    is_active = models.BooleanField(default=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    last_password_change = models.DateTimeField(default=timezone.now)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = CustomUserManager()

    class Meta:
        ordering = ['email']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['department']),
            models.Index(fields=['unit']),
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} <{self.email}>"

    def clean(self):
        super().clean()
        self.first_name = self.first_name.strip()
        self.last_name = self.last_name.strip()
        
        if self.unit and self.department and self.unit.department != self.department:
            raise ValidationError('Unit must belong to the selected department')
            
        if self.supervisor:
            if self.supervisor == self:
                raise ValidationError('User cannot be their own supervisor')
            if self.supervisor.department != self.department:
                raise ValidationError('Supervisor must be from the same department')
            if self.supervisor.unit != self.unit:
                raise ValidationError('Supervisor must be from the same unit')
            if self.supervisor.role not in ['SUPERVISOR']:
                raise ValidationError('Supervisor must have SUPERVISOR role')

        if self.role == 'STAFF' and self.pk:
            if self.supervised_users.exists():
                raise ValidationError('Staff members cannot have supervised users')
                
    def is_admin(self):
        """Check if the user has admin privileges"""
        return self.role == 'ADMIN' or self.is_superuser
    
    def is_supervisor(self):
        """Check if the user has supervisor role"""
        return self.role == 'SUPERVISOR'
    
    def is_staff_member(self):
        """Check if the user has staff role"""
        return self.role == 'STAFF'

class Team(models.Model):
    name = models.CharField(max_length=100, validators=[
            RegexValidator(regex=r'^[A-Za-z0-9\s-]+$', message='Team name can only contain letters, numbers, spaces and hyphens')])
    number = models.CharField(max_length=20,validators=[
            RegexValidator(regex=r'^[A-Za-z0-9-]+$',message='Team number can only contain letters, numbers and hyphens')])
    description = models.TextField(blank=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT)
    supervisor = models.ForeignKey(CustomUser, on_delete=models.PROTECT, related_name='supervised_teams')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['number', 'department']
        ordering = ['department', 'unit', 'name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['number']),
            models.Index(fields=['is_active'])
        ]

    def __str__(self):
        return f"{self.name} - {self.number}"

    def clean(self):
        self.name = self.name.strip()
        self.number = self.number.strip()
        
        if not self.name:
            raise ValidationError('Team name cannot be empty or just whitespace')
        if not self.number:
            raise ValidationError('Team number cannot be empty or just whitespace')
            
        if self.unit and self.department and self.unit.department != self.department:
            raise ValidationError('Unit must belong to the selected department')
            
        if hasattr(self, 'supervisor') and self.supervisor_id:
            if self.supervisor.department != self.department:
                raise ValidationError('Supervisor must belong to the same department')
            if self.supervisor.unit != self.unit:
                raise ValidationError('Supervisor must belong to the same unit')
            if self.supervisor.role not in ['SUPERVISOR']:
                raise ValidationError('Team supervisor must have SUPERVISOR role')
            if not self.supervisor.is_active:
                raise ValidationError('Team supervisor must be active')

class TeamMember(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members')
    staff = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='team_memberships')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['team', 'staff']
        ordering = ['team', 'staff__first_name', 'staff__last_name']
        indexes = [
            models.Index(fields=['is_active'])
        ]

    def __str__(self):
        return f"{self.staff} - {self.team}"

    def clean(self):
        if self.staff.department != self.team.department:
            raise ValidationError('Staff member must belong to the same department as the team')
        if self.staff.unit != self.team.unit:
            raise ValidationError('Staff member must belong to the same unit as the team')
        if not self.staff.is_active:
            raise ValidationError('Cannot add inactive staff member to team')
        if not self.team.is_active:
            raise ValidationError('Cannot add member to inactive team')

class PasswordResetOTP(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['otp', 'is_used'])
        ]

    def __str__(self):
        return f"OTP for {self.user.email}"

    def is_valid(self):
        if self.is_used or self.attempts >= 3:
            return False
            
        time_difference = timezone.now() - self.created_at
        return time_difference.total_seconds() <= 600  

    def increment_attempts(self):
        self.attempts += 1
        self.save()