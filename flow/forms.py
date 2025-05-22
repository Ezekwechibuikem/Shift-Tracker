from django import forms
from django.utils import timezone
from django.utils.safestring import mark_safe
from datetime import timedelta, datetime
from .models import SupervisorAssignment, WeeklySchedule, Holiday, StaffShift
from authentication.models import CustomUser

class SupervisorAssignmentForm(forms.Form):
    staff = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.filter(role='STAFF'),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label='Select Staff Members'
    )

    def save(self, supervisor):
        staff_members = self.cleaned_data['staff']
        assignments = []
        
        for staff_member in staff_members:
            assignment, created = SupervisorAssignment.objects.update_or_create(
                staff=staff_member,
                defaults={'supervisor': supervisor}
            )
            assignments.append(assignment)
        
        return assignments
    
class WeeklyScheduleGenerationForm(forms.Form):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text=mark_safe('<span style="color: red;">Schedule must start on a Sunday</span>')
    )

    def clean_start_date(self):
        start_date = self.cleaned_data['start_date']
        today = timezone.now().date()
      
        if start_date < today:
            raise forms.ValidationError("Cannot create schedule for past dates")

        if start_date.weekday() != 6: 
            raise forms.ValidationError("Schedule must start on a Sunday")

        return start_date

class HolidayForm(forms.ModelForm):
    class Meta:
        model = Holiday
        fields = ['name', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_date(self):
        date = self.cleaned_data['date']
        
        if Holiday.objects.filter(date=date).exists():
            raise forms.ValidationError("A holiday already exists on this date")
        return date

class ManualScheduleEditForm(forms.Form):
    staff = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role='STAFF'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    is_off_day = forms.BooleanField(required=False)

    def __init__(self, *args, schedule=None, **kwargs):
        super().__init__(*args, **kwargs)
        if schedule:
            self.fields['staff'].queryset = CustomUser.objects.filter(
                shifts__schedule=schedule
            ).distinct()

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        is_off_day = cleaned_data.get('is_off_day')

        if date and date.weekday() == 6 and is_off_day:  
            raise forms.ValidationError("Cannot set off day on Sunday")

        return cleaned_data