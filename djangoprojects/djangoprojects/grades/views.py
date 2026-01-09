from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django import forms
from decimal import Decimal, InvalidOperation

from django.contrib.auth.models import User
from .models import Course, Enrollment, Teacher
from .models import Comment
from django.contrib.auth import login
from .forms import UserRegistrationForm, ProfileForm, CommentForm, CreateTeacherForm
from django.contrib.auth.decorators import login_required, user_passes_test


def index(request):
    """Index page with link to main grade system."""
    return render(request, 'index.html')


def main(request):
    """Main page: show students, their enrolled courses and average score."""
    # Redirect based on role: teachers -> teacher dashboard; students -> student dashboard
    if request.user.is_authenticated:
        if _is_teacher(request.user):
            return redirect('teacher_courses')
        if not request.user.is_staff:
            return redirect('student_courses')
    # exclude staff/admin users from the student listing
    students = User.objects.filter(is_staff=False).order_by('username')
    rows = []
    for s in students:
        enrollments = Enrollment.objects.filter(student=s).select_related('course')
        # Use User.avg_grade if present (we attach it in models.py), otherwise compute here
        avg = None
        if hasattr(s, 'avg_grade') and callable(getattr(s, 'avg_grade')):
            try:
                avg = s.avg_grade()
            except Exception:
                avg = None
        rows.append({'student': s, 'enrollments': enrollments, 'avg': avg})

    courses = Course.objects.all().order_by('code')
    return render(request, 'main.html', {'rows': rows, 'courses': courses})


def _is_teacher_or_staff(user):
    if not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    profile = getattr(user, 'profile', None)
    return bool(profile and profile.is_teacher)


def _is_teacher(user):
    if not user.is_authenticated:
        return False
    # prefer group membership; fallback to profile flag for compatibility
    try:
        if user.groups.filter(name='Teacher').exists():
            return True
    except Exception:
        pass
    profile = getattr(user, 'profile', None)
    return bool(profile and profile.is_teacher)


@user_passes_test(_is_teacher)
def teacher_courses(request):
    """List courses taught by the logged-in teacher (or staff)."""
    courses = Course.objects.filter(teacher__user=request.user).order_by('code')
    return render(request, 'teacher_courses.html', {'courses': courses})


@user_passes_test(_is_teacher)
def teacher_course_students(request, course_id):
    """Show students for a course and allow the teacher to enter grades."""
    course = get_object_or_404(Course, id=course_id, teacher__user=request.user)
    enrollments = Enrollment.objects.filter(course=course).select_related('student')
    return render(request, 'teacher_course_students.html', {'course': course, 'enrollments': enrollments})


@user_passes_test(_is_teacher)
def update_enrollment_grade(request, enrollment_id):
    """Handle grade updates for an enrollment (POST)."""
    if request.method != 'POST':
        return redirect('teacher_courses')
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)
    # ensure the current user is the instructor for the course (or staff)
    course_teacher_user = getattr(getattr(enrollment.course, 'teacher', None), 'user', None)
    if not (course_teacher_user == request.user):
        messages.error(request, '沒有權限修改成績')
        return redirect('teacher_courses')

    mid = request.POST.get('midtrem_grade')
    fin = request.POST.get('final_grade')
    # simple validation: allow empty to mean null
    try:
        enrollment.midtrem_grade = Decimal(mid) if mid not in (None, '') else None
    except (InvalidOperation, ValueError):
        messages.error(request, '期中成績格式錯誤')
        return redirect('teacher_course_students', course_id=enrollment.course.id)
    try:
        enrollment.final_grade = Decimal(fin) if fin not in (None, '') else None
    except (InvalidOperation, ValueError):
        messages.error(request, '期末成績格式錯誤')
        return redirect('teacher_course_students', course_id=enrollment.course.id)
    # Disallow negative scores at view level
    if enrollment.midtrem_grade is not None and enrollment.midtrem_grade < 0:
        messages.error(request, '期中成績不得為負數')
        return redirect('teacher_course_students', course_id=enrollment.course.id)
    if enrollment.final_grade is not None and enrollment.final_grade < 0:
        messages.error(request, '期末成績不得為負數')
        return redirect('teacher_course_students', course_id=enrollment.course.id)

    enrollment.save()
    messages.success(request, '成績已更新')
    return redirect('teacher_course_students', course_id=enrollment.course.id)


