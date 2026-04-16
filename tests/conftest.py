"""
Pytest fixture-үүд — тестийн туршид ашиглах объектуудыг бэлдэнэ.

Эдгээр fixture-ууд нь test_*.py файлуудаас автоматаар import хийгдэнэ.
"""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


# ---------------------------------------------------------------------------
# Хэрэглэгчийн fixture-үүд
# ---------------------------------------------------------------------------

@pytest.fixture
def employee_user(db):
    """Ажилтны эрхтэй тестийн хэрэглэгч."""
    return User.objects.create_user(
        username='test_employee',
        password='testpass123',
        role='employee',
        first_name='Тест',
        last_name='Ажилтан',
        department='Хүний нөөцийн хэлтэс',
        is_active=True,
    )


@pytest.fixture
def hr_user(db):
    """Хүний нөөцийн ажилтны эрхтэй тестийн хэрэглэгч."""
    return User.objects.create_user(
        username='test_hr',
        password='testpass123',
        role='hr',
        first_name='HR',
        last_name='Менежер',
        is_active=True,
    )


@pytest.fixture
def director_user(db):
    """Захирлын (admin_role) эрхтэй тестийн хэрэглэгч."""
    return User.objects.create_user(
        username='test_director',
        password='testpass123',
        role='admin_role',
        first_name='Тест',
        last_name='Захирал',
        department='Удирдлага',
        is_active=True,
    )


@pytest.fixture
def sysadmin_user(db):
    """Системийн администраторын эрхтэй тестийн хэрэглэгч."""
    return User.objects.create_user(
        username='test_sysadmin',
        password='testpass123',
        role='sysadmin',
        is_active=True,
    )


# ---------------------------------------------------------------------------
# Өргөдлийн төрлийн fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def app_type(db):
    """Тестийн өргөдлийн төрөл."""
    from applications.models import ApplicationType
    return ApplicationType.objects.create(
        name='Чөлөөний хүсэлт',
        description='Тест чөлөөний хүсэлтийн төрөл',
        is_active=True,
        requires_attachment=False,
        required_fields=[],
        target_department='',
    )


# ---------------------------------------------------------------------------
# Өргөдлийн fixture-үүд
# ---------------------------------------------------------------------------

@pytest.fixture
def submitted_app(db, employee_user, app_type):
    """Илгээгдсэн статустай тестийн өргөдөл."""
    from applications.models import Application
    return Application.objects.create(
        user=employee_user,
        app_type=app_type,
        title='Тест өргөдөл',
        description='Тестийн зориулалтаар үүсгэсэн өргөдөл',
        status='submitted',
        is_draft=False,
        return_count=0,
        extra_data={},
    )


@pytest.fixture
def draft_app(db, employee_user, app_type):
    """Ноорог статустай тестийн өргөдөл."""
    from applications.models import Application
    return Application.objects.create(
        user=employee_user,
        app_type=app_type,
        title='(Ноорог)',
        description='',
        status='draft',
        is_draft=True,
        return_count=0,
        extra_data={},
    )


@pytest.fixture
def forwarded_app(db, employee_user, app_type, director_user):
    """Захиргаанд дамжуулагдсан тестийн өргөдөл."""
    from applications.models import Application
    return Application.objects.create(
        user=employee_user,
        app_type=app_type,
        title='Дамжуулагдсан өргөдөл',
        description='Тест',
        status='forwarded',
        is_draft=False,
        assigned_to=director_user,
        return_count=0,
        extra_data={},
    )


@pytest.fixture
def returned_app(db, employee_user, app_type):
    """Буцаагдсан тестийн өргөдөл (1 удаа буцаагдсан)."""
    from applications.models import Application
    return Application.objects.create(
        user=employee_user,
        app_type=app_type,
        title='Буцаагдсан өргөдөл',
        description='Тест',
        status='returned',
        is_draft=False,
        return_count=1,
        extra_data={},
    )
