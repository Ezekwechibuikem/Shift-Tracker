from django import forms
from .models import StaffMember, WeeklySchedule, DayShift, LeaveRequest, DailyReport, ReportComment
from datetime import datetime, timedelta

class StaffMemberForm(forms.ModelForm):
    class Meta:
        model = StaffMember
        fields = ['user', 'is_active', 'supervisor']
        widgets = {
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class WeeklyScheduleForm(forms.ModelForm):
    class Meta:
        model = WeeklySchedule
        fields = ['staff_member', 'start_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
        
    def clean_start_date(self):
        start_date = self.cleaned_data['start_date']
        if start_date.weekday() !=6:
            raise forms.ValidationError("Schedule must start on a Sunday")
        return start_date

class DayShiftForm(forms.ModelForm):
    class Meta:
        model = DayShift
        fields = ['schedule', 'user', 'date', 'status']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
        
        
    #     class DayShiftFormSet(forms.BaseModelFormSet):
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     for form in self.forms:
    #         form.fields['status'].widget.attrs.update({'class': 'form-select'})
        

class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['start_date', 'end_date', 'reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("End date must be after start date.")
        
        return cleaned_data

class LeaveRequestReviewForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class DailyReportForm(forms.ModelForm):
    class Meta:
        model = DailyReport
        fields = ['date', 'report_text']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'report_text': forms.Textarea(attrs={
                'rows': 6, 
                'class': 'form-control',
                'placeholder': 'Enter your daily report here...'
            }),
        }

class ReportCommentForm(forms.ModelForm):
    class Meta:
        model = ReportComment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control',
                'placeholder': 'Enter your comment here...'
            }),
        }