from django.core.management.base import BaseCommand
from authentication.groups import create_default_groups

class Command(BaseCommand):
    help = 'Create default groups and permissions'

    def handle(self, *args, **options):
        create_default_groups()
        self.stdout.write(self.style.SUCCESS('Successfully created groups and permissions'))