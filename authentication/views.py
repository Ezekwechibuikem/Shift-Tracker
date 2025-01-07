from django.contrib.auth import login as auth_login, logout
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import Group
from .forms import CustomUserCreationForm, CustomAuthenticationForm, PasswordResetRequestForm, OTPVerificationForm, SetNewPasswordForm
import random
import string
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone
from .models import CustomUser, PasswordResetOTP
from django.conf import settings

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = form.cleaned_data['role']
            group = Group.objects.get(name=role.capitalize())
            user.groups.add(group)
            if role == 'admin':
                user.is_staff = True
                user.save()
            auth_login(request, user)
            messages.success(request, "Registration successful.")
            return redirect('authentication:login') 
        messages.error(request, "Unsuccessful registration. Invalid information.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'authentication/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(email=email, password=password)
            if user is not None:
                auth_login(request, user)
                messages.success(request, f"Welcome back, {user.first_name}!")
                return redirect('authentication:home') 
            else:
                messages.error(request, "Invalid email or password.")
                return render(request, 'authentication/login.html')
        else:
            messages.error(request, "Invalid email or password.")
            return render(request, 'authentication/login.html')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'authentication/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('authentication:login')

@login_required
def home(request):
    return render(request, 'authentication/home.html')


def generate_otp():
    """ Generate a random 6-digit OTP """
    return ''.join(random.choices(string.digits, k=6))


def password_reset_request(request):
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            try:
                email = form.cleaned_data['email']
                user = CustomUser.objects.get(email__iexact=email)
                otp = ''.join(random.choices(string.digits, k=6))
                
                PasswordResetOTP.objects.filter(user=user, is_used=False).update(is_used=True)
                PasswordResetOTP.objects.create(user=user, otp=otp)
                
                try:
                    send_mail(
                        'Password Reset OTP',
                        f'Your OTP for password reset is: {otp}\nThis OTP is valid for 10 minutes.',
                        settings.EMAIL_HOST_USER,
                        [email],
                        fail_silently=True,
                    )
                    request.session['reset_user_id'] = user.id
                    messages.success(request, 'OTP has been sent to your email.')
                    return redirect('authentication:verify_otp')
                except Exception as e:
                    messages.error(request, 'Error sending email. Please try again later.')
                    
            except CustomUser.DoesNotExist:
                messages.error(request, 'No user found with this email address.')
            except Exception as e:
                messages.error(request, 'An error occurred. Please try again.')
    else:
        form = PasswordResetRequestForm()
    
    return render(request, 'authentication/password_reset_request.html', {'form': form})

def verify_otp(request):
    """ Verify the OTP entered by user """
    if 'reset_user_id' not in request.session:
        messages.error(request, 'Please start password reset process again.')
        return redirect('authentication:password_reset_request')
        
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            user = CustomUser.objects.get(id=request.session['reset_user_id'])
            otp = form.cleaned_data['otp']
            otp_obj = PasswordResetOTP.objects.filter(
                user=user,
                otp=otp,
                is_used=False
            ).order_by('-created_at').first()
            
            if otp_obj and otp_obj.is_valid():
                otp_obj.is_used = True
                otp_obj.save()
                request.session['otp_verified'] = True
                return redirect('authentication:set_new_password')
            else:
                messages.error(request, 'Invalid or expired OTP.')
    else:
        form = OTPVerificationForm()
    
    return render(request, 'authentication/verify_otp.html', {'form': form})

def set_new_password(request):
    """Set new password after OTP verification"""
    if 'reset_user_id' not in request.session or 'otp_verified' not in request.session:
        messages.error(request, 'Please complete the verification process first.')
        return redirect('authentication:password_reset_request')
        
    if request.method == 'POST':
        form = SetNewPasswordForm(request.POST)
        if form.is_valid():
            user = CustomUser.objects.get(id=request.session['reset_user_id'])
            user.set_password(form.cleaned_data['new_password1'])
            user.save()
            del request.session['reset_user_id']
            del request.session['otp_verified']
            
            messages.success(request, 'Password has been reset successfully. You can now login.')
            return redirect('authentication:login')
    else:
        form = SetNewPasswordForm()
    
    return render(request, 'authentication/set_new_password.html', {'form': form})
