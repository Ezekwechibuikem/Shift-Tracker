from datetime import timedelta
from django.db import transaction
import random
from .models import WeeklySchedule, StaffShift

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
        day_counts = {day: 0 for day in available_days}

        staff_list = list(staff_members)
        random.shuffle(staff_list)

        for staff in staff_list:
            available_days_under_limit = [day for day in available_days if day_counts[day] < 2]
            if available_days_under_limit:
                chosen_day = min(available_days_under_limit, key=lambda d: day_counts[d])
            else:
                chosen_day = random.choice(available_days)
            assignments[staff.id] = chosen_day
            day_counts[chosen_day] += 1

        return assignments

    @transaction.atomic
    def generate_schedule_for_staff(self, staff_members):
        """
        Generate schedule using already-fetched staff members.
        """
        schedule = WeeklySchedule.objects.create(
            supervisor=self.supervisor,
            start_date=self.start_date,
            end_date=self.end_date,
            is_published=True
        )

        # Assign off days
        staff_off_days = self.assign_off_days_evenly(staff_members)

        # Generate shifts for the week (Monday to Sunday)
        for current_date in (self.start_date + timedelta(n) for n in range(7)):
            day_of_week = current_date.weekday()

            for staff in staff_members:
                is_off = False
                if day_of_week != 6:  # Not Sunday
                    staff_off_day = staff_off_days.get(staff.id)
                    is_off = (day_of_week == staff_off_day)

                StaffShift.objects.create(
                    schedule=schedule,
                    staff=staff,
                    date=current_date,
                    is_off_day=is_off
                )

        return schedule
