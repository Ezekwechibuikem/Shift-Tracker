from django.forms import modelformset_factory
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from .models import *
from .forms import *

@login_required
def assign_supervisor(request, staff_id):
    if request.user.role != 'ADMIN':
        raise PermissionDenied
        
    staff_member = get_object_or_404(StaffMember, id=staff_id)
    if request.method == 'POST':
        supervisor_id = request.POST.get('supervisor')
        supervisor = get_object_or_404(CustomUser, id=supervisor_id, role='SUPERVISOR')
        staff_member.supervisor = supervisor
        staff_member.save()
        return redirect('staff_detail', staff_id=staff_id)
        
    supervisors = CustomUser.objects.filter(role='SUPERVISOR')
    return render(request, 'staff/assign_supervisor.html', {
        'staff_member': staff_member,
        'supervisors': supervisors
    })

# @login_required
# def view_team_staff(request):
#     if request.user.role == 'SUPERVISOR':
#         # Get staff members supervised by this supervisor
#         staff_members = StaffMember.objects.filter(
#             supervisor=request.user,
#             is_active=True
#         )
#     elif request.user.role == 'ADMIN':
#         # Admins can see all staff members
#         staff_members = StaffMember.objects.filter(is_active=True)
#     else:
#         # Regular staff can only see their team members
#         staff_members = StaffMember.objects.filter(
#             user__team=request.user.team,
#             is_active=True
#         )
    
#     return render(request, 'staff/team_list.html', {
#         'staff_members': staff_members
#     })


@login_required
def supervisor_dashboard(request):
    if request.user.role != 'SUPERVISOR':
        raise PermissionDenied
        
    staff_members = get_supervisor_staff(request.user)
    teams_data = {}
    
    for team_code, team_name in CustomUser.TEAM_CHOICES:
        team_staff = staff_members.filter(user__team=team_code)
        if team_staff.exists():
            teams_data[team_name] = team_staff
            
    return render(request, 'staff/supervisor_dashboard.html', {
        'teams_data': teams_data
    })


@login_required
def create_weekly_schedule(request):
    DayShiftFormSet = modelformset_factory(
        DayShift, 
        fields=('status',),
        extra=7, 
    )
    
    if request.method == 'POST':
        schedule_form = WeeklyScheduleForm(request.POST)
        if schedule_form.is_valid():
            try:
                with transaction.atomic():
                    # Save the weekly schedule
                    schedule = schedule_form.save(commit=False)
                    schedule.created_by = request.user
                    schedule.save()
                    
                    # Create shifts for each day of the week
                    start_date = schedule.start_date
                    formset = DayShiftFormSet(request.POST)
                    
                    if formset.is_valid():
                        shifts = []
                        for i, form in enumerate(formset):
                            if form.is_valid():
                                shift = form.save(commit=False)
                                shift.schedule = schedule
                                shift.user = schedule.staff_member.user
                                shift.date = start_date + timedelta(days=i)
                                shifts.append(shift)
                        
                        DayShift.objects.bulk_create(shifts)
                        
                        return redirect('schedule_detail', pk=schedule.pk)
            
            except Exception as e:
                # Handle any errors
                schedule_form.add_error(None, f"Error creating schedule: {str(e)}")
    
    else:
        schedule_form = WeeklyScheduleForm()
        formset = DayShiftFormSet(queryset=DayShift.objects.none())
    
    return render(request, 'flow/create_schedule.html', {
        'schedule_form': schedule_form,
        'formset': formset,
    })
