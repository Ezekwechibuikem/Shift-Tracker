from django.contrib.auth.models import AbstractUser, BaseUserManager, Group, Permission
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, department, unit, password=None, **extra_fields):
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
            department=department,
            unit=unit,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, department='Admin', unit='Admin', password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
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
        ('admin', 'Admin'),
        ('supervisor', 'Supervisor'),
        ('staff', 'Staff'),
    )
    username = None
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    department = models.CharField(max_length=50)
    unit = models.CharField(max_length=50)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='admin')
    
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        related_name='custom_users'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        related_name='custom_users'
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = CustomUserManager()
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} <{self.email}>"
    
class PasswordResetOTP(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        from django.utils import timezone
        time_difference = timezone.now() - self.created_at
        return not self.is_used and time_difference.total_seconds() <= 600