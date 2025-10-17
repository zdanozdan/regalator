from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from wms.models import UserProfile


class Command(BaseCommand):
    help = 'Reset password_changed status for users (useful for testing first-time login flow)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username to reset (if not provided, resets all users)',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Reset password status for all users',
        )

    def handle(self, *args, **options):
        username = options.get('username')
        reset_all = options.get('all')

        if username:
            try:
                user = User.objects.get(username=username)
                profile, created = UserProfile.objects.get_or_create(user=user)
                profile.password_changed = False
                profile.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Reset password status for user: {username}')
                )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User "{username}" does not exist')
                )
        elif reset_all:
            updated_count = 0
            for user in User.objects.all():
                profile, created = UserProfile.objects.get_or_create(user=user)
                profile.password_changed = False
                profile.save()
                updated_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(f'Reset password status for {updated_count} users')
            )
        else:
            self.stdout.write(
                self.style.ERROR('Please specify --username or --all')
            )
