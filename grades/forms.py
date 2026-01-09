from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, Teacher

from .models import Comment


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('content',)
        widgets = {
            'content': forms.Textarea(attrs={'rows':3, 'class':'form-control', 'placeholder':'在此留言...'}),
        }


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('full_name', 'avatar')


class StudentRegistrationForm(UserRegistrationForm):
    """Registration form for students; ensure profile.is_teacher=False on save."""
    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            # ensure profile exists and is marked as student
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.is_teacher = False
            profile.save()
        return user


class GradeForm(forms.ModelForm):
    class Meta:
        model = None  # set in __init__ to Enrollment
        fields = ('midterm_grade', 'final_grade')

    midterm_grade = forms.DecimalField(max_digits=7, decimal_places=2, required=False, min_value=0, label='期中')
    final_grade = forms.DecimalField(max_digits=7, decimal_places=2, required=False, min_value=0, label='期末')

    def __init__(self, *args, **kwargs):
        # Accept an Enrollment instance via 'instance'
        self.instance = kwargs.get('instance', None)
        # dynamically set Meta.model to Enrollment to satisfy ModelForm behavior
        from .models import Enrollment
        self.__class__.Meta.model = Enrollment
        super().__init__(*args, **kwargs)
        if self.instance is not None:
            self.fields['midterm_grade'].initial = getattr(self.instance, 'midterm_grade', None)
            self.fields['final_grade'].initial = getattr(self.instance, 'final_grade', None)

    def __init__(self, *args, **kwargs):
        # Accept an Enrollment instance via 'instance'
        self.instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)
        if self.instance is not None:
            self.fields['midterm_grade'].initial = getattr(self.instance, 'midterm_grade', None)
            self.fields['final_grade'].initial = getattr(self.instance, 'final_grade', None)

    def save(self, commit=True):
        if self.instance is None:
            raise ValueError('GradeForm requires an Enrollment instance via ``instance`` kwarg')
        self.instance.midterm_grade = self.cleaned_data.get('midterm_grade')
        self.instance.final_grade = self.cleaned_data.get('final_grade')
        if commit:
            self.instance.save()
        return self.instance


class CreateTeacherForm(UserCreationForm):
    """Form for admin to create a new teacher account."""
    email = forms.EmailField(required=False)
    full_name = forms.CharField(max_length=100, required=False, label='教師姓名')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            # Teachers are not staff by default; admin manages them
            user.save()
            # Create or update profile with is_teacher=True
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.is_teacher = True
            profile.full_name = self.cleaned_data.get('full_name', '')
            profile.save()
            # Ensure 'Teacher' group exists and add the user to it
            teacher_group, _ = Group.objects.get_or_create(name='Teacher')
            user.groups.add(teacher_group)
            # Create Teacher model instance
            Teacher.objects.get_or_create(user=user, defaults={'department': ''})
        return user
