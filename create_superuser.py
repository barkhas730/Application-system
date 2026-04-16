"""
Тест хэрэглэгчдийг үүсгэх скрипт.
Ажиллуулах: python manage.py shell < create_superuser.py
Эсвэл: python create_superuser.py (manage.py байгаа лавлахаас)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import CustomUser

users = [
    {'username': 'sysadmin', 'password': 'admin1234', 'role': 'sysadmin',
     'first_name': 'Систем', 'last_name': 'Админ', 'email': 'sysadmin@example.mn', 'is_staff': True, 'is_superuser': True},
    {'username': 'hr_user', 'password': 'hr1234', 'role': 'hr',
     'first_name': 'Болормаа', 'last_name': 'Ганбат', 'email': 'hr@example.mn', 'department': 'Хүний нөөцийн хэлтэс'},
    {'username': 'admin_user', 'password': 'admin1234', 'role': 'admin_role',
     'first_name': 'Баасандорж', 'last_name': 'Намдаг', 'email': 'admin@example.mn', 'department': 'Захиргааны хэлтэс'},
    {'username': 'employee1', 'password': 'emp1234', 'role': 'employee',
     'first_name': 'Бархас', 'last_name': 'Лхаасүрэн', 'email': 'emp1@example.mn', 'department': 'МКУТ'},
    {'username': 'employee2', 'password': 'emp1234', 'role': 'employee',
     'first_name': 'Мөнхцэцэг', 'last_name': 'Дорж', 'email': 'emp2@example.mn', 'department': 'Санхүүгийн хэлтэс'},
]

for u in users:
    if not CustomUser.objects.filter(username=u['username']).exists():
        user = CustomUser.objects.create_user(
            username=u['username'],
            password=u['password'],
            role=u['role'],
            first_name=u.get('first_name', ''),
            last_name=u.get('last_name', ''),
            email=u.get('email', ''),
            department=u.get('department', ''),
            is_staff=u.get('is_staff', False),
            is_superuser=u.get('is_superuser', False),
        )
        print(f"✓ Үүслээ: {user.username} ({user.get_role_display()})")
    else:
        print(f"- Аль хэдийн байна: {u['username']}")

print("\nДуусав! Нэвтрэх мэдээлэл:")
print("  sysadmin / admin1234")
print("  hr_user  / hr1234")
print("  admin_user / admin1234")
print("  employee1  / emp1234")
print("  employee2  / emp1234")
