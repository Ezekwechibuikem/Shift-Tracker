from datetime import timedelta
from django.db import transaction
import random

class ScheduleGenerator:
    def __init__(self, supervisor, start_date):
        self.supervisor = supervisor
        self.start_date = start_date
        self.end_date = start_date + timedelta(days=6)

    @transaction.atomic
    def generate_schedule(self):
        from .models import WeeklySchedule, StaffShift
        
        # Create the weekly schedule
        schedule = WeeklySchedule.objects.create(
            supervisor=self.supervisor,
            start_date=self.start_date,
            end_date=self.end_date
        )

        # Get all staff members under this supervisor
        staff_members = self.supervisor.supervised_staff.all()
        
        # Group staff by teams
        teams = {}
        for staff in staff_members:
            if staff.team not in teams:
                teams[staff.team] = []
            teams[staff.team].append(staff)

        # Generate shifts for each day
        current_date = self.start_date
        while current_date <= self.end_date:
            if current_date.weekday() != 6:  # Not Sunday
                # For each team, assign one staff member to be off
                for team, members in teams.items():
                    # Randomly select one staff member to be off
                    off_staff = random.choice(members)
                    
                    # Create shifts for both team members
                    for staff in members:
                        StaffShift.objects.create(
                            schedule=schedule,
                            staff=staff,
                            date=current_date,
                            is_off_day=(staff == off_staff)
                        )
            else:
                # Sunday - everyone works
                for team, members in teams.items():
                    for staff in members:
                        StaffShift.objects.create(
                            schedule=schedule,
                            staff=staff,
                            date=current_date,
                            is_off_day=False
                        )
            
            current_date += timedelta(days=1)

        return schedule