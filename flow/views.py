from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
# from django.urls import reverse
from django.utils import timezone
# from django.db import transaction
from datetime import timedelta
from authentication.models import CustomUser
from .models import SupervisorAssignment, WeeklySchedule, StaffShift, Holiday, Attendance
from .forms import SupervisorAssignmentForm, WeeklyScheduleGenerationForm, HolidayForm, ManualScheduleEditForm
from .utils import ScheduleGenerator
from django.http import JsonResponse
from django.views.decorators.http import require_POST


@login_required
def supervisor_dashboard(request):
    # if not request.user.is_admin():
    #     messages.error(request, "Access denied. Admin privileges required.")
    #     return redirect('authentication:home')
    
    supervisors = CustomUser.objects.filter(
        role='SUPERVISOR'
    ).order_by('first_name', 'last_name')

    search_query = request.GET.get('search', '')
    if search_query:
        supervisors = supervisors.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(department__icontains=search_query) |
            Q(unit__icontains=search_query)
        )

    paginator = Paginator(supervisors, 10)  
    page_number = request.GET.get('page')
    supervisors_page = paginator.get_page(page_number)
    
    context = {
        'supervisors': supervisors_page,
        'search_query': search_query,
    }
    return render(request, 'flow/supervisor_dashboard.html', context)

@login_required
def supervisor_team(request):
    """View for supervisors to see their team"""
    # Check if user is a supervisor
    if not hasattr(request.user, 'is_supervisor') or not request.user.is_supervisor:
        messages.error(request, "Access denied. Supervisor privileges required.")
        return redirect('authentication:home')
    
    # Get the current supervisor 
    supervisor = request.user
    
    # Get all staff members assigned to this supervisor
    supervisor_team = CustomUser.objects.filter(
        assigned_supervisor__supervisor=supervisor,
        ).select_related(
        'assigned_supervisor__supervisor',
        # 'department',
        ).order_by('first_name', 'last_name')
        
    context = {
        'supervisor': supervisor,
        'supervisor_team': supervisor_team,
        # 'total_staff_count': total_staff_count,
        }
    return render(request, 'flow/supervisor_team.html', context)

@require_POST
def clear_message(request):
    if 'gritter_message' in request.session:
        del request.session['gritter_message']
    return JsonResponse({'status': 'ok'})

@login_required
def assign_staff(request, supervisor_id):
    if not request.user.is_admin():
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('authentication:home')
    
    supervisor = get_object_or_404(CustomUser, id=supervisor_id, role='SUPERVISOR')
    
    assigned_staff = CustomUser.objects.filter(
        assigned_supervisor__supervisor=supervisor,
        department=supervisor.department
    ).select_related(
        'assigned_supervisor__supervisor'  
    ).order_by('first_name', 'last_name')
    
    unassigned_staff = CustomUser.objects.filter(
        role='STAFF',
        department=supervisor.department
    ).exclude(
        assigned_supervisor__supervisor=supervisor
    ).order_by('first_name', 'last_name')

    if request.method == 'POST':
        form = SupervisorAssignmentForm(request.POST, supervisor=supervisor)
        if form.is_valid():
            try:
                assignments = form.save(supervisor=supervisor)
                assigned_count = len(assignments)
                messages.success(
                    request, 
                    f"{assigned_count} staff member{'s' if assigned_count != 1 else ''} assigned successfully to {supervisor.first_name}!"
                )
                return redirect('flow:assign_staff', supervisor_id=supervisor_id)
            except Exception as e:
                messages.error(request, f"Error assigning staff: {str(e)}")
                
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = SupervisorAssignmentForm()
        form.fields['staff'].queryset = unassigned_staff
    
    context = {
        'form': form,
        'supervisor': supervisor,
        'assigned_staff': assigned_staff,
        'unassigned_staff': unassigned_staff,
        'supervisor_department': supervisor.department,
    }
    return render(request, 'flow/assign_staff.html', context)

