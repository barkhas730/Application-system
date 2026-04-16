"""
Хэрэглэгч шинэчлэх скрипт:
  - Цэцэгмаа Лхагва  (head_hr)      → устгах
  - Батбаяр Дорлиг   (head_it)      → устгах
  - Оюунцэцэг Дамдин (hr_manager)   → hr   → employee болгох
  - Оюунгэрэл Санжаа (head_finance) → head → employee болгох
  - Дулмаа Дамдинсүрэн (head_admin) → head → employee болгох

Ажиллуулах: python -X utf8 update_users.py
"""
import os
import sys
import django

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from accounts.models import CustomUser

print('=== Хэрэглэгч шинэчлэх ===\n')

# ── 1. Устгах хэрэглэгчид ────────────────────────────────────────────────────
DELETE_USERNAMES = ['head_hr', 'head_it']
for uname in DELETE_USERNAMES:
    try:
        u = CustomUser.objects.get(username=uname)
        name = u.get_full_name() or uname
        u.delete()
        print(f'[x] Устгагдлаа: {uname} ({name})')
    except CustomUser.DoesNotExist:
        print(f'[!] Олдсонгүй: {uname}')

# ── 2. Эрх өөрчлөх хэрэглэгчид ──────────────────────────────────────────────
ROLE_CHANGES = [
    ('hr_manager',   'employee'),
    ('head_finance', 'employee'),
    ('head_admin',   'employee'),
]
for uname, new_role in ROLE_CHANGES:
    try:
        u = CustomUser.objects.get(username=uname)
        old_role = u.role
        u.role = new_role
        u.save()
        print(f'[~] Шинэчлэгдлээ: {uname} ({u.get_full_name()}) — {old_role} → {new_role}')
    except CustomUser.DoesNotExist:
        print(f'[!] Олдсонгүй: {uname}')

# ── 3. Үлдсэн хэрэглэгчид ────────────────────────────────────────────────────
ROLE_LABELS = {
    'sysadmin':   'Системийн админ',
    'admin_role': 'Захирал',
    'head':       'Ахлах ажилтан',
    'hr':         'Хүний нөөц',
    'employee':   'Ажилтан',
}

print('\n─── Үлдсэн хэрэглэгчид ───────────────────────────────────────────')
for u in CustomUser.objects.all().order_by('role', 'username'):
    label = ROLE_LABELS.get(u.role, u.role)
    print(f'  {u.username:20s} | {u.get_full_name() or "—":25s} | {label:20s} | {u.department}')

print('\nДууслаа.')
