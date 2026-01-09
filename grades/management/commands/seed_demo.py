from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import IntegrityError

from grades.models import Course, Enrollment, Profile, Teacher


class Command(BaseCommand):
    help = 'Seed demo data: admin, teacher, student, 3 courses, enroll student'

    def handle(self, *args, **options):
        created = []
        # create admin
        admin_username = 'admin'
        admin_email = 'admin@example.com'
        admin_password = 'adminpass'
        admin, a_created = User.objects.get_or_create(username=admin_username, defaults={'email': admin_email})
        if a_created:
            admin.is_staff = True
            admin.is_superuser = True
            admin.set_password(admin_password)
            admin.save()
            created.append('admin user')

        # create teacher
        teacher_username = 'teacher1'
        teacher_email = 'teacher1@example.com'
        teacher_password = 'teacherpass'
        teacher, t_created = User.objects.get_or_create(username=teacher_username, defaults={'email': teacher_email})
        if t_created:
            teacher.set_password(teacher_password)
            teacher.save()
            created.append('teacher1 user')
        # ensure profile and mark as teacher (do NOT set is_staff)
        Profile.objects.get_or_create(user=teacher, defaults={'full_name': '教師 一', 'is_teacher': True})
        p = getattr(teacher, 'profile', None)
        if p and not p.is_teacher:
            p.is_teacher = True
            p.save()
        # create Teacher object linked to the user
        teacher_obj, t_obj_created = Teacher.objects.get_or_create(user=teacher, defaults={'department': 'General'})

        # create student
        student_username = 'student1'
        student_email = 'student1@example.com'
        student_password = 'studentpass'
        student, s_created = User.objects.get_or_create(username=student_username, defaults={'email': student_email})
        if s_created:
            student.set_password(student_password)
            student.save()
            created.append('student1 user')
        Profile.objects.get_or_create(user=student, defaults={'full_name': '學生 一', 'is_teacher': False})

        # create three courses
        courses_data = [
            ('CSE101', 'Computer Science 101'),
            ('MATH101', 'Mathematics 101'),
            ('ENG101', 'English 101'),
        ]
        courses = []
        for code, name in courses_data:
            course, c_created = Course.objects.get_or_create(code=code, defaults={'name': name, 'teacher': teacher})
            if c_created:
                created.append(f'course {code}')
            else:
                # ensure teacher set
                if course.teacher != teacher:
                    course.teacher = teacher
                    course.save()
            courses.append(course)

        # enroll student in the three courses with sample grades
        for course in courses:
            en, e_created = Enrollment.objects.get_or_create(student=student, course=course, defaults={'semester': '2026S', 'midterm_grade': 85.0, 'final_grade': 90.0})
            if e_created:
                created.append(f'enrollment {student.username} -> {course.code}')

        self.stdout.write(self.style.SUCCESS('Demo seed complete.'))
        if created:
            for item in created:
                self.stdout.write(f'  - {item}')
        self.stdout.write('Accounts:')
        self.stdout.write(f'  admin / {admin_password}')
        self.stdout.write(f'  teacher1 / {teacher_password}')
        self.stdout.write(f'  student1 / {student_password}')