@login_required
def remove_staff_assignment(request, supervisor_id, staff_id):
    if not request.user.is_admin():
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('authentication:home')
    
    supervisor = get_object_or_404(CustomUser, id=supervisor_id, role='SUPERVISOR')
    staff = get_object_or_404(CustomUser, id=staff_id, role='STAFF')
    
    try:
        assignment = SupervisorAssignment.objects.get(supervisor=supervisor, staff=staff)
        assignment.delete()
        messages.success(request, f"{staff.first_name} has been removed from {supervisor.first_name}'s supervision.")
    except SupervisorAssignment.DoesNotExist:
        messages.error(request, "Assignment not found.")
    except Exception as e:
        messages.error(request, f"Error removing assignment: {str(e)}")
    
    return redirect('flow:assign_staff', supervisor_id=supervisor_id)

@login_required
def team_staff_list(request):
    """View for supervisors to see staff in their team"""
    if not request.user.is_staff_member():
        messages.error(request, "Access denied. Supervisor privileges required.")
        return redirect('authentication:home')
    
    staff_members = CustomUser.objects.filter(
        role='STAFF',
        team=request.user.team
    ).order_by('first_name', 'last_name')

    search_query = request.GET.get('search', '')
    if search_query:
        staff_members = staff_members.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(department__icontains=search_query) |
            Q(unit__icontains=search_query)
        )

    paginator = Paginator(staff_members, 10)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'staff_members': page_obj,
        'search_query': search_query,
        'team_name': request.user.team,
    }
    return render(request, 'flow/team_staff_list.html', context)

@login_required
def generate_schedule(request):
    if not request.user.is_supervisor():
        messages.error(request, "Access denied. Supervisor privileges required.")
        return redirect('authentication:home')
    
    if request.method == 'POST':
        form = WeeklyScheduleGenerationForm(request.POST)
        if form.is_valid():
            try:
                start_date = form.cleaned_data['start_date']
                
                existing_schedule = WeeklySchedule.objects.filter(
                    supervisor=request.user,
                    start_date=start_date
                ).first()
                
                if existing_schedule:
                    messages.warning(request, "A schedule already exists for this week.")
                    return redirect('flow:view_schedule', schedule_id=existing_schedule.id)
                
                generator = ScheduleGenerator(request.user, start_date)
                schedule = generator.generate_schedule()

                # Store success message in session for Gritter
                request.session['gritter_message'] = {
                    'title': 'Success!',
                    'message': f'Schedule generated for week of {start_date.strftime("%B %d, %Y")}',
                    'type': 'success'
                }
                
                return redirect('flow:view_schedule', schedule_id=schedule.id)
            
            except Exception as e:
                messages.error(request, f"Error generating schedule: {str(e)}")
    else:
        next_sunday = timezone.now().date()
        while next_sunday.weekday() != 6:
            next_sunday += timedelta(days=1)
        form = WeeklyScheduleGenerationForm(initial={'start_date': next_sunday})
    
    context = {
        'form': form,
    }
    return render(request, 'flow/generate_schedule.html', context)