def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    enrollments = Enrollment.objects.filter(course=course).select_related('student')
    # students not enrolled (for quick enroll form)
    enrolled_student_ids = [e.student.id for e in enrollments]
    other_students = User.objects.exclude(id__in=enrolled_student_ids).filter(is_staff=False).order_by('username')
    comments = Comment.objects.filter(course=course).select_related('user').order_by('-created_at')
    # comment form
    comment_form = CommentForm()
    # pass a safe user_profile to templates to avoid AttributeError for AnonymousUser
    user_profile = getattr(request.user, 'profile', None) if request.user.is_authenticated else None
    return render(request, 'course.html', {
        'course': course,
        'enrollments': enrollments,
        'other_students': other_students,
        'comments': comments,
        'comment_form': comment_form,
        'user_profile': user_profile,
    })

@user_passes_test(_is_teacher)
def add_course(request):
    class CourseForm(forms.ModelForm):
        class Meta:
            model = Course
            fields = ['name', 'code', 'teacher']

    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '課程已新增')
            return redirect('main')
    else:
        form = CourseForm()
    # restrict instructor choices to users marked as teachers
    try:
        form.fields['teacher'].queryset = Teacher.objects.filter(user__profile__is_teacher=True)
    except Exception:
        pass
    return render(request, 'add_course.html', {'form': form})


@user_passes_test(lambda u: u.is_authenticated and u.is_staff)
def admin_add_course(request):
    """Admin-only: create a course and assign a Teacher."""
    class CourseForm(forms.ModelForm):
        class Meta:
            model = Course
            fields = ['name', 'code', 'teacher']

    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '課程已由管理者建立')
            return redirect('main')
    else:
        form = CourseForm()
    try:
        form.fields['teacher'].queryset = Teacher.objects.all()
    except Exception:
        pass
    return render(request, 'add_course.html', {'form': form})


@user_passes_test(_is_teacher)
def create_course(request):
    """Allow a logged-in teacher to create a course assigned to themselves."""
    if request.method == 'POST':
        course_name = request.POST.get('course_name')
        course_code = request.POST.get('course_code')
        try:
            teacher = Teacher.objects.get(user=request.user)
        except Teacher.DoesNotExist:
            messages.error(request, '找不到教師資料')
            return redirect('teacher_courses')
        Course.objects.create(name=course_name, code=course_code, teacher=teacher)
        messages.success(request, '課程已建立')
        return redirect('teacher_courses')

    return render(request, 'create_course.html')


def enroll_course(request):
    """Toggle enroll/drop for a student in a course via POST.

    Expects POST keys: course_id, student_id, action ('enroll'|'drop').
    """
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        student_id = request.POST.get('student_id')
        action = request.POST.get('action')
        course = get_object_or_404(Course, id=course_id)

        # determine student: if student_id provided, use it (admin/teacher action);
        # otherwise require login and use the current user.
        if student_id:
            try:
                student = get_object_or_404(User, id=int(student_id))
            except (ValueError, TypeError):
                messages.error(request, '選取的學生無效')
                return redirect(request.META.get('HTTP_REFERER', reverse('main')))
            # If acting on behalf of someone else, require staff/instructor/teacher
            if not request.user.is_authenticated:
                messages.error(request, '請先登入以加退選課程')
                return redirect('login')
            if student != request.user:
                course_teacher_user = getattr(getattr(course, 'teacher', None), 'user', None)
                if not (
                    request.user.is_staff or request.user == course_teacher_user or
                    (hasattr(request.user, 'profile') and getattr(request.user.profile, 'is_teacher', False))
                ):
                    messages.error(request, '只有授課教師或管理員可以替學生加退選')
                    return redirect(request.META.get('HTTP_REFERER', reverse('main')))
        else:
            if not request.user.is_authenticated:
                messages.error(request, '請先登入以加退選課程')
                return redirect('login')
            student = request.user

        if action == 'enroll':
            Enrollment.objects.get_or_create(student=student, course=course)
            messages.success(request, f"{student.username} 已加入 {course.code}")
        else:
            Enrollment.objects.filter(student=student, course=course).delete()
            messages.success(request, f"{student.username} 已從 {course.code} 退選")

    return redirect(request.META.get('HTTP_REFERER', reverse('main')))


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('main')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def edit_profile(request):
    profile = getattr(request.user, 'profile', None)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, '個人資料已更新')
            return redirect('edit_profile')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'profile_edit.html', {'form': form})


