"""
Management command: clear_test_data
Бүх өргөдөл, мэдэгдлийг устгана. Хэрэглэгчид хэвээр үлдэнэ.

Ажиллуулах команд:
    python manage.py clear_test_data
"""
from django.core.management.base import BaseCommand
from applications.models import Application, Attachment, DecisionHistory
from notifications.models import Notification


class Command(BaseCommand):
    help = 'Бүх өргөдөл болон мэдэгдлийг устгана. Хэрэглэгчид хэвээр үлдэнэ.'

    def handle(self, *args, **options):
        # Устгахын өмнө тоог тоолно
        attach_count = Attachment.objects.count()
        history_count = DecisionHistory.objects.count()
        app_count = Application.objects.count()
        notif_count = Notification.objects.count()

        # Хамаарлын дарааллаар устгана — эхлээд child, дараа нь parent
        Attachment.objects.all().delete()
        DecisionHistory.objects.all().delete()
        Application.objects.all().delete()
        Notification.objects.all().delete()

        # Үр дүнг хэвлэнэ
        self.stdout.write(self.style.SUCCESS('=' * 45))
        self.stdout.write(self.style.SUCCESS('  Өгөгдөл амжилттай цэвэрлэгдлээ!'))
        self.stdout.write(self.style.SUCCESS('=' * 45))
        self.stdout.write(f'  Хавсралт устгасан    : {attach_count}')
        self.stdout.write(f'  Шийдвэрийн түүх      : {history_count}')
        self.stdout.write(f'  Өргөдөл устгасан     : {app_count}')
        self.stdout.write(f'  Мэдэгдэл устгасан    : {notif_count}')
        self.stdout.write(self.style.SUCCESS('=' * 45))
        self.stdout.write('  Хэрэглэгчид хэвээр үлдлээ.')
        self.stdout.write(self.style.SUCCESS('=' * 45))