@login_required
def view_schedule(request, schedule_id=None):
    """View to display weekly schedule"""
    user = request.user
    
    try:
        # Get the schedule
        if schedule_id:
            schedule = get_object_or_404(WeeklySchedule, id=schedule_id)
        else:
            current_date = timezone.now().date()
            schedule = WeeklySchedule.objects.filter(
                start_date__lte=current_date,
                end_date__gte=current_date
            ).first() or WeeklySchedule.objects.filter(
                start_date__gt=current_date
            ).order_by('start_date').first()

        if not schedule:
            if user.is_supervisor():
                messages.info(request, "No schedule found. Generate a new schedule.")
                return redirect('flow:generate_schedule')
            else:
                messages.info(request, "No current schedule found.")
                return redirect('authentication:home')

        # Get all schedules for pagination (for supervisors and admins)
        all_schedules = []
        if user.is_supervisor() or user.is_admin():
            all_schedules = WeeklySchedule.objects.all().order_by('-start_date')

        # Get shifts based on user role
        if user.is_staff_member():
            shifts = StaffShift.objects.filter(
                schedule=schedule,
                staff=user
            ).select_related('staff').order_by('date')
            template_name = 'flow/staff_schedule.html'
        else:
            # For supervisors and admins, get all shifts grouped by team
            shifts = StaffShift.objects.filter(
                schedule=schedule
            ).select_related('staff').order_by('staff__team', 'staff__first_name', 'date')
            template_name = 'flow/supervisor_schedule.html'  

        date_range = [schedule.start_date + timedelta(days=x) for x in range(7)]

        context = {
            'schedule': schedule,
            'all_schedules': all_schedules,  
            'shifts': shifts,
            'date_range': date_range,
            'user_role': user.role,
        }
        
        return render(request, template_name=template_name, context=context)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        messages.error(request, f"Error viewing schedule: {str(e)}")
        return redirect('authentication:home')
    
@login_required
def manage_holidays(request):
    """View for supervisors to manage holidays"""
    if not request.user.is_supervisor():
        messages.error(request, "Access denied. Supervisor privileges required.")
        return redirect('authentication:home')
    
    if request.method == 'POST':
        form = HolidayForm(request.POST)
        if form.is_valid():
            holiday = form.save(commit=False)
            holiday.created_by = request.user
            holiday.save()
            messages.success(request, f"Holiday '{holiday.name}' added successfully!")
            return redirect('flow:manage_holidays')
    else:
        form = HolidayForm()
    
    # Get upcoming holidays
    upcoming_holidays = Holiday.objects.filter(
        date__gte=timezone.now().date()
    ).order_by('date')
    
    context = {
        'form': form,
        'upcoming_holidays': upcoming_holidays,
    }
    return render(request, 'flow/manage_holidays.html', context)

@login_required
def edit_schedule(request, schedule_id):
    """View for supervisors to manually edit schedules"""
    if not request.user.is_supervisor():
        messages.error(request, "Access denied. Supervisor privileges required.")
        return redirect('authentication:home')
    
    schedule = get_object_or_404(WeeklySchedule, id=schedule_id)
    
    if request.method == 'POST':
        form = ManualScheduleEditForm(request.POST, schedule=schedule)
        if form.is_valid():
            try:
                staff = form.cleaned_data['staff']
                date = form.cleaned_data['date']
                is_off_day = form.cleaned_data['is_off_day']
                
                shift = StaffShift.objects.get(
                    schedule=schedule,
                    staff=staff,
                    date=date
                )
                shift.is_off_day = is_off_day
                shift.save()
                
                messages.success(request, "Schedule updated successfully!")
                return redirect('flow:view_schedule', schedule_id=schedule.id)
            
            except StaffShift.DoesNotExist:
                messages.error(request, "Shift not found.")
            except Exception as e:
                messages.error(request, f"Error updating schedule: {str(e)}")
    else:
        form = ManualScheduleEditForm(schedule=schedule)
    
    context = {
        'form': form,
        'schedule': schedule,
    }
    return render(request, 'flow/edit_schedule.html', context)

@login_required
def check_attendance(request):
    """View to handle staff check-in/check-out"""
    now = timezone.now()
    today = now.date()
    
    # Get or create today's attendance record
    attendance, created = Attendance.objects.get_or_create(
        staff=request.user,
        date=today,
        defaults={'time_in': now}
    )
    
    if not created and not attendance.time_out:
        # Staff is checking out
        attendance.time_out = now
        attendance.save()
        messages.success(request, "Check-out successful!")
    elif created:
        messages.success(request, "Check-in successful!")
    else:
        messages.info(request, "You have already completed your shift for today.")
    
    return redirect('flow:view_schedule')