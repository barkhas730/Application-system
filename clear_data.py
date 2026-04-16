"""
clear_data.py — Тест өмнөх өгөгдөл цэвэрлэх скрипт
Бүх өргөдөл, мэдэгдлийг устгана. Хэрэглэгчид хэвээр үлдэнэ.

Ажиллуулах: python clear_data.py
"""
import os
import django

# Django тохиргоог эхлүүлэх
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from applications.models import Application, Attachment, DecisionHistory
from notifications.models import Notification


def clear_all():
    # Устгалтын тоог тоолоход ашиглана
    attach_count = Attachment.objects.count()
    history_count = DecisionHistory.objects.count()
    app_count = Application.objects.count()
    notif_count = Notification.objects.count()

    # Хамаарлын дарааллаар устгана — эхлээд child, дараа нь parent
    Attachment.objects.all().delete()
    DecisionHistory.objects.all().delete()
    Application.objects.all().delete()
    Notification.objects.all().delete()

    print("=" * 45)
    print("  Өгөгдөл амжилттай цэвэрлэгдлээ!")
    print("=" * 45)
    print(f"  Хавсралт устгасан    : {attach_count}")
    print(f"  Шийдвэрийн түүх      : {history_count}")
    print(f"  Өргөдөл устгасан     : {app_count}")
    print(f"  Мэдэгдэл устгасан    : {notif_count}")
    print("=" * 45)
    print("  Хэрэглэгчид хэвээр үлдлээ.")
    print("=" * 45)


if __name__ == '__main__':
    clear_all()
