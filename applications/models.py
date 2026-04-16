from django.db import models
from django.conf import settings
from django.utils import timezone


class ApplicationType(models.Model):
    # Өргөдлийг хэн шийдвэрлэхийг тодорхойлох сонголтууд
    TARGET_DEPT_CHOICES = [
        ('', 'Бүх захирлууд'),
        ('__own_dept__', 'Тухайн ажилтны хэлтэс'),
        ('Хүний нөөцийн хэлтэс', 'Хүний нөөцийн хэлтэс'),
        ('Санхүүгийн хэлтэс', 'Санхүүгийн хэлтэс'),
        ('Аж ахуйн хэлтэс', 'Аж ахуйн хэлтэс'),
        ('Мэдээлэл технологийн хэлтэс', 'Мэдээлэл технологийн хэлтэс'),
    ]

    name = models.CharField(max_length=100, verbose_name='Нэр')
    description = models.TextField(blank=True, verbose_name='Тайлбар')
    # Өргөдлийн маягт дотор харуулах заавар / анхааруулга
    instructions = models.TextField(blank=True, verbose_name='Заавар / Анхааруулга')
    # Өргөдлийн маягтад харуулах нэмэлт талбаруудын тодорхойлолт (JSON формат)
    # Формат: [{"key": "purpose", "label": "Зориулалт", "type": "select",
    #            "required": true, "options": ["Банкны зээлд", "Бусад"]}]
    required_fields = models.JSONField(default=list, blank=True, verbose_name='Нэмэлт талбарууд')
    requires_attachment = models.BooleanField(default=False, verbose_name='Хавсралт заавал')
    # Өргөдлийг хариуцах хэлтэс — шийдвэрлэгчийн жагсаалтыг шүүхэд ашиглана
    target_department = models.CharField(
        max_length=100, blank=True, default='',
        choices=TARGET_DEPT_CHOICES,
        verbose_name='Хариуцах хэлтэс'
    )
    is_active = models.BooleanField(default=True, verbose_name='Идэвхтэй')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Өргөдлийн төрөл'
        verbose_name_plural = 'Өргөдлийн төрлүүд'
        ordering = ['name']

    def __str__(self):
        return self.name


