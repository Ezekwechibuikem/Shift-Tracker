from django import forms
from authentication.models import CustomUser
from .models import SupervisorAssignment

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