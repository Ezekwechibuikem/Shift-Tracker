from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from .models import StaffSupervisor
from .forms import SupervisorAssignmentForm
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
def staff_list(request):
    if not request.user.is_admin():
        raise PermissionDenied
    
    staff_members = User.objects.filter(role='STAFF')
    supervisors = User.objects.filter(role='SUPERVISOR')
    
    return render(request, 'flow/assign_staff_list.html', {
        'staff_members': staff_members,
        'supervisors': supervisors,
    })

@login_required
def assign_supervisor(request, staff_id):
    if not request.user.is_admin():
        raise PermissionDenied
    
    staff = get_object_or_404(User, id=staff_id, role='STAFF')
    supervisor_assignment, created = StaffSupervisor.objects.get_or_create(
        staff=staff,
        defaults={'assigned_by': request.user}
    )
    
    if request.method == 'POST':
        form = SupervisorAssignmentForm(request.POST, instance=supervisor_assignment)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.assigned_by = request.user
            assignment.save()
            messages.success(request, f'Supervisor assigned to {staff.get_full_name()}')
            return redirect('flow:assign_staff_list')
    else:
        form = SupervisorAssignmentForm(instance=supervisor_assignment)
    
    return render(request, 'flow/assign_supervisor.html', {
        'form': form,
        'staff': staff,
    })

@login_required
def supervision_overview(request):
    if not request.user.is_admin():
        raise PermissionDenied
    
    assignments = StaffSupervisor.objects.select_related('staff', 'supervisor', 'assigned_by').all()
    return render(request, 'flow/supervision_overview.html', {
        'assignments': assignments,
    })