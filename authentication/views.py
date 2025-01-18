from django.contrib.auth import login as auth_login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Q
from django.http import JsonResponse, HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.core.paginator import Paginator
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from django.core.mail import send_mail
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

def generate_otp():
    """Generate a secure OTP"""
    return ''.join(random.SystemRandom().choices(string.digits, k=6))

@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_admin()) 
def register_view(request):
    """Handle user creation by admin only"""
    if not request.user.is_admin():
        messages.error(request, "You don't have permission to create users.")
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
                    
                    messages.success(request, f"User {user.email} created successfully.")
                    logger.info(f"New user created by admin: {user.email}")
                    return redirect('authentication:user_list')
            except Exception as e:
                logger.error(f"User creation error: {str(e)}")
                messages.error(request, "An error occurred during user creation.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'staff/user_form.html', {
        'form': form,
        'is_create': True,
        'title': 'Create New User'
    })

@csrf_protect
def login_view(request):
    """Handle user login with security measures"""
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
    """Handle user logout"""
    if request.user.is_authenticated:
        logger.info(f"User logged out: {request.user.email}")
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('authentication:login')

@login_required
def home(request):
    """Display home page with relevant user information"""
    context = {}
    
    if request.user.is_admin():
        # For admin, show overall statistics
        context.update({
            'department_stats': Department.objects.filter(is_active=True).annotate(
                team_count=Count('team'),
                member_count=Count('customuser')
            ),
            'total_users': CustomUser.objects.count(),
            'total_teams': Team.objects.count()
        })
    elif request.user.is_supervisor():
        # For supervisor, show their teams
        context.update({
            'user_teams': Team.objects.filter(supervisor=request.user)
        })
    else:
        # For regular staff, show teams they're part of
        context.update({
            'user_teams': Team.objects.filter(
                members__staff=request.user
            ).distinct()
        })
    
    return render(request, 'flow/home.html', context)


@csrf_protect
@require_http_methods(["GET", "POST"])
def password_reset_request(request):
    """Handle password reset requests with rate limiting"""
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

@csrf_protect
@require_http_methods(["GET", "POST"])
def verify_otp(request):
    """Verify OTP for password reset"""
    if 'reset_user_id' not in request.session:
        return redirect('authentication:password_reset_request')
        
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data['otp']
            user_id = request.session['reset_user_id']
            
            try:
                otp_obj = PasswordResetOTP.objects.filter(
                    user_id=user_id,
                    is_used=False
                ).latest('created_at')
                
                if otp_obj.is_valid():
                    if otp_obj.otp == otp:
                        otp_obj.is_used = True
                        otp_obj.save()
                        request.session['otp_verified'] = True
                        messages.success(request, 'OTP verified successfully.')
                        return redirect('authentication:set_new_password')
                    else:
                        otp_obj.increment_attempts()
                        messages.error(request, 'Invalid OTP.')
                else:
                    messages.error(request, 'OTP has expired or too many attempts.')
                    return redirect('authentication:password_reset_request')
                    
            except PasswordResetOTP.DoesNotExist:
                messages.error(request, 'Invalid OTP.')
                return redirect('authentication:password_reset_request')
    else:
        form = OTPVerificationForm()
    
    return render(request, 'authentication/verify_otp.html', {'form': form})

@csrf_protect
@require_http_methods(["GET", "POST"])
def set_new_password(request):
    """Set new password after OTP verification"""
    if 'reset_user_id' not in request.session or 'otp_verified' not in request.session:
        return redirect('authentication:password_reset_request')
        
    if request.method == 'POST':
        form = SetNewPasswordForm(request.POST)
        if form.is_valid():
            try:
                user = CustomUser.objects.get(id=request.session['reset_user_id'])
                user.set_password(form.cleaned_data['new_password1'])
                user.failed_login_attempts = 0
                user.last_password_change = timezone.now()
                user.save()
                
                # Clear session data
                del request.session['reset_user_id']
                del request.session['otp_verified']
                if 'reset_email_sent' in request.session:
                    del request.session['reset_email_sent']
                
                messages.success(request, 'Password has been reset successfully. Please login with your new password.')
                logger.info(f"Password reset successful for user: {user.email}")
                return redirect('authentication:login')
                
            except CustomUser.DoesNotExist:
                messages.error(request, 'Invalid request.')
                return redirect('authentication:password_reset_request')
    else:
        form = SetNewPasswordForm()
    
    return render(request, 'authentication/set_new_password.html', {'form': form})

