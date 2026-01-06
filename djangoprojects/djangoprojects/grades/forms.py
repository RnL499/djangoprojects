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
