from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import requests 
import datetime
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
from datetime import date, timedelta


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
    # Check if user is supervisor
    if not request.user.is_supervisor():
        # Non-supervisor - redirect to home page
        messages.error(request, "Access denied. Supervisor privileges required.")
        return redirect('authentication:home')
    
    # Check if this is the initial request (supervisor hasn't checked holidays yet)
    if not request.GET.get('holidays_checked') and not request.session.get('holidays_checked'):
        # Supervisor - redirect to holiday check page first
        return redirect('flow:check_holidays')
    
    # Clear the session flag after using it
    if request.session.get('holidays_checked'):
        del request.session['holidays_checked']
    
    if request.method == 'POST':
        form = WeeklyScheduleGenerationForm(request.POST)
        if form.is_valid():
            try:
                start_date = form.cleaned_data['start_date']
                
                # Check if start_date is a Monday
                if start_date.weekday() != 0:
                    messages.error(request, "Schedule must start on a Monday.")
                    return render(request, 'flow/generate_schedule.html', {'form': form})
                
                existing_schedule = WeeklySchedule.objects.filter(
                    supervisor=request.user,
                    start_date=start_date
                ).first()
                
                if existing_schedule:
                    messages.warning(request, "A schedule already exists for this week.")
                    return redirect('flow:view_schedule', schedule_id=existing_schedule.id)
                
                # Check if supervisor has staff in their department
                staff_count = CustomUser.objects.filter(
                    assigned_supervisor__supervisor=request.user,
                    role='STAFF',
                    department=request.user.department
                ).count()
                
                if staff_count == 0:
                    messages.error(request, "No staff members found in your department to schedule.")
                    return render(request, 'flow/generate_schedule.html', {'form': form})
                
                generator = ScheduleGenerator(request.user, start_date)
                schedule = generator.generate_schedule()

                # Store success message in session for Gritter
                request.session['gritter_message'] = {
                    'title': 'Success!',
                    'message': f'Schedule generated for week of {start_date.strftime("%B %d, %Y")} for {staff_count} staff members in {request.user.department} department',
                    'type': 'success'
                }
                
                return redirect('flow:view_schedule', schedule_id=schedule.id)
            
            except Exception as e:
                messages.error(request, f"Error generating schedule: {str(e)}")
    else:
        # Find the next Monday as the default start date
        next_monday = timezone.now().date()
        while next_monday.weekday() != 0:
            next_monday += timedelta(days=1)
        form = WeeklyScheduleGenerationForm(initial={'start_date': next_monday})
    
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
def check_public_holidays(request):
    if not request.user.is_supervisor():
        messages.error(request, "Access denied. Supervisor privileges required.")
        return redirect('authentication:home')

    today = timezone.now().date()
    days_until_sunday = (6 - today.weekday()) % 7
    upcoming_sunday = today + timedelta(days=days_until_sunday)
    week_end = upcoming_sunday + timedelta(days=6)
   
    year = upcoming_sunday.year
    url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/NG"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        holidays_data = response.json()
    except requests.RequestException:
        messages.error(request, "Error fetching public holidays. Please try again.")
        return render(request, 'flow/check_holidays.html')

    week_holidays = [
        h for h in holidays_data
        if upcoming_sunday <= datetime.date.fromisoformat(h['date']) <= week_end
    ]

    if week_holidays:
        saved_count = 0
        for h in week_holidays:
            date_obj = datetime.date.fromisoformat(h['date'])
            holiday_obj, created = Holiday.objects.get_or_create(
                name=h['localName'],
                date=date_obj,
                defaults={'created_by': request.user}
            )
            # UPDATE: Always set created_by if it's None
            if holiday_obj.created_by is None:
                holiday_obj.created_by = request.user
                holiday_obj.save()
            
            if created:
                saved_count += 1
        messages.success(request, f"Found and saved {saved_count} holiday(s) for the week.")
    else:
        # FIXED: Handle "No holiday" case properly
        holiday_obj, created = Holiday.objects.get_or_create(
            name="No holiday",
            date=upcoming_sunday,
            defaults={'created_by': request.user}
        )
        
        # If the holiday already existed but has no created_by, update it
        if holiday_obj.created_by is None:
            holiday_obj.created_by = request.user
            holiday_obj.save()
            
        messages.info(request, "No public holidays found for that week.")

    # Get all holidays for display
    all_holidays = Holiday.objects.all().order_by('date')
    
    # Check if this request came from generate_schedule redirect
    # Set session flag to indicate holidays have been checked
    request.session['holidays_checked'] = True
    
    context = {
        'week_holidays': week_holidays,
        'upcoming_sunday': upcoming_sunday,
        'week_end': week_end,
        'all_holidays': all_holidays,
        'show_continue_to_schedule': True,  # Flag to show "Continue to Schedule" button
    }
    
    return render(request, 'flow/check_holidays.html', context)
    
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