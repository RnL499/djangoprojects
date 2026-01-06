from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Course, Enrollment, Profile, Teacher


class FlowTests(TestCase):
    def setUp(self):
        self.client = Client()

        # create teacher user
        self.teacher = User.objects.create_user(username='teacher1', password='pass')
        # profile created by signal
        self.teacher.profile.is_teacher = True
        self.teacher.profile.full_name = 'Teacher One'
        self.teacher.profile.save()
        # create Teacher object
        self.teacher_obj = Teacher.objects.create(user=self.teacher, department='Test Dept')

        # create student user
        self.student = User.objects.create_user(username='student1', password='pass')

        # create a course taught by teacher
        self.course = Course.objects.create(name='Test Course', code='T100', teacher=self.teacher_obj)

    def test_register_and_profile_edit(self):
        # register a new user
        resp = self.client.post(reverse('register'), {
            'username': 'u2', 'password1': 'strongpass123', 'password2': 'strongpass123'
        })
        self.assertEqual(resp.status_code, 302)
        user = User.objects.get(username='u2')

        # login and edit profile
        self.client.login(username='u2', password='strongpass123')
        resp = self.client.post(reverse('edit_profile'), {'full_name': 'New Name'})
        self.assertEqual(resp.status_code, 302)
        user.refresh_from_db()
        self.assertEqual(user.profile.full_name, 'New Name')

    def test_student_enroll_and_drop(self):
        # login as student and enroll via enroll_student_course
        self.client.login(username='student1', password='pass')
        enroll_url = reverse('enroll_student_course', args=[self.course.id])
        resp = self.client.get(enroll_url)
        # enroll view redirects back
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Enrollment.objects.filter(student=self.student, course=self.course).exists())

        # drop via enroll_course POST (admin-like action) - student can also drop themselves
        drop_resp = self.client.post(reverse('enroll_course'), {
            'course_id': str(self.course.id), 'student_id': str(self.student.id), 'action': 'drop'
        })
        self.assertEqual(drop_resp.status_code, 302)
        self.assertFalse(Enrollment.objects.filter(student=self.student, course=self.course).exists())

    def test_teacher_can_grade(self):
        # enroll student
        Enrollment.objects.create(student=self.student, course=self.course)

        # login as teacher
        self.client.login(username='teacher1', password='pass')
        enrollment = Enrollment.objects.get(student=self.student, course=self.course)
        grade_url = reverse('update_enrollment_grade', args=[enrollment.id])
        resp = self.client.post(grade_url, {'midtrem_grade': '75.5', 'final_grade': '82'})
        self.assertEqual(resp.status_code, 302)
        enrollment.refresh_from_db()
        self.assertEqual(float(enrollment.midtrem_grade), 75.5)
        self.assertEqual(float(enrollment.final_grade), 82.0)

    def test_comments_permissions_and_crud(self):
        # student posts a comment
        self.client.login(username='student1', password='pass')
        add_url = reverse('add_comment', args=[self.course.id])
        resp = self.client.post(add_url, {'content': 'Nice course'})
        self.assertEqual(resp.status_code, 302)
        from .models import Comment
        c = Comment.objects.filter(course=self.course, user=self.student).first()
        self.assertIsNotNone(c)
        self.assertEqual(c.content, 'Nice course')

        # student edits own comment
        edit_url = reverse('edit_comment', args=[c.id])
        resp = self.client.post(edit_url, {'content': 'Updated comment'})
        self.assertEqual(resp.status_code, 302)
        c.refresh_from_db()
        self.assertEqual(c.content, 'Updated comment')

        # another user (teacher) cannot edit student's comment
        self.client.login(username='teacher1', password='pass')
        resp = self.client.post(edit_url, {'content': 'Malicious edit'})
        # should redirect and not change
        self.assertEqual(resp.status_code, 302)
        c.refresh_from_db()
        self.assertNotEqual(c.content, 'Malicious edit')

        # teacher (staff check) cannot edit but can delete
        # make teacher a staff user for delete privilege
        self.teacher.is_staff = True
        self.teacher.save()
        delete_url = reverse('delete_comment', args=[c.id])
        resp = self.client.post(delete_url)
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Comment.objects.filter(id=c.id).exists())
from django.test import TestCase

# Create your tests here.
