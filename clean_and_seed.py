"""
Систем лог, мэдэгдэл, өргөдлүүдийг цэвэрлэж
employee_it хэрэглэгч дээр хэлтэс тус бүрд нэг жишээ өргөдөл үүсгэнэ.
Ажиллуулах: python clean_and_seed.py
"""
import os
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from django.utils import timezone
from datetime import timedelta

from accounts.models import CustomUser
from applications.models import Application, ApplicationType, DecisionHistory
from notifications.models import Notification


def run():
    # ── 1. Систем лог цэвэрлэх ──────────────────────────────
    try:
        from logs.models import SystemLog
        deleted_logs, _ = SystemLog.objects.all().delete()
        print(f'  Систем лог: {deleted_logs} бичлэг устгагдлаа')
    except Exception as e:
        print(f'  Лог цэвэрлэхэд алдаа: {e}')

    # ── 2. Мэдэгдэл цэвэрлэх ────────────────────────────────
    deleted_notifs, _ = Notification.objects.all().delete()
    print(f'  Мэдэгдэл: {deleted_notifs} бичлэг устгагдлаа')

    # ── 3. Бүх өргөдөл устгах ───────────────────────────────
    deleted_apps, _ = Application.objects.all().delete()
    print(f'  Өргөдөл: {deleted_apps} бичлэг устгагдлаа')

    # ── 4. employee_it хэрэглэгч ────────────────────────────
    try:
        emp = CustomUser.objects.get(username='employee_it')
    except CustomUser.DoesNotExist:
        print('  [!] employee_it хэрэглэгч олдсонгүй — зогслоо')
        return

    print(f'\n  Ажилтан: {emp.get_full_name()} ({emp.department})')

    # HR болон захирлуудыг олох
    try:
        hr = CustomUser.objects.filter(role='hr', is_active=True).first()
        dir_hr      = CustomUser.objects.get(username='director_hr')
        dir_finance = CustomUser.objects.get(username='director_finance')
        dir_it      = CustomUser.objects.get(username='director_it')
        dir_admin   = CustomUser.objects.get(username='director_admin')
    except CustomUser.DoesNotExist as e:
        print(f'  [!] Захирал / HR олдсонгүй: {e}')
        return

    # Өргөдлийн төрлүүдийг олох
    types = {t.pk: t for t in ApplicationType.objects.all()}
    if not types:
        print('  [!] ApplicationType байхгүй')
        return

    # Хэлтэс тус бүрд нэг өргөдөл
    # ── А: Хүний нөөцийн хэлтэс → type 1 (Ажилласан хугацааны тодорхойлолт)
    a1 = Application.objects.create(
        user=emp,
        app_type=types[1],
        title='Ажилласан хугацааны тодорхойлолт авах',
        description='Банкны зээлийн хүсэлтэд шаардлагатай ажилласан хугацааны тодорхойлолт авахыг хүсье.',
        status='submitted',
        priority='normal',
        is_draft=False,
        submitted_at=timezone.now() - timedelta(days=2),
        extra_data={'purpose': 'Банкны зээлд', 'work_period': '3 жил 5 сар'},
        assigned_to=dir_hr,
    )
    Application.objects.filter(pk=a1.pk).update(
        created_at=timezone.now() - timedelta(days=2)
    )
    DecisionHistory.objects.create(
        application=a1, actor=emp, action='submit',
        comment='Өргөдөл илгээгдлээ.'
    )
    if hr:
        Notification.objects.create(
            user=hr,
            title=f'Шинэ өргөдөл ирлээ: {a1.app_number}',
            message=f'{emp.get_full_name()} өргөдөл илгээлээ.',
        )
    print(f'  ✓ {a1.app_number} — Хүний нөөцийн хэлтэс ({dir_hr.get_full_name()}) | submitted')

    # ── Б: Санхүүгийн хэлтэс → type 13 (Цалингийн урьдчилгаа)
    a2 = Application.objects.create(
        user=emp,
        app_type=types[13],
        title='Цалингийн урьдчилгаа авах хүсэлт',
        description='Гэр бүлийн яаралтай шаардлагын улмаас нэг сарын цалингийн 50% урьдчилгаа авахыг хүсье.',
        status='forwarded',
        priority='high',
        is_draft=False,
        submitted_at=timezone.now() - timedelta(days=5),
        extra_data={'advance_amount': '500000', 'reason': 'Гэр бүлийн яаралтай зардал', 'repayment_months': '3'},
        assigned_to=dir_finance,
    )
    Application.objects.filter(pk=a2.pk).update(
        created_at=timezone.now() - timedelta(days=5)
    )
    DecisionHistory.objects.create(application=a2, actor=emp, action='submit', comment='')
    if hr:
        DecisionHistory.objects.create(
            application=a2, actor=hr, action='forward',
            comment='Санхүүгийн захиралд дамжууллаа.'
        )
        Notification.objects.create(
            user=dir_finance,
            title=f'Өргөдөл таньд дамжуулагдлаа: {a2.app_number}',
            message=f'{emp.get_full_name()}-ийн өргөдөл таньд дамжуулагдлаа.',
        )
    print(f'  ✓ {a2.app_number} — Санхүүгийн хэлтэс ({dir_finance.get_full_name()}) | forwarded')

    # ── В: Мэдээлэл технологийн хэлтэс → type 8 (Системд нэвтрэх эрх)
    a3 = Application.objects.create(
        user=emp,
        app_type=types[8],
        title='ERP системд нэвтрэх эрх авах хүсэлт',
        description='Ажлын зорилгоор байгууллагын ERP системд засах эрх авахыг хүсье.',
        status='approved',
        priority='normal',
        is_draft=False,
        submitted_at=timezone.now() - timedelta(days=10),
        closed_at=timezone.now() - timedelta(days=7),
        extra_data={
            'system_name': 'Байгууллагын ERP систем',
            'access_type': 'Засах эрх',
            'reason': 'Ажлын даалгаврыг биелүүлэх',
            'duration': '6 сар',
        },
        assigned_to=dir_it,
    )
    Application.objects.filter(pk=a3.pk).update(
        created_at=timezone.now() - timedelta(days=10)
    )
    DecisionHistory.objects.create(application=a3, actor=emp, action='submit', comment='')
    if hr:
        DecisionHistory.objects.create(
            application=a3, actor=hr, action='forward',
            comment='МТ захиралд дамжууллаа.'
        )
    DecisionHistory.objects.create(
        application=a3, actor=dir_it, action='approve',
        comment='Зөвшөөрлөө.'
    )
    Notification.objects.create(
        user=emp,
        title=f'Өргөдөл шийдвэрлэгдлээ: {a3.app_number}',
        message='Захиргааны шийдвэр: Зөвшөөрсөн.',
    )
    print(f'  ✓ {a3.app_number} — МТ хэлтэс ({dir_it.get_full_name()}) | approved')

    # ── Г: Аж ахуйн хэлтэс → type 11 (Хангамж материал)
    a4 = Application.objects.create(
        user=emp,
        app_type=types[11],
        title='Ажлын байрны хэрэгцээт материал авах хүсэлт',
        description='Ажлын байрны A4 цаас болон бичгийн хэрэгсэл дууссан тул нэмэлт хангамж авахыг хүсье.',
        status='returned',
        priority='normal',
        is_draft=False,
        submitted_at=timezone.now() - timedelta(days=7),
        extra_data={
            'item_name': 'A4 цаас, бичгийн хэрэгсэл',
            'quantity': '5',
            'purpose': 'Өдөр тутмын ажлын хэрэгцээ',
            'estimated_cost': '45000',
        },
        assigned_to=dir_admin,
    )
    Application.objects.filter(pk=a4.pk).update(
        created_at=timezone.now() - timedelta(days=7)
    )
    DecisionHistory.objects.create(application=a4, actor=emp, action='submit', comment='')
    if hr:
        DecisionHistory.objects.create(
            application=a4, actor=hr, action='return',
            comment='Шаардлагатай хэмжээг нарийвчлан тодруулж, тооны нэгжийг зааж өгнө үү.'
        )
    Notification.objects.create(
        user=emp,
        title=f'Өргөдөл буцаагдлаа: {a4.app_number}',
        message='HR: Шаардлагатай хэмжээг нарийвчлан тодруулж, тооны нэгжийг зааж өгнө үү.',
    )
    print(f'  ✓ {a4.app_number} — Аж ахуйн хэлтэс ({dir_admin.get_full_name()}) | returned')

    print(f'\n  Нийт 4 жишээ өргөдөл амжилттай үүслээ!')
    print('\n  Төлөв:')
    print('    submitted  — Хүний нөөцийн хэлтэс (HR хянаж байна)')
    print('    forwarded  — Санхүүгийн хэлтэс (Захирал шийдвэрлэж байна)')
    print('    approved   — МТ хэлтэс (Зөвшөөрсөн)')
    print('    returned   — Аж ахуйн хэлтэс (Буцаагдсан, засвар хийх шаардлагатай)')


if __name__ == '__main__':
    print('Цэвэрлэж, жишээ өргөдлүүд үүсгэж байна...\n')
    run()
    print('\nДууслаа.')
