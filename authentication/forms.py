from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import password_validation
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    """ Admin registeration page for users """
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
            'class': 'form-control','placeholder': 'Enter your email'})
    )
    first_name = forms.CharField(required=True, max_length=30, widget=forms.TextInput(attrs={
            'class': 'form-control','placeholder': 'Enter your first name' })
    )
    last_name = forms.CharField(required=True, max_length=30, widget=forms.TextInput(attrs={
            'class': 'form-control','placeholder': 'Enter your last name'})
    )
    department = forms.CharField(required=True, max_length=50, widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': 'Enter your department'})
    )
    unit = forms.CharField(required=True, max_length=50, widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': 'Enter your unit'})
    )
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={
            'class': 'form-control', 'placeholder': 'Enter your password'})
    )
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={
            'class': 'form-control', 'placeholder': 'Confirm your password'})
    )
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES, required=True, widget=forms.Select(attrs={
            'class': 'form-control', 'placeholder': 'Select role'
    }))
    team = forms.ChoiceField(choices=CustomUser.TEAM_CHOICES, required=True, widget=forms.Select(attrs={
            'class': 'form-control', 'placeholder': 'Select team'
    }))
    
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'department', 'unit', 'role', 'team', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        password_validation.validate_password(password2, self.instance)
        return password2
    
class UserEditForm(forms.ModelForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control'
    }))
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-control'
    }))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-control'
    }))
    department = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-control'
    }))
    unit = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-control'
    }))
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES, widget=forms.Select(attrs={
        'class': 'form-control'
    }))
    team = forms.ChoiceField(choices=CustomUser.TEAM_CHOICES, widget=forms.Select(attrs={
        'class': 'form-control'
    }))

    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'department', 'unit', 'role', 'team']

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )
    
class PasswordResetRequestForm(forms.Form):
    """Form for requesting password reset OTP"""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your registered email'
        })
    )

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if not CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("No user found with this email address.")
        return email

class OTPVerificationForm(forms.Form):
    """ Form for verifying OTP """
    otp = forms.CharField(
        label='Enter OTP',
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter 6-digit OTP'
        })
    )

class SetNewPasswordForm(forms.Form):
    """Form for setting new password after OTP verification"""
    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password'
        })
    )
    new_password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')
        
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError("Passwords don't match")
        return cleaned_data