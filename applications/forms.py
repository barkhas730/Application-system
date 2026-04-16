from django import forms
from .models import Application, ApplicationType, Attachment


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['title', 'description', 'app_type', 'priority', 'due_date', 'extra_data']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'app_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_app_type'}),
            'priority': forms.Select(attrs={'class': 'form-select', 'id': 'id_priority'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'extra_data': forms.HiddenInput(),
        }
        labels = {
            'title': 'Гарчиг',
            'description': 'Тайлбар',
            'app_type': 'Өргөдлийн төрөл',
            'priority': 'Ач холбогдол',
            'due_date': 'Дуусах огноо',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['app_type'].queryset = ApplicationType.objects.filter(is_active=True)
        self.fields['due_date'].required = False


class AttachmentForm(forms.ModelForm):
    class Meta:
        model = Attachment
        fields = ['file']
        widgets = {
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'file': 'Файл хавсаргах',
        }


class DecisionForm(forms.Form):
    comment = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label='Тайлбар',
        required=True
    )


class ApplicationTypeForm(forms.ModelForm):
    class Meta:
        model = ApplicationType
        # required_fields нь template-д JavaScript field builder-ээр удирдагдана
        # тиймээс энд ороогүй — view-д гараар боловсруулна
        fields = ['name', 'description', 'instructions', 'target_department',
                  'requires_attachment', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            # Маягт дотор харуулах анхааруулга/заавар — хоосон орхивол харуулахгүй
            'instructions': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2,
                'placeholder': 'Жишээ: Хавсралт заавал байх ёстой...',
            }),
            # Өргөдлийг хариуцах хэлтэс — шийдвэрлэгчийн жагсаалтыг шүүхэд ашиглана
            'target_department': forms.Select(attrs={'class': 'form-select'}),
            'requires_attachment': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': 'Нэр',
            'description': 'Тайлбар',
            'instructions': 'Заавар / Анхааруулга',
            'target_department': 'Хариуцах хэлтэс',
            'requires_attachment': 'Хавсралт заавал',
            'is_active': 'Идэвхтэй',
        }
