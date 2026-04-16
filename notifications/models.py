from django.db import models
from django.conf import settings


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications', verbose_name='Хэрэглэгч')
    title = models.CharField(max_length=200, verbose_name='Гарчиг')
    message = models.TextField(verbose_name='Мэдэгдэл')
    is_read = models.BooleanField(default=False, verbose_name='Уншсан')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Огноо')

    class Meta:
        verbose_name = 'Мэдэгдэл'
        verbose_name_plural = 'Мэдэгдлүүд'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.title}"
