"""
View-ийн permission integration тест-үүд.

role_required болон sysadmin_required декораторын зан байдлыг шалгана:
- Нэвтрээгүй хэрэглэгч → login хуудас руу redirect
- Буруу эрхтэй хэрэглэгч → dashboard руу redirect
- Зөв эрхтэй хэрэглэгч → хуудас амжилттай нээгдэнэ (200)

Ажиллуулах:
    pytest tests/test_views_permission.py -v
"""

import pytest
from django.urls import reverse


# ===========================================================================
# sysadmin_required декораторын тест
# ===========================================================================

@pytest.mark.django_db
class TestSysadminRequiredDecorator:
    """
    sysadmin_required декораторын хандалтын хяналтыг тестлэнэ.
    Тестэд 'user_list' URL-г төлөөлөгчөөр ашиглана — бүх sysadmin view-д хамаарна.
    """

    def test_unauthenticated_user_redirects_to_login(self, client):
        """Нэвтрээгүй хэрэглэгч login хуудас руу чиглүүлэгдэнэ."""
        url = reverse('user_list')
        response = client.get(url)
        # login_required decorator redirect хийдэг
        assert response.status_code == 302
        assert '/login' in response['Location'] or 'login' in response['Location']

    def test_employee_user_redirected_to_dashboard(self, client, employee_user):
        """Ажилтны эрхтэй хэрэглэгч dashboard руу чиглүүлэгдэнэ."""
        client.force_login(employee_user)
        url = reverse('user_list')
        response = client.get(url)
        assert response.status_code == 302
        assert response['Location'] == reverse('dashboard')

    def test_hr_user_redirected_to_dashboard(self, client, hr_user):
        """Хүний нөөцийн ажилтан dashboard руу чиглүүлэгдэнэ."""
        client.force_login(hr_user)
        url = reverse('user_list')
        response = client.get(url)
        assert response.status_code == 302
        assert response['Location'] == reverse('dashboard')

    def test_director_user_redirected_to_dashboard(self, client, director_user):
        """Захирал dashboard руу чиглүүлэгдэнэ."""
        client.force_login(director_user)
        url = reverse('user_list')
        response = client.get(url)
        assert response.status_code == 302
        assert response['Location'] == reverse('dashboard')

    def test_sysadmin_user_gets_200(self, client, sysadmin_user):
        """Системийн администратор хуудсыг амжилттай нэвтэрнэ (200)."""
        client.force_login(sysadmin_user)
        url = reverse('user_list')
        response = client.get(url)
        assert response.status_code == 200


# ===========================================================================
# role_required декораторын тест
# ===========================================================================

@pytest.mark.django_db
class TestRoleRequiredDecorator:
    """
    role_required декораторын хандалтын хяналтыг тестлэнэ.
    Тестэд 'application_list' URL-г ашиглана — hr/admin_role/sysadmin эрх шаардана.
    """

    def test_unauthenticated_user_redirects_to_login(self, client):
        """Нэвтрээгүй хэрэглэгч login хуудас руу чиглүүлэгдэнэ."""
        url = reverse('application_list')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response['Location']

    def test_employee_without_required_role_redirected(self, client, employee_user):
        """Шаардлагатай эрхгүй ажилтан dashboard руу чиглүүлэгдэнэ."""
        client.force_login(employee_user)
        url = reverse('application_list')
        response = client.get(url)
        # Ажилтны эрх application_list-д хүрэхгүй тул redirect
        assert response.status_code == 302
        assert response['Location'] == reverse('dashboard')

    def test_hr_user_can_access_application_list(self, client, hr_user):
        """Хүний нөөцийн ажилтан өргөдлийн жагсаалтыг харах эрхтэй."""
        client.force_login(hr_user)
        url = reverse('application_list')
        response = client.get(url)
        assert response.status_code == 200

    def test_director_can_access_application_list(self, client, director_user):
        """Захирал өргөдлийн жагсаалтыг харах эрхтэй."""
        client.force_login(director_user)
        url = reverse('application_list')
        response = client.get(url)
        assert response.status_code == 200

    def test_sysadmin_can_access_application_list(self, client, sysadmin_user):
        """Системийн администратор өргөдлийн жагсаалтыг харах эрхтэй."""
        client.force_login(sysadmin_user)
        url = reverse('application_list')
        response = client.get(url)
        assert response.status_code == 200