@login_required
@csrf_protect
def update_profile(request):
    """Handle user profile updates"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, instance=request.user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save(commit=False)
                    
                    # Keep admin status if user is already admin
                    if not request.user.is_admin():
                        user.role = request.user.role
                    
                    user.save()
                    messages.success(request, "Profile updated successfully.")
                    logger.info(f"Profile updated for user: {request.user.email}")
                    return redirect('authentication:profile')
            except Exception as e:
                logger.error(f"Profile update error: {str(e)}")
                messages.error(request, "An error occurred while updating your profile.")
    else:
        form = CustomUserCreationForm(instance=request.user)

    # Get user's teams based on role
    if request.user.is_admin():
        # For admin, show supervised teams
        user_teams = Team.objects.filter(supervisor=request.user)
    else:
        # For regular users, show teams they're a member of
        user_teams = Team.objects.filter(members__staff=request.user)
    
    context = {
        'form': form,
        'user_teams': user_teams.distinct(),
        'supervised_teams': request.user.supervised_teams.all() if request.user.is_supervisor() else None,
        'team_memberships': request.user.team_memberships.all()
    }
    
    return render(request, 'staff/profile.html', context)

@login_required
@user_passes_test(lambda u: u.is_admin())
def user_list(request):
    """List and filter users"""
    users = CustomUser.objects.all()
    
    # Apply filters
    department_id = request.GET.get('department')
    unit_id = request.GET.get('unit')
    role = request.GET.get('role')
    
    if department_id:
        users = users.filter(department_id=department_id)
    if unit_id:
        users = users.filter(unit_id=unit_id)
    if role:
        users = users.filter(role=role)
        
    context = {
        'users': users,
        'departments': Department.objects.filter(is_active=True),
        'units': Unit.objects.filter(is_active=True),
        'roles': CustomUser.ROLE_CHOICES
    }
    return render(request, 'staff/user_list.html', context)

@login_required
@user_passes_test(lambda u: u.is_admin())
@csrf_protect
def user_update(request, user_id):
    """Update user details - admin only"""
    user_obj = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, instance=user_obj)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    messages.success(request, f"User {user.email} updated successfully.")
                    logger.info(f"User updated by admin: {user.email}")
                    return redirect('authentication:user_list')
            except Exception as e:
                logger.error(f"User update error: {str(e)}")
                messages.error(request, "An error occurred while updating the user.")
    else:
        form = CustomUserCreationForm(instance=user_obj)
        # Pre-populate department dependent fields
        if user_obj.department:
            form.fields['unit'].queryset = Unit.objects.filter(
                department=user_obj.department,
                is_active=True
            )
        if user_obj.department and user_obj.unit:
            form.fields['supervisor'].queryset = CustomUser.objects.filter(
                department=user_obj.department,
                unit=user_obj.unit,
                role='SUPERVISOR',
                is_active=True
            ).exclude(id=user_obj.id)
    
    return render(request, 'staff/user_form.html', {
        'form': form,
        'is_update': True,
        'user_obj': user_obj
    })
    
@login_required
def filter_users(request):
    """AJAX endpoint to filter users"""
    users = CustomUser.objects.all()
    
    # Apply filters
    department_id = request.GET.get('department')
    unit_id = request.GET.get('unit')
    role = request.GET.get('role')
    
    if department_id:
        users = users.filter(department_id=department_id)
    if unit_id:
        users = users.filter(unit_id=unit_id)
    if role:
        users = users.filter(role=role)
    
    # Prepare data for JSON response
    users_data = users.values(
        'id', 'email', 'first_name', 'last_name',
        'department__name', 'unit__name', 'role',
        'is_active'
    )
    
    return JsonResponse(list(users_data), safe=False)

@login_required
@user_passes_test(lambda u: u.is_admin() or u.is_supervisor())
def team_list(request):
    """List teams based on user role"""
    if request.user.is_admin():
        teams = Team.objects.all()
    else:
        teams = Team.objects.filter(supervisor=request.user)
    
    department_id = request.GET.get('department')
    unit_id = request.GET.get('unit')
    
    if department_id:
        teams = teams.filter(department_id=department_id)
    if unit_id:
        teams = teams.filter(unit_id=unit_id)
        
    context = {
        'teams': teams,
        'departments': Department.objects.filter(is_active=True),
        'units': Unit.objects.filter(is_active=True)
    }
    return render(request, 'staff/team_list.html', context)

@login_required
@user_passes_test(lambda u: u.is_admin())
@csrf_protect
def team_create(request):
    """Create new team"""
    if request.method == 'POST':
        form = TeamForm(request.POST)
        if form.is_valid():
            try:
                team = form.save()
                messages.success(request, f"Team '{team.name}' created successfully.")
                return redirect('authentication:team_list')
            except Exception as e:
                logger.error(f"Team creation error: {str(e)}")
                messages.error(request, "An error occurred while creating the team.")
    else:
        form = TeamForm()
    
    return render(request, 'staff/team_form.html', {'form': form, 'is_create': True})

@login_required
@user_passes_test(lambda u: u.is_admin() or u.is_supervisor())
@csrf_protect
def team_update(request, team_id):
    """Update existing team"""
    team = get_object_or_404(Team, id=team_id)
    
    if not request.user.is_admin() and team.supervisor != request.user:
        raise PermissionDenied
        
    if request.method == 'POST':
        form = TeamForm(request.POST, instance=team)
        if form.is_valid():
            try:
                team = form.save()
                messages.success(request, f"Team '{team.name}' updated successfully.")
                return redirect('authentication:team_list')
            except Exception as e:
                logger.error(f"Team update error: {str(e)}")
                messages.error(request, "An error occurred while updating the team.")
    else:
        form = TeamForm(instance=team)
    
    return render(request, 'staff/team_form.html', {
        'form': form,
        'is_create': False,
        'team': team
    })

# AJAX endpoints
@login_required
def get_units(request):
    """AJAX endpoint to get units for a department"""
    department_id = request.GET.get('department')
    if department_id:
        units = Unit.objects.filter(
            department_id=department_id,
            is_active=True
        ).values('id', 'name', 'is_active')
        return JsonResponse(list(units), safe=False)
    return JsonResponse([], safe=False)

@login_required
def get_supervisors(request):
    """AJAX endpoint to get supervisors for a unit"""
    department_id = request.GET.get('department')
    unit_id = request.GET.get('unit')
    if department_id and unit_id:
        supervisors = CustomUser.objects.filter(
            department_id=department_id,
            unit_id=unit_id,
            role='SUPERVISOR',
            is_active=True
        ).values('id', 'first_name', 'last_name', 'email')
        # Format supervisor names for display
        formatted_supervisors = [
            {**supervisor, 
             'display_name': f"{supervisor['first_name']} {supervisor['last_name']} ({supervisor['email']})"}
            for supervisor in supervisors
        ]
        return JsonResponse(formatted_supervisors, safe=False)
    return JsonResponse([], safe=False)

# @login_required
# @user_passes_test(lambda u: u.is_admin() or u.is_supervisor()) #change to template permission 
# def team_member_list(request, team_id):
#     """AJAX endpoint to get team members"""
#     team = get_object_or_404(Team, id=team_id)
    
#     # Check permissions
#     if not (request.user.is_admin() or team.supervisor == request.user):
#         return JsonResponse({'error': 'Permission denied'}, status=403)
        
#     members = TeamMember.objects.filter(team=team).select_related('staff').values(
#         'id',
#         'staff__id',
#         'staff__first_name',
#         'staff__last_name',
#         'staff__email',
#         'is_active'
#     )
    
#     return JsonResponse(list(members), safe=False)

@login_required
@user_passes_test(lambda u: u.is_admin() or u.is_supervisor())
def team_member_list(request, team_id):
    """Manage team members"""
    team = get_object_or_404(Team, id=team_id)
    
    # Check if user can manage this team
    if not request.user.is_admin() and team.supervisor != request.user:
        raise PermissionDenied
    
    if request.method == 'POST':
        form = TeamMemberForm(request.POST)
        if form.is_valid():
            try:
                member = form.save(commit=False)
                member.team = team
                member.save()
                messages.success(request, "Team member added successfully.")
                return redirect('authentication:team_members', team_id=team.id)
            except Exception as e:
                logger.error(f"Error adding team member: {str(e)}")
                messages.error(request, "An error occurred while adding team member.")
    else:
        form = TeamMemberForm()
        form.fields['staff'].queryset = CustomUser.objects.filter(
            department=team.department,
            unit=team.unit,
            is_active=True,
            role='STAFF'
        ).exclude(
            team_memberships__team=team
        )
    
    context = {
        'team': team,
        'form': form,
        'members': team.members.select_related('staff').all()
    }
    return render(request, 'staff/team_members.html', context)

@login_required
@user_passes_test(lambda u: u.is_admin() or u.is_supervisor())
def add_team_member(request, team_id):
    """AJAX endpoint to add team member"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)
        
    team = get_object_or_404(Team, id=team_id)
    
    # Check permissions
    if not request.user.is_admin() and team.supervisor != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
        
    try:
        staff_id = request.POST.get('staff_id')
        staff = CustomUser.objects.get(id=staff_id, is_active=True)
        
        # Validate department and unit
        if staff.department != team.department or staff.unit != team.unit:
            return JsonResponse({
                'error': 'Staff member must belong to the same department and unit'
            }, status=400)
            
        # Check if already a member
        if TeamMember.objects.filter(team=team, staff=staff).exists():
            return JsonResponse({
                'error': 'Staff member is already in the team'
            }, status=400)
            
        member = TeamMember.objects.create(team=team, staff=staff)
        
        return JsonResponse({
            'status': 'success',
            'member': {
                'id': member.id,
                'staff_id': staff.id,
                'name': staff.get_full_name(),
                'email': staff.email
            }
        })
        
    except CustomUser.DoesNotExist:
        return JsonResponse({'error': 'Staff member not found'}, status=404)
    except Exception as e:
        logger.error(f"Error adding team member: {str(e)}")
        return JsonResponse({'error': 'An error occurred'}, status=500)

