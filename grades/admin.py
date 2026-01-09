from django.contrib import admin
from .models import Course, Enrollment, Profile, Comment, Teacher


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'teacher')
    search_fields = ('code', 'name', 'teacher__username', 'teacher__profile__full_name')


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'semester', 'midterm_grade', 'final_grade')
    list_filter = ('course', 'semester')
    search_fields = ('student__username', 'course__code', 'course__name')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'is_teacher')
    search_fields = ('user__username', 'full_name')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'created_at', 'updated_at')
    search_fields = ('user__username', 'course__code', 'content')


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user', 'department')
    search_fields = ('user__username', 'department')