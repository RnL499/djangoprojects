from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=150, blank=True, verbose_name="姓名")
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name="個人頭像")
    is_teacher = models.BooleanField(default=False, verbose_name="是否為教師")

    def __str__(self):
        return self.full_name or self.user.username


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    department = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.department}"


class Course(models.Model):
    name = models.CharField(max_length=100, verbose_name="課程名稱")
    code = models.CharField(max_length=10, unique=True, verbose_name="課程號碼")
    teacher = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='teaching_courses',
        verbose_name="任課教師",
    )

    def __str__(self):
        return f"{self.code} - {self.name}"

    def enrolled_students(self):
        return User.objects.filter(enrollment__course=self)


class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="學生", related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name="課程", related_name='enrollments')
    semester = models.CharField(max_length=20, blank=True, default='', verbose_name="學期")
    # Allow larger numeric ranges for scores (e.g. up to 99999.99 if needed)
    midterm_grade = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="期中成績",
        validators=[MinValueValidator(0)],
    )
    final_grade = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="期末成績",
        validators=[MinValueValidator(0)],
    )

    def __str__(self):
        return f"{self.student.username} 選修 {self.course.code} ({self.semester})"

    class Meta:
        verbose_name = "選課紀錄"
        verbose_name_plural = "選課紀錄管理"


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="使用者", related_name='comments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name="課程", related_name='comments')
    content = models.TextField(verbose_name="留言內容")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} @ {self.course.code}: {self.content[:30]}"


# Helper: compute a student's average grade across all enrollments (both midterm and final)
def _user_avg_grade(self):
    qs = Enrollment.objects.filter(student=self)
    total = 0.0
    count = 0
    for e in qs:
        for g in (e.midterm_grade, e.final_grade):
            if g is not None:
                try:
                    total += float(g)
                    count += 1
                except (TypeError, ValueError):
                    continue
    if count == 0:
        return None
    return round(total / count, 2)


def _user_avg_for_semester(self, semester):
    qs = Enrollment.objects.filter(student=self, semester=semester)
    total = 0.0
    count = 0
    for e in qs:
        for g in (e.midterm_grade, e.final_grade):
            if g is not None:
                try:
                    total += float(g)
                    count += 1
                except (TypeError, ValueError):
                    continue
    if count == 0:
        return None
    return round(total / count, 2)


# Attach helpers to User
User.avg_grade = _user_avg_grade
User.avg_grade_for_semester = _user_avg_for_semester


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        # ensure a profile exists for existing users
        Profile.objects.get_or_create(user=instance)