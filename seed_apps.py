"""
Жишээ өргөдлүүд үүсгэх скрипт.
Ажиллуулах: python seed_apps.py
"""
import os
import sys
import django
from datetime import date, timedelta

# Windows дэлгэцийн encoding асуудлыг засна
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.utils import timezone
from accounts.models import CustomUser
from applications.models import Application, ApplicationType, DecisionHistory
from notifications.utils import create_notification


def get_or_warn(username):
    try:
        return CustomUser.objects.get(username=username)
    except CustomUser.DoesNotExist:
        print(f'  [!] {username} хэрэглэгч олдсонгүй — алгасав')
        return None


def make_app(user, app_type, title, description, status, priority='normal',
             extra_data=None, return_count=0, days_ago=0, due_offset=None):
    app = Application(
        user=user,
        app_type=app_type,
        title=title,
        description=description,
        status=status,
        priority=priority,
        extra_data=extra_data or {},
        return_count=return_count,
        is_draft=(status == 'draft'),
    )
    if due_offset is not None:
        app.due_date = date.today() + timedelta(days=due_offset)
    if status not in ('draft',):
        app.submitted_at = timezone.now() - timedelta(days=days_ago)
    if status in ('approved', 'rejected', 'cancelled'):
        app.closed_at = timezone.now() - timedelta(days=max(0, days_ago - 2))
    app.save()
    # created_at-г гараар тохируулна
    Application.objects.filter(pk=app.pk).update(
        created_at=timezone.now() - timedelta(days=days_ago)
    )
    app.refresh_from_db()
    return app


def add_history(app, actor, action, comment='', days_ago=0):
    h = DecisionHistory(
        application=app,
        actor=actor,
        action=action,
        comment=comment,
    )
    h.save()
    DecisionHistory.objects.filter(pk=h.pk).update(
        created_at=timezone.now() - timedelta(days=days_ago)
    )


