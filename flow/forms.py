from django import forms
from .models import StaffSupervisor
from django.contrib.auth import get_user_model

User = get_user_model()

class SupervisorAssignmentForm(forms.ModelForm):
    class Meta:
        model = StaffSupervisor
        fields = ['supervisor']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['supervisor'].queryset = User.objects.filter(role='SUPERVISOR')
        self.fields['supervisor'].label_from_instance = lambda obj: obj.get_full_name()