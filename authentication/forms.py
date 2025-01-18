from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from .models import Department, Unit, CustomUser, Team, TeamMember

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}))
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your first name'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your last name'}))

    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name',
                  'department', 'unit', 'role', 'supervisor')
        widgets = {
            'department': forms.Select(attrs={'class': 'form-control'}),
            'unit': forms.Select(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'supervisor': forms.Select(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

        self.fields['department'].queryset = Department.objects.filter(
            is_active=True)

        if self.instance and self.instance.department:
            self.fields['unit'].queryset = Unit.objects.filter(department=self.instance.department, is_active=True)
        else:
            self.fields['unit'].queryset = Unit.objects.none()

        if self.instance and self.instance.department and self.instance.unit:
            self.fields['supervisor'].queryset = CustomUser.objects.filter(
                department=self.instance.department,
                unit=self.instance.unit,
                role__in=['SUPERVISOR'],
                is_active=True
            ).exclude(id=self.instance.id if self.instance.id else None)
        else:
            self.fields['supervisor'].queryset = CustomUser.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        department = cleaned_data.get('department')
        unit = cleaned_data.get('unit')
        role = cleaned_data.get('role')
        supervisor = cleaned_data.get('supervisor')

        if unit and department:
            if unit.department != department:
                raise ValidationError('Selected unit must belong to the selected department')
            if not unit.is_active:
                raise ValidationError('Selected unit is inactive')

        if supervisor:
            if supervisor.department != department:
                raise ValidationError('Supervisor must belong to the same department')
            if supervisor.unit != unit:
                raise ValidationError('Supervisor must belong to the same unit')
            if supervisor.role not in ['SUPERVISOR']:
                raise ValidationError('Supervisor must have SUPERVISOR role')
            if not supervisor.is_active:
                raise ValidationError('Selected supervisor is inactive')

        return cleaned_data

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password'}))

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')

        if username:
            user = CustomUser.objects.filter(email__iexact=username).first()
            if user and not user.is_active:
                raise ValidationError('This account is inactive')

        return cleaned_data

class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'number', 'department',
                  'unit', 'supervisor', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'number': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'unit': forms.Select(attrs={'class': 'form-control'}),
            'supervisor': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set initial querysets
        self.fields['department'].queryset = Department.objects.filter(
            is_active=True)
        self.fields['unit'].queryset = Unit.objects.none()
        self.fields['supervisor'].queryset = CustomUser.objects.none()

        # If instance exists and has a department
        if self.instance and hasattr(self.instance, 'department_id') and self.instance.department_id:
            # Set unit queryset based on department
            self.fields['unit'].queryset = Unit.objects.filter(
                department=self.instance.department,
                is_active=True
            )

            # If instance also has a unit
            if hasattr(self.instance, 'unit_id') and self.instance.unit_id:
                # Set supervisor queryset
                self.fields['supervisor'].queryset = CustomUser.objects.filter(
                    role__in=['ADMIN', 'SUPERVISOR'],
                    department=self.instance.department,
                    unit=self.instance.unit,
                    is_active=True
                )

    def clean(self):
        cleaned_data = super().clean()
        department = cleaned_data.get('department')
        unit = cleaned_data.get('unit')
        supervisor = cleaned_data.get('supervisor')

        if unit and department:
            if unit.department != department:
                raise ValidationError('Selected unit must belong to the selected department')
            if not unit.is_active:
                raise ValidationError('Selected unit is inactive')

        if supervisor:
            if supervisor.department != department:
                raise ValidationError('Supervisor must belong to the same department')
            if supervisor.unit != unit:
                raise ValidationError('Supervisor must belong to the same unit')
            if supervisor.role not in ['ADMIN', 'SUPERVISOR']:
                raise ValidationError('Team supervisor must have ADMIN or SUPERVISOR role')
            if not supervisor.is_active:
                raise ValidationError('Selected supervisor is inactive')

        if department and self.cleaned_data.get('number'):
            exists = Team.objects.filter(
                department=department,
                number=self.cleaned_data['number']
            ).exclude(id=self.instance.id if self.instance else None).exists()
            if exists:
                raise ValidationError('A team with this number already exists in this department')

        return cleaned_data

class TeamMemberForm(forms.ModelForm):
    class Meta:
        model = TeamMember
        fields = ['team', 'staff']
        widgets = {
            'team': forms.Select(attrs={'class': 'form-control'}),
            'staff': forms.Select(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['team'].queryset = Team.objects.filter(is_active=True)

        if self.instance and self.instance.team:
            self.fields['staff'].queryset = CustomUser.objects.filter(
                department=self.instance.team.department,
                unit=self.instance.team.unit,
                is_active=True
            )
        else:
            self.fields['staff'].queryset = CustomUser.objects.none()

class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your registered email'
        })
    )

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        user = CustomUser.objects.filter(email__iexact=email, is_active=True).first()
        if not user:
            raise ValidationError("No active user found with this email address.")
        return email

class OTPVerificationForm(forms.Form):
    otp = forms.CharField(
        label='Enter OTP',
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter 6-digit OTP'
        })
    )

    def clean_otp(self):
        otp = self.cleaned_data['otp']
        if not otp.isdigit():
            raise ValidationError("OTP must contain only numbers")
        return otp

class SetNewPasswordForm(forms.Form):
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
                raise ValidationError("Passwords don't match")

            try:
                password_validation.validate_password(password1)
            except ValidationError as error:
                raise ValidationError(error.messages)

        return cleaned_data