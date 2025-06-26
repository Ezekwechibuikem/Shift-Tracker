from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, unit, password=None, **extra_fields):
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
            unit=unit,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, department='Admin', unit='Admin', password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'ADMIN')  # Set default role for superuser
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            department=department,
            unit=unit,
            password=password,
            **extra_fields
        )

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('HR', 'Human Resources'),
        ('IT', 'Information Technology'),
        ('SUPERVISOR', 'Supervisor'),
        ('STAFF', 'Staff'),
    )
    TEAM_CHOICES = (
        ('TeamLead', 'Team Lead'),
        ('TEAM1', 'Team 1'),
        ('TEAM2', 'Team 2'),
        ('TEAM3', 'Team 3'),
        ('TEAM4', 'Team 4'),
        ('TEAM5', 'Team 5'),
        ('TEAM6', 'Team 6'),
        ('TEAM7', 'Team 7'),
        ('TEAM8', 'Team 8'),
        ('TEAM9', 'Team 9'),
        ('TEAM10', 'Team 10'),
        ('Support', 'Support Team'),
    )
    DEPARTMENT_CHOICES = (
        ('Admin', 'Admin'),
        ('HR', 'Human Resources'),
        ('Finance', 'Finance'),
        ('IT', 'Information Technology'),
        ('HI', 'Health Informatics'),
        ('M&E', 'Monitory and Evaluation'),
        ('Survey', 'Surveliance'),
        ('Support', 'Facility Services Support'),
    )
    username = None
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, default='Admin')
    unit = models.CharField(max_length=50)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STAFF')
    team = models.CharField(max_length=20, choices=TEAM_CHOICES, null=True, blank=True, default='Team 0')
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = CustomUserManager()
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}, email -- {self.email}, department -- {self.get_department_display()}, Team -- {self.get_team_display()}"
    
    def is_admin(self):
        return self.role == 'ADMIN' or self.is_superuser
    
    def is_hr(self):
        return self.role == 'HR'
    
    def is_it(self):
        return self.role == 'IT'
    
    def is_supervisor(self):
        return self.role == 'SUPERVISOR'
    
    def is_staff_member(self):
        return self.role == 'STAFF'

class PasswordResetOTP(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        from django.utils import timezone
        time_difference = timezone.now() - self.created_at
        return not self.is_used and time_difference.total_seconds() <= 600