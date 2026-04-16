"""
Хэлтэс шинэчлэх + захирал нэмэх скрипт.
Ажиллуулах: python -X utf8 seed_departments.py
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

# ── 1. "mkut" хэлтэсийг устга (хэрэглэгчдийн department-г хоослоно) ──────────
removed = CustomUser.objects.filter(department__icontains='mkut').update(department='')
print(f'mkut хэлтэстэй {removed} хэрэглэгчийн хэлтэс цэвэрлэгдлээ.')

# ── 2. Хэлтэсүүдийн бүтэц ─────────────────────────────────────────────────────
DEPARTMENTS = [
    'Хүний нөөцийн хэлтэс',
    'Мэдээлэл технологийн хэлтэс',
    'Санхүүгийн хэлтэс',
    'Аж ахуйн хэлтэс',
]

# ── 3. Тус бүр дор нэг захирал үүсгэнэ ──────────────────────────────────────
DIRECTORS = [
    {
        'username': 'director_hr',
        'first_name': 'Болд',
        'last_name': 'Дорж',
        'email': 'director_hr@company.mn',
        'department': 'Хүний нөөцийн хэлтэс',
        'role': 'admin_role',
    },
    {
        'username': 'director_it',
        'first_name': 'Мөнх',
        'last_name': 'Батаа',
        'email': 'director_it@company.mn',
        'department': 'Мэдээлэл технологийн хэлтэс',
        'role': 'admin_role',
    },
    {
        'username': 'director_finance',
        'first_name': 'Нарантуяа',
        'last_name': 'Гантулга',
        'email': 'director_finance@company.mn',
        'department': 'Санхүүгийн хэлтэс',
        'role': 'admin_role',
    },
    {
        'username': 'director_admin',
        'first_name': 'Энхтүвшин',
        'last_name': 'Пүрэв',
        'email': 'director_admin@company.mn',
        'department': 'Аж ахуйн хэлтэс',
        'role': 'admin_role',
    },
]

for d in DIRECTORS:
    user, created = CustomUser.objects.get_or_create(
        username=d['username'],
        defaults={
            'first_name': d['first_name'],
            'last_name': d['last_name'],
            'email': d['email'],
            'department': d['department'],
            'role': d['role'],
            'is_active': True,
        }
    )
    if created:
        user.set_password('Admin1234!')
        user.save()
        print(f'  [+] Захирал үүсгэсэн: {user.username} — {d["department"]}  (нууц үг: Admin1234!)')
    else:
        # Байгаа бол хэлтэс + эрх шинэчлэнэ
        user.department = d['department']
        user.role = d['role']
        user.save()
        print(f'  [~] Шинэчлэсэн: {user.username} — {d["department"]}')

# ── 4. Одоо байгаа ажилтнуудыг хэлтэст хувааж өгнө ─────────────────────────
# (department хоосон ажилтнуудыг жишиг байдлаар хуваарилна)
employees_no_dept = CustomUser.objects.filter(
    department='', role='employee', is_active=True
)

import itertools
cycle = itertools.cycle(DEPARTMENTS)
count = 0
for emp in employees_no_dept:
    emp.department = next(cycle)
    emp.save()
    count += 1
    print(f'  [>] {emp.username} → {emp.department}')

if count:
    print(f'\nНийт {count} ажилтанд хэлтэс хуваарилагдлаа.')
else:
    print('\nХэлтэсгүй ажилтан олдсонгүй.')

print('\nДуусгавар!')