def run():
    print('Жишээ өргөдлүүд үүсгэж байна...')

    emp1 = get_or_warn('employee1')
    emp2 = get_or_warn('employee2')
    hr   = get_or_warn('hr_user')
    adm  = get_or_warn('admin_user')

    if not (emp1 and hr and adm):
        print('Шаардлагатай хэрэглэгчид байхгүй. Эхлээд create_superuser.py ажиллуулна уу.')
        return

    types = {t.pk: t for t in ApplicationType.objects.all()}
    if not types:
        print('ApplicationType байхгүй. Эхлээд fixture ачаална уу:')
        print('  python manage.py loaddata fixtures/initial_data.json')
        return

    t = list(types.values())  # [0]=чөлөө, [1]=цалин, [2]=ажил, [3]=зардал, [4]=томилолт, [5]=сургалт, [6]=бусад

    # Одоо байгаа өргөдлүүдийг устгана
    deleted, _ = Application.objects.filter(user__in=[u for u in [emp1, emp2] if u]).delete()
    print(f'  Өмнөх {deleted} өргөдөл устгагдлаа')

    apps_created = []

    # ====== employee1 өргөдлүүд ======
    print('  employee1 өргөдлүүд...')

    # 1. Зөвшөөрсөн — чөлөөний хүсэлт (45 өдрийн өмнө)
    a = make_app(emp1, t[0], '5 хоногийн чөлөө хүсэх', 'Гэр бүлийн шалтгааны улмаас 5 хоногийн чөлөө авах хүсэлт гаргаж байна.',
                 'approved', 'high', {'leave_start': '2026-02-10', 'leave_end': '2026-02-14', 'leave_reason': 'Гэр бүлийн шалтгаан'}, days_ago=45)
    add_history(a, emp1, 'submit', '', 45)
    add_history(a, hr,   'forward', 'Хүсэлт нь бүрэн боловсруулагдсан байна.', 43)
    add_history(a, adm,  'approve', 'Зөвшөөрлөө.', 42)
    apps_created.append(a)

    # 2. Зөвшөөрсөн — цалингийн тодорхойлолт (30 өдрийн өмнө)
    a = make_app(emp1, t[1], 'Цалингийн тодорхойлолт авах', 'Банкны зээлийн хүсэлтэд шаардлагатай тодорхойлолт.',
                 'approved', 'normal', {'cert_purpose': 'Банкны зээл', 'cert_language': 'Монгол'}, days_ago=30)
    add_history(a, emp1, 'submit', '', 30)
    add_history(a, hr,   'forward', 'Дамжуулсан.', 28)
    add_history(a, adm,  'approve', 'Зөвшөөрлөө.', 27)
    apps_created.append(a)

    # 3. Татгалзсан — томилолт (20 өдрийн өмнө)
    a = make_app(emp1, t[4], 'Улаанбаатар хот руу томилолт', 'Хамтын ажиллагааны уулзалтад оролцох зорилгоор томилолт хүсэж байна.',
                 'rejected', 'urgent', {'travel_destination': 'Улаанбаатар', 'travel_date': '2026-03-01', 'travel_purpose': 'Хамтын ажиллагааны уулзалт', 'travel_budget': '150000'}, days_ago=20)
    add_history(a, emp1, 'submit', '', 20)
    add_history(a, hr,   'forward', 'Шалгасан.', 18)
    add_history(a, adm,  'reject', 'Тухайн хугацаанд байгууллагын ажилчдын томилолт хязгаарлагдсан байгаа тул татгалзав.', 17)
    apps_created.append(a)

    # 4. Буцаагдсан — зардлын нөхөн олговор (15 өдрийн өмнө)
    a = make_app(emp1, t[3], 'Такси зардлын нөхөн олговор', 'Ажлын зорилгоор ашигласан такси зардлын нөхөн олговор хүсэж байна.',
                 'returned', 'normal', {'expense_type': 'Тээвэр', 'expense_amount': '25000', 'expense_date': '2026-03-10', 'expense_note': 'Ажлын хурлаар явсан'}, days_ago=15)
    add_history(a, emp1, 'submit', '', 15)
    add_history(a, hr,   'return', 'Баримтыг хавсаргаагүй байна. Зардлын баримтыг хавсаргана уу.', 13)
    apps_created.append(a)

    # 5. Хянагдаж буй (submitted) — ажлын тодорхойлолт (5 өдрийн өмнө)
    a = make_app(emp1, t[2], 'Ажлын тодорхойлолт хүсэх', 'Орон сууцны зээлийн хүсэлтэд шаардлагатай ажлын тодорхойлолт.',
                 'submitted', 'normal', {'ref_purpose': 'Орон сууцны зээл', 'ref_detail': 'Голомт банк'}, days_ago=5)
    add_history(a, emp1, 'submit', '', 5)
    apps_created.append(a)

    # 6. Дамжуулагдсан — сургалтын хүсэлт (8 өдрийн өмнө)
    a = make_app(emp1, t[5], 'Python сургалтад оролцох хүсэлт', 'Мэдээллийн технологийн Python програмчлалын сургалтад оролцох хүсэлт.',
                 'forwarded', 'high', {'training_name': 'Python Advanced', 'training_org': 'Монголын IT Академи', 'training_date': '2026-04-20', 'training_cost': '350000'}, days_ago=8)
    add_history(a, emp1, 'submit', '', 8)
    add_history(a, hr,   'forward', 'Сургалт нь мэргэжлийн хөгжилд нийцсэн байна.', 6)
    apps_created.append(a)

    # 7. Ноорог — бусад хүсэлт (2 өдрийн өмнө)
    a = make_app(emp1, t[6], 'Ажлын байрны тоног төхөөрөмж шинэчлэх хүсэлт', 'Компьютерийн техник хуучирсан тул шинэчлэх хүсэлт.',
                 'draft', 'normal', {'other_title': 'Техник шинэчлэл', 'other_detail': 'Dell laptop шинэчлэх шаардлагатай'}, days_ago=2)
    apps_created.append(a)

    # 8. Зөвшөөрсөн — 60 өдрийн өмнө (chart-д харагдах)
    a = make_app(emp1, t[0], '3 хоногийн чөлөө', 'Эрүүл мэндийн шалтгаан.',
                 'approved', 'urgent', {'leave_start': '2025-11-10', 'leave_end': '2025-11-12', 'leave_reason': 'Эрүүл мэнд'}, days_ago=150)
    add_history(a, emp1, 'submit', '', 150)
    add_history(a, hr,   'forward', '', 148)
    add_history(a, adm,  'approve', 'Зөвшөөрлөө.', 147)
    apps_created.append(a)

    # 9. Chart-д харагдах — 90 өдрийн өмнө
    a = make_app(emp1, t[1], 'Цалингийн тодорхойлолт (2)', 'Визний хүсэлтэд шаардлагатай.',
                 'approved', 'normal', {'cert_purpose': 'Виз', 'cert_language': 'Англи'}, days_ago=90)
    add_history(a, emp1, 'submit', '', 90)
    add_history(a, hr,   'forward', '', 88)
    add_history(a, adm,  'approve', '', 87)
    apps_created.append(a)

    # 10. Chart-д харагдах — 60 өдрийн өмнө
    a = make_app(emp1, t[2], 'Ажлын тодорхойлолт (2)', 'Шүүхэд шаардлагатай.',
                 'approved', 'normal', {'ref_purpose': 'Шүүх', 'ref_detail': ''}, days_ago=60)
    add_history(a, emp1, 'submit', '', 60)
    add_history(a, hr,   'forward', '', 58)
    add_history(a, adm,  'approve', '', 57)
    apps_created.append(a)

    # ====== employee2 өргөдлүүд ======
    if emp2:
        print('  employee2 өргөдлүүд...')

        a = make_app(emp2, t[0], 'Эхчүүдийн баяраар чөлөө авах', '2026 оны эхчүүдийн баяраар нэг өдрийн чөлөө авах хүсэлт.',
                     'approved', 'normal', {'leave_start': '2026-03-08', 'leave_end': '2026-03-08', 'leave_reason': 'Эхчүүдийн баяр'}, days_ago=33)
        add_history(a, emp2, 'submit', '', 33)
        add_history(a, hr,   'forward', '', 31)
        add_history(a, adm,  'approve', 'Зөвшөөрлөө.', 30)
        apps_created.append(a)

        a = make_app(emp2, t[5], 'Монгол хэлний сургалт', 'Техникийн бичиг баримт боловсруулах сургалт.',
                     'submitted', 'high', {'training_name': 'Техникийн бичиг', 'training_org': 'Хэл соёлын төв', 'training_date': '2026-05-10', 'training_cost': '120000'}, days_ago=3)
        add_history(a, emp2, 'submit', '', 3)
        apps_created.append(a)

        a = make_app(emp2, t[4], 'Дархан хот руу томилолт', 'Тогтмол хамтрагч байгууллагад зочлох.',
                     'forwarded', 'urgent', {'travel_destination': 'Дархан', 'travel_date': '2026-04-25', 'travel_purpose': 'Байгууллагын зочлол', 'travel_budget': '80000'}, days_ago=10)
        add_history(a, emp2, 'submit', '', 10)
        add_history(a, hr,   'forward', 'Зайлшгүй шаардлагатай байна.', 8)
        apps_created.append(a)

    print(f'\nНийт {len(apps_created)} жишээ өргөдөл амжилттай үүслээ!')
    print('\nНэвтрэх мэдээлэл:')
    print('  employee1 / employee1pass')
    if emp2:
        print('  employee2 / employee2pass')
    print('  hr_user   / hrpass123')
    print('  admin_user / adminpass123')


if __name__ == '__main__':
    run()
