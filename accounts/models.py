from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('employee', 'Ажилтан'),
        ('hr', 'Хүний нөөц'),
        ('admin_role', 'Захирал'),
        ('sysadmin', 'Системийн админ'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee', verbose_name='Эрх')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Утас')
    department = models.CharField(max_length=100, blank=True, verbose_name='Хэлтэс')
    profile_photo = models.ImageField(upload_to='photos/', null=True, blank=True, verbose_name='Профайл зураг')

    class Meta:
        verbose_name = 'Хэрэглэгч'
        verbose_name_plural = 'Хэрэглэгчид'

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_employee(self):
        return self.role == 'employee'

    @property
    def is_hr(self):
        return self.role == 'hr'

    @property
    def is_admin_role(self):
        return self.role == 'admin_role'

    @property
    def is_sysadmin(self):
        return self.role == 'sysadmin'

    @property
    def can_view_reports(self):
        return self.role in ('hr', 'admin_role', 'sysadmin')