class Application(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Ноорог'),
        ('submitted', 'Илгээгдсэн'),
        ('forwarded', 'Дамжуулагдсан'),
        ('approved', 'Зөвшөөрсөн'),
        ('rejected', 'Татгалзсан'),
        ('returned', 'Буцаагдсан'),
        ('cancelled', 'Цуцалсан'),
    ]

    PRIORITY_CHOICES = [
        ('urgent', 'Маш яаралтай'),
        ('high', 'Яаралтай'),
        ('normal', 'Энгийн'),
    ]

    app_number = models.CharField(max_length=20, unique=True, blank=True, verbose_name='Дугаар')
    title = models.CharField(max_length=200, verbose_name='Гарчиг')
    description = models.TextField(verbose_name='Тайлбар')
    app_type = models.ForeignKey(ApplicationType, on_delete=models.PROTECT, verbose_name='Төрөл')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications', verbose_name='Өргөдлийн эзэн')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='Төлөв')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal', verbose_name='Ач холбогдол')
    due_date = models.DateField(null=True, blank=True, verbose_name='Дуусах огноо')
    extra_data = models.JSONField(default=dict, blank=True, verbose_name='Нэмэлт мэдээлэл')
    return_count = models.IntegerField(default=0, verbose_name='Буцаалтын тоо')
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_apps',
        verbose_name='Хариуцах захирал'
    )
    is_draft = models.BooleanField(default=True, verbose_name='Ноорог эсэх')
    is_cancelled = models.BooleanField(default=False, verbose_name='Цуцалсан эсэх')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Үүсгэсэн')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Шинэчлэгдсэн')
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name='Илгээсэн')
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name='Хаагдсан')

    class Meta:
        verbose_name = 'Өргөдөл'
        verbose_name_plural = 'Өргөдлүүд'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.app_number} - {self.title}"

    def _generate_app_number(self):
        """
        Өргөдлийн дугаар үүсгэх. transaction.atomic() дотор дуудна.
        Формат: APP-ЖЖЖЖ-ДДД (жишээ: APP-2025-001)
        """
        year = timezone.now().year
        last = (
            Application.objects
            .filter(app_number__startswith=f'APP-{year}-')
            .order_by('app_number')
            .last()
        )
        if last:
            try:
                num = int(last.app_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                num = 1
        else:
            num = 1
        return f'APP-{year}-{num:03d}'

    def save(self, *args, **kwargs):
        from django.db import transaction, IntegrityError

        if not self.app_number:
            # transaction.atomic() + давталт: хэрэв 2 хүн нэгэн зэрэг дугаар
            # авахыг оролдвол unique constraint алдааг барьж дахин оролдоно.
            max_retries = 5
            for attempt in range(max_retries):
                with transaction.atomic():
                    self.app_number = self._generate_app_number()
                    try:
                        super().save(*args, **kwargs)
                        return  # Амжилттай хадгалагдсан
                    except IntegrityError:
                        # Давхар дугаар үүссэн тул дахин оролдоно
                        self.app_number = ''
                        if attempt == max_retries - 1:
                            raise  # Бүх оролдлого дууссан
        else:
            super().save(*args, **kwargs)

    @property
    def status_badge(self):
        badges = {
            'draft': 'secondary',
            'submitted': 'primary',
            'forwarded': 'info',
            'approved': 'success',
            'rejected': 'danger',
            'returned': 'warning',
            'cancelled': 'dark',
        }
        return badges.get(self.status, 'secondary')

    @property
    def priority_badge(self):
        badges = {
            'urgent': 'danger',
            'high': 'warning',
            'normal': 'primary',
        }
        return badges.get(self.priority, 'secondary')

    @property
    def can_edit(self):
        return self.status in ('draft', 'returned')

    @property
    def can_cancel(self):
        return self.status in ('draft', 'submitted', 'returned')

    @property
    def can_submit(self):
        return self.status in ('draft', 'returned')

    @property
    def is_due_overdue(self):
        if self.due_date:
            return self.due_date < timezone.now().date()
        return False


class Attachment(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='attachments', verbose_name='Өргөдөл')
    file = models.FileField(upload_to='attachments/%Y/%m/', verbose_name='Файл')
    file_name = models.CharField(max_length=255, verbose_name='Файлын нэр')
    file_size = models.IntegerField(default=0, verbose_name='Файлын хэмжээ')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Оруулсан огноо')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='Оруулсан хүн')

    class Meta:
        verbose_name = 'Хавсралт'
        verbose_name_plural = 'Хавсралтууд'

    def __str__(self):
        return self.file_name

    @property
    def file_size_display(self):
        size = self.file_size
        if size < 1024:
            return f'{size} B'
        elif size < 1024 * 1024:
            return f'{size / 1024:.1f} KB'
        else:
            return f'{size / (1024 * 1024):.1f} MB'


class DecisionHistory(models.Model):
    ACTION_CHOICES = [
        ('submit', 'Илгээсэн'),
        ('forward', 'Дамжуулсан'),
        ('return', 'Буцаасан'),
        ('approve', 'Зөвшөөрсөн'),
        ('reject', 'Татгалзсан'),
        ('cancel', 'Цуцалсан'),
        ('resubmit', 'Дахин илгээсэн'),
    ]

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='history', verbose_name='Өргөдөл')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='Үйлдэл хийсэн хүн')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name='Үйлдэл')
    comment = models.TextField(blank=True, verbose_name='Тайлбар')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Огноо')

    class Meta:
        verbose_name = 'Шийдвэрийн түүх'
        verbose_name_plural = 'Шийдвэрийн түүхүүд'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.application.app_number} - {self.get_action_display()}"
