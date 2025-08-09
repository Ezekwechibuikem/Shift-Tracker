from datetime import timedelta
from django.db import transaction
import random
from .models import WeeklySchedule, StaffShift
from authentication.models import CustomUser

class ScheduleGenerator:
    def __init__(self, supervisor, start_date):
        self.supervisor = supervisor
        self.start_date = start_date
        self.end_date = start_date + timedelta(days=6)

    def assign_off_days_evenly(self, staff_members):
        """
        Assign one off day per staff member from Monday to Saturday,
        ensuring no more than 2 staff members are off on any given day.
        """
        available_days = list(range(0, 6))  # Monday(0) to Saturday(5)
        assignments = {}
        day_counts = {day: 0 for day in available_days}  # Track how many staff off each day
        
        # Shuffle staff list for random assignment
        staff_list = list(staff_members)
        random.shuffle(staff_list)
        
        # First pass: assign off days while respecting the 2-person limit
        for staff in staff_list:
            # Find days with the least number of people off (under the limit of 2)
            available_days_under_limit = [day for day in available_days if day_counts[day] < 2]
            
            if available_days_under_limit:
                # Choose the day with the fewest people off
                chosen_day = min(available_days_under_limit, key=lambda d: day_counts[d])
                assignments[staff.id] = chosen_day
                day_counts[chosen_day] += 1
            else:
                # If all days have 2 people off, assign to a random day anyway
                # This handles cases where there are more than 12 staff members
                chosen_day = random.choice(available_days)
                assignments[staff.id] = chosen_day
                day_counts[chosen_day] += 1
        
        return assignments

    @transaction.atomic
    def generate_schedule(self):
        schedule = WeeklySchedule.objects.create(
            supervisor=self.supervisor,
            start_date=self.start_date,
            end_date=self.end_date,
            is_published=True
        )

        # Get all staff members under this supervisor in the same department
        staff_members = CustomUser.objects.filter(
            assigned_supervisor__supervisor=self.supervisor,
            role='STAFF',
            department=self.supervisor.department  # Only staff in same department
        ).order_by('first_name')

        # Assign off days for all staff members evenly
        staff_off_days = self.assign_off_days_evenly(staff_members)

        # Generate shifts for the week (Monday to Sunday)
        for current_date in (self.start_date + timedelta(n) for n in range(7)):
            day_of_week = current_date.weekday()
            
            # Create shifts for all staff
            for staff in staff_members:
                is_off = False
                
                # Check if it's this staff member's off day
                if day_of_week != 6:  # Not Sunday (Sunday is mandatory workday)
                    staff_off_day = staff_off_days.get(staff.id)
                    is_off = (day_of_week == staff_off_day)
                # If it's Sunday (day_of_week == 6), is_off remains False
                
                StaffShift.objects.create(
                    schedule=schedule,
                    staff=staff,
                    date=current_date,
                    is_off_day=is_off
                )

        return schedule