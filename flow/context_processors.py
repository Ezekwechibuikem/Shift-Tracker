from django.utils import timezone
from .models import WeeklySchedule

def new_schedules_count(request):
    """ Context processor to count new weekly schedules created today."""
    if request.user.is_authenticated:
        count = WeeklySchedule.objects.filter(
            created_at__date=timezone.now().date()
        ).count()
        return {'new_schedules_count': count}
    return {'new_schedules_count': 0}