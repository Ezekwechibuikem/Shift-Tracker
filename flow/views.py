from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.urls import reverse

from authentication.models import CustomUser
from .models import SupervisorAssignment
from .forms import SupervisorAssignmentForm

@login_required
def supervisor_dashboard(request):
    if not request.user.is_admin():
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('authentication:home')
    
    # Get all users with supervisor role, ordered by name
    supervisors = CustomUser.objects.filter(
        role='SUPERVISOR'
    ).order_by('first_name', 'last_name')

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        supervisors = supervisors.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(department__icontains=search_query) |
            Q(unit__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(supervisors, 10)  
    page_number = request.GET.get('page')
    supervisors_page = paginator.get_page(page_number)
    
    context = {
        'supervisors': supervisors_page,
        'search_query': search_query,
    }
    return render(request, 'flow/supervisor_dashboard.html', context)

@login_required
def assign_staff(request, supervisor_id):
    if not request.user.is_admin():
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('authentication:home')
    
    supervisor = get_object_or_404(CustomUser, id=supervisor_id, role='SUPERVISOR')
    
    # Get currently assigned staff with all their information
    assigned_staff = CustomUser.objects.filter(
        assigned_supervisor__supervisor=supervisor
    ).select_related(
        'assigned_supervisor__supervisor'  # This joins the supervisor information
    ).order_by('first_name', 'last_name')
    
    # Get unassigned staff (staff without this supervisor)
    unassigned_staff = CustomUser.objects.filter(
        role='STAFF'
    ).exclude(
        assigned_supervisor__supervisor=supervisor
    ).order_by('first_name', 'last_name')

    if request.method == 'POST':
        form = SupervisorAssignmentForm(request.POST)
        form.fields['staff'].queryset = unassigned_staff
        if form.is_valid():
            try:
                form.save(supervisor=supervisor)
                messages.success(request, f"Staff assigned successfully to {supervisor.first_name}!")
                return redirect('flow:assign_staff', supervisor_id=supervisor_id)
            except Exception as e:
                messages.error(request, f"Error assigning staff: {str(e)}")
    else:
        form = SupervisorAssignmentForm()
        form.fields['staff'].queryset = unassigned_staff
    
    context = {
        'form': form,
        'supervisor': supervisor,
        'assigned_staff': assigned_staff,
        'unassigned_staff': unassigned_staff,
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
    
    # Get staff members in the same team as the supervisor
    staff_members = CustomUser.objects.filter(
        role='STAFF',
        team=request.user.team
    ).order_by('first_name', 'last_name')

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        staff_members = staff_members.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(department__icontains=search_query) |
            Q(unit__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(staff_members, 10)  # 10 staff per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'staff_members': page_obj,
        'search_query': search_query,
        'team_name': request.user.team,
    }
    return render(request, 'flow/team_staff_list.html', context)
