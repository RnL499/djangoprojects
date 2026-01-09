from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from grades.models import Teacher

class Command(BaseCommand):
    help = 'Create Teacher entries for users whose profile.is_teacher is True and missing Teacher object.'

    def handle(self, *args, **options):
        created = 0
        for u in User.objects.filter(is_active=True):
            profile = getattr(u, 'profile', None)
            if profile and getattr(profile, 'is_teacher', False):
                if not hasattr(u, 'teacher_profile') and not Teacher.objects.filter(user=u).exists():
                    Teacher.objects.create(user=u, department='')
                    created += 1
                    self.stdout.write(self.style.SUCCESS(f'Created Teacher for user {u.username}'))
                # ensure group membership
                from django.contrib.auth.models import Group
                teacher_group, _ = Group.objects.get_or_create(name='Teacher')
                if not u.groups.filter(name='Teacher').exists():
                    u.groups.add(teacher_group)
                    self.stdout.write(self.style.SUCCESS(f'Added {u.username} to Teacher group'))
        if created == 0:
            self.stdout.write('No Teacher objects needed creating.')
        else:
            self.stdout.write(self.style.SUCCESS(f'Created {created} Teacher objects.'))
