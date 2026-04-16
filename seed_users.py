"""
Бүх хэрэглэгч устгаж, шинэ бүтцээр үүсгэх скрипт.
Ажиллуулах: python -X utf8 seed_users.py

Нийт 9 хэрэглэгч:
  1 Системийн админ
  4 Захирал (хэлтэс бүрт нэг)
  4 Ажилтан (хэлтэс бүрт нэг — зарим нь өмнө head байсан)
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

# ── 1. Бүх хэрэглэгч устгана ─────────────────────────────────────────────────
deleted, _ = CustomUser.objects.all().delete()
print(f'[x] {deleted} хэрэглэгч устгагдлаа.\n')

# ── 2. Шинэ хэрэглэгчдийн тодорхойлолт ──────────────────────────────────────
USERS = [
    # ── Системийн админ (МТ хэлтэс) ──
    {
        'username': 'sysadmin',
        'first_name': 'Систем',
        'last_name': 'Админ',
        'email': 'sysadmin@company.mn',
        'phone': '99001100',
        'department': 'Мэдээлэл технологийн хэлтэс',
        'role': 'sysadmin',
        'password': 'Admin1234!',
    },

    # ── Захирлууд (admin_role) — хэлтэс бүрд нэг ──
    {
        'username': 'director_hr',
        'first_name': 'Болд',
        'last_name': 'Дорж',
        'email': 'director.hr@company.mn',
        'phone': '99112233',
        'department': 'Хүний нөөцийн хэлтэс',
        'role': 'admin_role',
        'password': 'Admin1234!',
    },
    {
        'username': 'director_it',
        'first_name': 'Мөнх',
        'last_name': 'Батаа',
        'email': 'director.it@company.mn',
        'phone': '99223344',
        'department': 'Мэдээлэл технологийн хэлтэс',
        'role': 'admin_role',
        'password': 'Admin1234!',
    },
    {
        'username': 'director_finance',
        'first_name': 'Нарантуяа',
        'last_name': 'Гантулга',
        'email': 'director.finance@company.mn',
        'phone': '99334455',
        'department': 'Санхүүгийн хэлтэс',
        'role': 'admin_role',
        'password': 'Admin1234!',
    },
    {
        'username': 'director_admin',
        'first_name': 'Энхтүвшин',
        'last_name': 'Пүрэв',
        'email': 'director.admin@company.mn',
        'phone': '99445566',
        'department': 'Аж ахуйн хэлтэс',
        'role': 'admin_role',
        'password': 'Admin1234!',
    },

    # ── Ажилтнууд (employee) ──
    {
        'username': 'employee_it',
        'first_name': 'Бархас',
        'last_name': 'Лхаасүрэн',
        'email': 'employee.it@company.mn',
        'phone': '99667788',
        'department': 'Мэдээлэл технологийн хэлтэс',
        'role': 'employee',
        'password': 'Admin1234!',
    },
    {
        'username': 'hr_manager',
        'first_name': 'Оюунцэцэг',
        'last_name': 'Дамдин',
        'email': 'hr@company.mn',
        'phone': '99556677',
        'department': 'Хүний нөөцийн хэлтэс',
        'role': 'hr',
        'password': 'Admin1234!',
    },
    {
        'username': 'head_finance',
        'first_name': 'Оюунгэрэл',
        'last_name': 'Санжаа',
        'email': 'head.finance@company.mn',
        'phone': '99778800',
        'department': 'Санхүүгийн хэлтэс',
        'role': 'employee',
        'password': 'Admin1234!',
    },
    {
        'username': 'head_admin',
        'first_name': 'Дулмаа',
        'last_name': 'Дамдинсүрэн',
        'email': 'head.admin@company.mn',
        'phone': '99889900',
        'department': 'Аж ахуйн хэлтэс',
        'role': 'employee',
        'password': 'Admin1234!',
    },
]

# ── 3. Хэрэглэгч бүр үүсгэнэ ─────────────────────────────────────────────────
ROLE_LABELS = {
    'sysadmin':   'Системийн админ',
    'admin_role': 'Захирал',
    'hr':         'Хүний нөөц',
    'head':       'Ахлах ажилтан',
    'employee':   'Ажилтан',
}

for u in USERS:
    obj = CustomUser.objects.create_user(
        username=u['username'],
        password=u['password'],
        first_name=u['first_name'],
        last_name=u['last_name'],
        email=u['email'],
        phone=u['phone'],
        department=u['department'],
        role=u['role'],
        is_active=True,
    )
    label = ROLE_LABELS.get(u['role'], u['role'])
    print(f'  [+] {obj.get_full_name():25s}  {label:20s}  {u["department"]}')

print(f'\nНийт {len(USERS)} хэрэглэгч амжилттай үүсгэгдлээ.')
print('\nНэвтрэх мэдээлэл (бүгд нэг нууц үгтэй):')
print('  Нууц үг: Admin1234!\n')
for u in USERS:
    print(f'  {u["username"]:20s} — {ROLE_LABELS.get(u["role"])}')