@login_required
def student_courses(request):
    """Show student's enrolled courses with grades and semester average."""
    enrollments = Enrollment.objects.filter(student=request.user).select_related('course')
    semester_list = set(e.semester for e in enrollments if e.semester)
    rows = []
    for e in enrollments:
        rows.append({
            'enrollment': e,
            'midterm': e.midtrem_grade,
            'final': e.final_grade,
            'avg': (float(e.midtrem_grade) + float(e.final_grade)) / 2 if (e.midtrem_grade is not None and e.final_grade is not None) else None,
        })
    
    # semester average
    semester_avgs = {}
    for sem in semester_list:
        semester_avgs[sem] = request.user.avg_grade_for_semester(sem) if hasattr(request.user, 'avg_grade_for_semester') else None
    
    return render(request, 'student_courses.html', {
        'rows': rows,
        'semester_list': sorted(semester_list),
        'semester_avgs': semester_avgs,
    })


@login_required
def drop_course(request, enrollment_id):
    """Drop course for the logged-in student."""
    enrollment = get_object_or_404(Enrollment, id=enrollment_id, student=request.user)
    course = enrollment.course
    enrollment.delete()
    messages.success(request, f'已從 {course.code} 退選')
    return redirect('student_courses')


@login_required
def available_courses(request):
    """Show all courses available to enroll, with search functionality."""
    enrolled_course_ids = Enrollment.objects.filter(student=request.user).values_list('course_id', flat=True)
    available = Course.objects.exclude(id__in=enrolled_course_ids).order_by('code')
    
    # Handle search query
    search_query = request.GET.get('search', '').strip()
    if search_query:
        from django.db.models import Q
        available = available.filter(
            Q(name__icontains=search_query) | Q(code__icontains=search_query)
        )
    
    return render(request, 'available_courses.html', {
        'courses': available,
        'search_query': search_query
    })


@login_required
def enroll_student_course(request, course_id):
    """Student enrolls in a course."""
    course = get_object_or_404(Course, id=course_id)
    enrollment, created = Enrollment.objects.get_or_create(student=request.user, course=course)
    if created:
        messages.success(request, f'已加選 {course.code}')
    else:
        messages.info(request, f'您已經加選 {course.code}')
    return redirect('available_courses')


@login_required
def add_comment(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            c = form.save(commit=False)
            c.user = request.user
            c.course = course
            c.save()
            messages.success(request, '留言已新增')
    return redirect('course_detail', course_id=course_id)


@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.user != request.user:
        messages.error(request, '沒有權限編輯這則留言')
        return redirect('course_detail', course_id=comment.course.id)

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            messages.success(request, '留言已更新')
            return redirect('course_detail', course_id=comment.course.id)
    else:
        form = CommentForm(instance=comment)
    return render(request, 'comment_edit.html', {'form': form, 'comment': comment})


@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.user != request.user and not request.user.is_staff:
        messages.error(request, '沒有權限刪除這則留言')
        return redirect('course_detail', course_id=comment.course.id)
    course_id = comment.course.id
    comment.delete()
    messages.success(request, '留言已刪除')
    return redirect('course_detail', course_id=course_id)


@login_required
def create_teacher(request):
    """Admin-only view to create a new teacher account."""
    if not request.user.is_staff:
        messages.error(request, '只有管理員可以建立教師帳號')
        return redirect('main')
    
    if request.method == 'POST':
        form = CreateTeacherForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '教師帳號建立成功')
            return redirect('create_teacher')
    else:
        form = CreateTeacherForm()
    
    return render(request, 'create_teacher.html', {'form': form})