@login_required
@require_http_methods(["POST"])
def remove_team_member(request, team_id, member_id):
    """AJAX endpoint to remove team member"""
    team = get_object_or_404(Team, id=team_id)
    
    # Check permissions
    if not request.user.is_admin() and team.supervisor != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
        
    try:
        member = TeamMember.objects.get(id=member_id, team=team)
        member.delete()
        return JsonResponse({
            'status': 'success',
            'message': 'Member removed successfully'
        })
    except TeamMember.DoesNotExist:
        return JsonResponse({'error': 'Member not found'}, status=404)
    except Exception as e:
        logger.error(f"Error removing team member: {str(e)}")
        return JsonResponse({'error': 'An error occurred'}, status=500)

@login_required
def team_details(request, team_id):
    """View team details and members"""
    team = get_object_or_404(Team, id=team_id)
    
    # Check if user has access to this team
    if not (request.user.is_admin() or 
            team.supervisor == request.user or 
            team.members.filter(staff=request.user).exists()):
        raise PermissionDenied
    
    context = {
        'team': team,
        'members': team.members.select_related('staff').all(),
        'can_manage': request.user.is_admin() or team.supervisor == request.user
    }
    return render(request, 'staff/team_details.html', context)

@login_required
def get_available_staff(request):
    """AJAX endpoint to get available staff for team assignment"""
    department_id = request.GET.get('department')
    unit_id = request.GET.get('unit')
    team_id = request.GET.get('team_id')
    
    if not department_id or not unit_id:
        return JsonResponse([], safe=False)
        
    staff = CustomUser.objects.filter(
        department_id=department_id,
        unit_id=unit_id,
        is_active=True,
        role='STAFF'
    )
    
    # Exclude staff already in the team
    if team_id:
        staff = staff.exclude(team_memberships__team_id=team_id)
    
    staff_list = staff.values('id', 'first_name', 'last_name', 'email')
    formatted_staff = [
        {**member, 
         'display_name': f"{member['first_name']} {member['last_name']} ({member['email']})"}
        for member in staff_list
    ]
    
    return JsonResponse(formatted_staff, safe=False)