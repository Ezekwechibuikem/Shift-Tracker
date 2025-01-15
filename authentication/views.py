from django.contrib.auth import login as auth_login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Q
from django.http import JsonResponse, HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.core.paginator import Paginator
from django.utils import timezone
from django.db import transaction
from django.conf import settings
import random
import string
import logging

from .forms import (
    CustomUserCreationForm, CustomAuthenticationForm, PasswordResetRequestForm,
    OTPVerificationForm, SetNewPasswordForm, TeamForm, TeamMemberForm
)
from .models import CustomUser, PasswordResetOTP, Team, TeamMember, Department, Unit

# Configure logging
logger = logging.getLogger(__name__)

@csrf_protect
def register_view(request):
    """Handle user registration with proper validation and role assignment"""
    if request.user.is_authenticated:
        return redirect('authentication:home')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save(commit=False)
                    
                    if user.role == 'ADMIN':
                        user.is_staff = True
                    
                    user.last_login_ip = request.META.get('REMOTE_ADDR')
                    user.save()
                    
                    auth_login(request, user)
                    messages.success(request, "Registration successful.")
                    logger.info(f"New user registered: {user.email}")
                    return redirect('authentication:home')
            except Exception as e:
                logger.error(f"Registration error: {str(e)}")
                messages.error(request, "An error occurred during registration.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'authentication/register.html', {'form': form})

@csrf_protect
def login_view(request):
    """Handle user login with security measures and proper error handling"""
    if request.user.is_authenticated:
        return redirect('authentication:home')
        
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(email=email, password=password)
            
            if user is not None:
                if not user.is_active:
                    messages.error(request, "Your account is inactive.")
                    logger.warning(f"Inactive user attempted login: {email}")
                    return redirect('authentication:login')
                    
                user.last_login_ip = request.META.get('REMOTE_ADDR')
                user.failed_login_attempts = 0
                user.save()
                
                auth_login(request, user)
                logger.info(f"User logged in: {email}")
                messages.success(request, f"Welcome back, {user.first_name}!")
                
                next_page = request.GET.get('next')
                if next_page and next_page.startswith('/'):
                    return redirect(next_page)
                return redirect('authentication:home')
            else:
                try:
                    user = CustomUser.objects.get(email=email)
                    user.failed_login_attempts += 1
                    user.save()
                    
                    if user.failed_login_attempts >= 5:
                        logger.warning(f"Multiple failed login attempts for user: {email}")
                        messages.error(request, "Too many failed attempts. Please reset your password.")
                        return redirect('authentication:password_reset_request')
                except CustomUser.DoesNotExist:
                    pass
                
                messages.error(request, "Invalid email or password.")
        else:
            messages.error(request, "Invalid email or password.")
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'authentication/login.html', {'form': form})

@login_required
def logout_view(request):
    """Handle user logout securely"""
    if request.user.is_authenticated:
        logger.info(f"User logged out: {request.user.email}")
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('authentication:login')

@login_required
def home(request):
    """Display home page with relevant user information"""
    context = {
        'user_teams': Team.objects.filter(
            Q(supervisor=request.user) | 
            Q(teammember__staff=request.user)
        ).distinct(),
        'department_stats': Department.objects.filter(is_active=True).annotate(
            team_count=Count('team'),
            member_count=Count('customuser')
        )
    }
    return render(request, 'flow/home.html', context)

def generate_otp():
    """Generate a secure OTP"""
    return ''.join(random.SystemRandom().choices(string.digits, k=6))

@csrf_protect
@require_http_methods(["GET", "POST"])
def password_reset_request(request):
    """Handle password reset requests with rate limiting and security measures"""
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = CustomUser.objects.get(email__iexact=email, is_active=True)
                
                recent_otps = PasswordResetOTP.objects.filter(
                    user=user,
                    created_at__gte=timezone.now() - timezone.timedelta(minutes=15)
                ).count()
                
                if recent_otps >= 3:
                    messages.error(request, 'Too many reset attempts. Please try again later.')
                    logger.warning(f"Multiple OTP requests for user: {email}")
                    return redirect('authentication:password_reset_request')
                
                otp = generate_otp()
                with transaction.atomic():
                    PasswordResetOTP.objects.filter(user=user, is_used=False).update(is_used=True)
                    PasswordResetOTP.objects.create(user=user, otp=otp)
                
                try:
                    send_mail(
                        'Password Reset OTP',
                        f'Your OTP for password reset is: {otp}\nThis OTP is valid for 10 minutes.',
                        settings.EMAIL_HOST_USER,
                        [email],
                        fail_silently=False,
                    )
                    request.session['reset_user_id'] = user.id
                    request.session['reset_email_sent'] = timezone.now().isoformat()
                    messages.success(request, 'OTP has been sent to your email.')
                    logger.info(f"Password reset OTP sent to: {email}")
                    return redirect('authentication:verify_otp')
                except Exception as e:
                    logger.error(f"Error sending reset email to {email}: {str(e)}")
                    messages.error(request, 'Error sending email. Please try again later.')
                    
            except CustomUser.DoesNotExist:
                messages.error(request, 'If a user exists with this email, they will receive reset instructions.')
            except Exception as e:
                logger.error(f"Password reset error: {str(e)}")
                messages.error(request, 'An error occurred. Please try again.')
    else:
        form = PasswordResetRequestForm()
    
    return render(request, 'authentication/password_reset_request.html', {'form': form})

