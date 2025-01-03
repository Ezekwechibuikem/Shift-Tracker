from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from .models import CustomUser

def create_default_groups():
    # Get CustomUser content type
    content_type = ContentType.objects.get_for_model(CustomUser)
    
    admin_group, _ = Group.objects.get_or_create(name='Admin')
    admin_permissions = Permission.objects.all()
    admin_group.permissions.set(admin_permissions)

    supervisor_group, _ = Group.objects.get_or_create(name='Supervisor')
    supervisor_permissions = Permission.objects.filter(
        content_type=content_type,
        codename__in=['can_view_team_users', 'can_manage_team_shifts', 'can_approve_team_leaves']
    )
    supervisor_group.permissions.set(supervisor_permissions)

    staff_group, _ = Group.objects.get_or_create(name='Staff')
    staff_permissions = Permission.objects.filter(
        content_type=content_type,
        codename__in=['can_view_own_profile', 'can_request_leave', 'can_view_own_shifts']
    )
    staff_group.permissions.set(staff_permissions)

