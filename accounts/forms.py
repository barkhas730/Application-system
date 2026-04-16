from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.utils.safestring import mark_safe
from .models import CustomUser


class ProfileForm(forms.ModelForm):
    # Хэлтэс талбарыг хасав — зөвхөн системийн админ UserEditForm-р өөрчилнө.
    # Хэрэглэгч өөрөө хэлтсээ өөрчлөх эрхгүй.
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone', 'profile_photo']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
        labels = {
            'first_name': 'Нэр',
            'last_name': 'Овог',
            'email': 'Имэйл',
            'phone': 'Утас',
            'profile_photo': 'Профайл зураг',
        }

    def clean_profile_photo(self):
        photo = self.cleaned_data.get('profile_photo')
        if not photo:
            return photo

        # Шинэ файл upload хийгдсэн эсэх шалгана
        if hasattr(photo, 'size'):
            # Хамгийн их хэмжээ: 2МБ
            max_size = 2 * 1024 * 1024
            if photo.size > max_size:
                raise forms.ValidationError('Зурагны хэмжээ 2МБ-аас хэтрэх ёсгүй.')

            # Зөвшөөрөгдсөн формат: JPEG, PNG, GIF
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            content_type = getattr(photo, 'content_type', '')
            if content_type and content_type not in allowed_types:
                raise forms.ValidationError('Зөвхөн JPG, PNG, GIF, WEBP форматтай зураг оруулна уу.')

        return photo


class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        self.fields['old_password'].label = 'Одоогийн нууц үг'
        self.fields['old_password'].help_text = ''
        self.fields['new_password1'].label = 'Шинэ нууц үг'
        self.fields['new_password1'].help_text = mark_safe(
            '<ul class="mb-0 ps-3 mt-1" style="font-size:12px">'
            '<li>Хамгийн багадаа 8 тэмдэгт байх ёстой.</li>'
            '<li>Тоо болон тэмдэгт агуулсан байх ёстой.</li>'
            '</ul>'
        )
        self.fields['new_password2'].label = 'Шинэ нууц үг (давтах)'
        self.fields['new_password2'].help_text = 'Баталгаажуулахын тулд дахин оруулна уу.'


class UserCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label='Нууц үг')

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'phone', 'department', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'username': 'Хэрэглэгчийн нэр',
            'first_name': 'Нэр',
            'last_name': 'Овог',
            'email': 'Имэйл',
            'role': 'Эрх',
            'phone': 'Утас',
            'department': 'Хэлтэс',
            'is_active': 'Идэвхтэй',
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class UserEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'role', 'phone', 'department', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'first_name': 'Нэр',
            'last_name': 'Овог',
            'email': 'Имэйл',
            'role': 'Эрх',
            'phone': 'Утас',
            'department': 'Хэлтэс',
            'is_active': 'Идэвхтэй',
        }
