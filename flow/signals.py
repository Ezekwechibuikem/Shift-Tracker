# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from authentication.models import CustomUser
# from .models import StaffMember

# @receiver(post_save, sender=CustomUser)
# def create_staff_member(sender, instance, created, **kwargs):
#     if created and instance.role == 'STAFF':
#         # Find a supervisor in the same team
#         supervisor = CustomUser.objects.filter(
#             role='SUPERVISOR',
#             team=instance.team
#         ).first()
        
#         if supervisor:
#             StaffMember.objects.create(
#                 user=instance,
#                 supervisor=supervisor
#             )

# @receiver(post_save, sender=CustomUser)
# def update_staff_member(sender, instance, **kwargs):
#     if hasattr(instance, 'staff_profile'):
#         staff_profile = instance.staff_profile
#         if instance.role != 'STAFF':
#             # If user is no longer a staff member, deactivate their profile
#             staff_profile.is_active = False
#             staff_profile.save()