# ===========================================================================
# Нэвтрэх шаардлагатай view-үүдийн тест
# ===========================================================================

@pytest.mark.django_db
class TestLoginRequiredViews:
    """
    login_required хамгаалалттай view-үүд нэвтрээгүй хэрэглэгчийг
    login хуудас руу чиглүүлдэг эсэхийг шалгана.
    """

    LOGIN_REQUIRED_URLS = [
        'dashboard',
        'notification_list',
        'profile',
    ]

    @pytest.mark.parametrize('url_name', LOGIN_REQUIRED_URLS)
    def test_anonymous_redirected_to_login(self, client, url_name):
        """Нэвтрээгүй хэрэглэгч бүх хамгаалагдсан хуудснаас login руу чиглэгдэнэ."""
        url = reverse(url_name)
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response['Location']

    def test_authenticated_user_can_access_dashboard(self, client, employee_user):
        """Нэвтэрсэн ажилтан dashboard-д хандаж чадна."""
        client.force_login(employee_user)
        response = client.get(reverse('dashboard'))
        assert response.status_code == 200

    def test_authenticated_user_can_access_profile(self, client, employee_user):
        """Нэвтэрсэн хэрэглэгч профайлд хандаж чадна."""
        client.force_login(employee_user)
        response = client.get(reverse('profile'))
        assert response.status_code == 200


# ===========================================================================
# Password reset validation тест
# ===========================================================================

@pytest.mark.django_db
class TestUserResetPasswordView:
    """
    user_reset_password_view-ийн Django validate_password ашиглалтыг тестлэнэ.
    Хуучин len < 6 шалгалтын оронд AUTH_PASSWORD_VALIDATORS ажиллаж байгааг баталгаажуулна.
    """

    def test_short_password_rejected(self, client, sysadmin_user):
        """
        Богино нууц үг (< 8 тэмдэгт) хүлээж авахгүй.
        MinimumLengthValidator 8 тэмдэгт шаарддаг — 6 тэмдэгт дамжуулахад алдаа гарна.
        """
        client.force_login(sysadmin_user)
        target = sysadmin_user
        url = reverse('user_reset_password', kwargs={'pk': target.pk})
        response = client.post(url, {'new_password': 'short'})
        # Алдааны улмаас redirect хийхгүй — хуудас дахин харагдана
        assert response.status_code == 200

    def test_numeric_only_password_rejected(self, client, sysadmin_user):
        """
        Зөвхөн тоон нууц үг NumericPasswordValidator-р татгалзагдана.
        """
        client.force_login(sysadmin_user)
        target = sysadmin_user
        url = reverse('user_reset_password', kwargs={'pk': target.pk})
        response = client.post(url, {'new_password': '12345678'})
        assert response.status_code == 200

    def test_valid_password_accepted(self, client, sysadmin_user):
        """
        Хүчтэй нууц үг амжилттай хадгалагдаж user_list руу redirect хийнэ.
        """
        client.force_login(sysadmin_user)
        target = sysadmin_user
        url = reverse('user_reset_password', kwargs={'pk': target.pk})
        response = client.post(url, {'new_password': 'Str0ng!Pass#99'})
        # Амжилттай бол user_list руу redirect
        assert response.status_code == 302
        assert response['Location'] == reverse('user_list')

    def test_non_sysadmin_cannot_reset_password(self, client, employee_user, hr_user):
        """
        Ажилтан бусдын нууц үгийг дахин тохируулах эрхгүй.
        """
        client.force_login(employee_user)
        url = reverse('user_reset_password', kwargs={'pk': hr_user.pk})
        response = client.post(url, {'new_password': 'Str0ng!Pass#99'})
        # sysadmin_required декоратор dashboard руу буцаана
        assert response.status_code == 302
        assert response['Location'] == reverse('dashboard')
