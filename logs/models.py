from django.db import models
from django.conf import settings

# Лог үйлдлүүдийн монгол нэрс
ACTION_LABELS = {
    'LOGIN': 'Нэвтрэх',
    'LOGOUT': 'Гарах',
    'APP_CREATE': 'Өргөдөл үүсгэх',
    'APP_SUBMIT': 'Өргөдөл илгээх',
    'APP_EDIT': 'Өргөдөл засах',
    'APP_DELETE': 'Өргөдөл устгах',
    'APP_CANCEL': 'Өргөдөл цуцлах',
    'APP_APPROVE': 'Өргөдөл зөвшөөрөх',
    'APP_REJECT': 'Өргөдөл татгалзах',
    'APP_RETURN': 'Өргөдөл буцаах',
    'APP_FORWARD': 'Өргөдөл дамжуулах',
    'APP_DECIDE': 'Өргөдөл шийдвэрлэх',
    'USER_CREATE': 'Хэрэглэгч үүсгэх',
    'USER_EDIT': 'Хэрэглэгч засах',
    'PASSWORD_RESET': 'Нууц үг шинэчлэх',
    'PROFILE_UPDATE': 'Профайл шинэчлэх',
}


class SystemLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Хэрэглэгч')
    action = models.CharField(max_length=50, verbose_name='Үйлдэл')
    target = models.TextField(verbose_name='Объект')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP хаяг')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Огноо')

    class Meta:
        verbose_name = 'Системийн лог'
        verbose_name_plural = 'Системийн логууд'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M} | {self.action} | {self.user}"

    @property
    def action_label(self):
        """Үйлдлийн монгол нэрийг буцаана. Тодорхойлогдоогүй бол анхны кодыг буцаана."""
        return ACTION_LABELS.get(self.action, self.action)
