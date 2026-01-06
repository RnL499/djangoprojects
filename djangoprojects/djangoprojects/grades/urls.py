from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('register/', views.register, name='register'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('courses/', views.student_courses, name='student_courses'),
    path('courses/available/', views.available_courses, name='available_courses'),
    path('courses/<int:course_id>/enroll/', views.enroll_student_course, name='enroll_student_course'),
    path('enrollment/<int:enrollment_id>/drop/', views.drop_course, name='drop_course'),
    # teacher routes
    path('teacher/courses/', views.teacher_courses, name='teacher_courses'),
    path('teacher/course/create/', views.create_course, name='create_course'),
    path('teacher/course/<int:course_id>/students/', views.teacher_course_students, name='teacher_course_students'),
    # admin-only course creation
    path('admin/course/add/', views.admin_add_course, name='admin_add_course'),
    path('teacher/enrollment/<int:enrollment_id>/grade/', views.update_enrollment_grade, name='update_enrollment_grade'),
    # comments
    path('course/<int:course_id>/comment/add/', views.add_comment, name='add_comment'),
    path('comment/<int:comment_id>/edit/', views.edit_comment, name='edit_comment'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    # admin routes
    path('admin/create-teacher/', views.create_teacher, name='create_teacher'),
]
