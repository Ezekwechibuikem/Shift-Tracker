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

    def assign_off_days(self, team_members):
        """Assign one off day per staff member in a team per week, but one staff member within the team must be present each day."""
        available_days = list(range(0, 6))  # Monday(0) to Saturday(5)
        assignments = {}
        
        # Randomly assign different off days to each team member
        for staff in team_members:
            if available_days:
                off_day = random.choice(available_days)
                available_days.remove(off_day)
                assignments[staff.id] = off_day
            
        return assignments

    @transaction.atomic
    def generate_schedule(self):
        schedule = WeeklySchedule.objects.create(
            supervisor=self.supervisor,
            start_date=self.start_date,
            end_date=self.end_date,
            is_published=True
        )

        # Get all staff members under this supervisor
        staff_members = CustomUser.objects.filter(
            assigned_supervisor__supervisor=self.supervisor,
            role='STAFF'
        ).order_by('team', 'first_name')

        # Group staff by teams
        teams = {}
        for staff in staff_members:
            if staff.team not in teams:
                teams[staff.team] = []
            teams[staff.team].append(staff)

        # Assign off days for each team
        team_off_days = {}
        for team_name, team_members in teams.items():
            team_off_days[team_name] = self.assign_off_days(team_members)

        # Generate shifts for the week
        for current_date in (self.start_date + timedelta(n) for n in range(7)):
            day_of_week = current_date.weekday()
            
            # Create shifts for all staff
            for team_name, team_members in teams.items():
                for staff in team_members:
                    is_off = False
                    
                    # Check if it's this staff member's off day
                    if day_of_week != 6:  # Not Sunday
                        staff_off_day = team_off_days[team_name].get(staff.id)
                        is_off = (day_of_week == staff_off_day)
                    
                    StaffShift.objects.create(
                        schedule=schedule,
                        staff=staff,
                        date=current_date,
                        is_off_day=is_off
                    )

        return schedule