@login_required
@user_passes_test(is_admin_or_supervisor)
def team_management(request):
    """Handle team listing and creation for admin/supervisor users"""
    if request.user.role == 'ADMIN':
        teams = Team.objects.all()
    else:
        teams = Team.objects.filter(supervisor=request.user)
    
    paginator = Paginator(teams, 10)
    page = request.GET.get('page', 1)
    teams = paginator.get_page(page)
    
    context = {
        'teams': teams,
        'can_create': request.user.role == 'ADMIN'
    }
    return render(request, 'staff/team_list.html', context)

@login_required
@user_passes_test(is_admin_or_supervisor)
@csrf_protect
def team_create(request):
    """
    Handle team creation with proper validation and permissions
    """
    if request.method == 'POST':
        form = TeamForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    team = form.save(commit=False)
                    
                    # Ensure proper permissions
                    if request.user.role != 'ADMIN':
                        if team.department != request.user.department or \
                           team.unit != request.user.unit:
                            raise PermissionDenied("You can only create teams in your department and unit.")
                    
                    team.save()
                    messages.success(request, f"Team '{team.name}' created successfully.")
                    logger.info(f"Team created: {team.name} by {request.user.email}")
                    return redirect('authentication:team_list')
            except PermissionDenied as e:
                messages.error(request, str(e))
            except Exception as e:
                logger.error(f"Team creation error: {str(e)}")
                messages.error(request, "An error occurred while creating the team.")
    else:
        initial = {}
        if request.user.role != 'ADMIN':
            initial = {
                'department': request.user.department,
                'unit': request.user.unit,
                'supervisor': request.user
            }
        form = TeamForm(initial=initial)
    
    return render(request, 'staff/team_form.html', {'form': form, 'is_create': True})

@login_required
@csrf_protect
def update_profile(request):
    """
    Handle user profile updates with validation
    """
    if request.method == 'POST':
        form = UserForm(request.POST, instance=request.user)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                
                # Prevent role escalation
                if request.user.role != 'ADMIN':
                    user.role = request.user.role
                
                user.save()
                messages.success(request, "Profile updated successfully.")
                logger.info(f"Profile updated for user: {request.user.email}")
                return redirect('authentication:profile')
            except Exception as e:
                logger.error(f"Profile update error: {str(e)}")
                messages.error(request, "An error occurred while updating your profile.")
    else:
        form = UserForm(instance=request.user)
    
    return render(request, 'staff/profile.html', {'form': form})

@login_required
def get_units_for_department(request, department_id):
    """
    AJAX endpoint to get units for a department
    """
    try:
        department = Department.objects.get(id=department_id, is_active=True)
        units = Unit.objects.filter(
            department=department,
            is_active=True
        ).values('id', 'name')
        return JsonResponse(list(units), safe=False)
    except Department.DoesNotExist:
        return JsonResponse([], safe=False)
    except Exception as e:
        logger.error(f"Error fetching units: {str(e)}")
        return JsonResponse({'error': 'An error occurred'}, status=500)

@login_required
def get_supervisors_for_unit(request, department_id, unit_id):
    """
    AJAX endpoint to get supervisors for a unit
    """
    try:
        supervisors = CustomUser.objects.filter(
            department_id=department_id,
            unit_id=unit_id,
            role__in=['ADMIN', 'SUPERVISOR'],
            is_active=True
        ).values('id', 'first_name', 'last_name')
        return JsonResponse(list(supervisors), safe=False)
    except Exception as e:
        logger.error(f"Error fetching supervisors: {str(e)}")
        return JsonResponse({'error': 'An error occurred'}, status=500)