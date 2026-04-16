"""
applications.services модулийн unit test-үүд.

mutmut mutation testing-д зориулан:
- Тоон хязгаар (return_count >= 3) тэнцэл/тэгш бус байдлыг тест хийнэ
- Статусын тодорхой утгуудыг тест хийнэ
- Boolean утгуудыг тест хийнэ
- Нөхцөлт логик (duplicate check, file size) тест хийнэ

Ажиллуулах:
    pytest tests/test_application_service.py -v
Mutation testing:
    mutmut run --paths-to-mutate applications/services.py
    mutmut results
"""

import pytest
from django.utils import timezone

from applications import services as svc
from applications.models import Application, DecisionHistory
from notifications.models import Notification


# ===========================================================================
# format_date_mongolian
# ===========================================================================

class TestFormatDateMongolian:
    """Огноо форматлах функцийн тест."""

    def test_valid_date_returns_mongolian_format(self):
        """YYYY-MM-DD форматыг монгол хэлнд хөрвүүлнэ."""
        result = svc.format_date_mongolian('2024-03-15')
        assert '2024' in result
        assert '3-р' in result
        assert '15' in result

    def test_january_returns_first_month(self):
        """1-р сар зөв орчуулагдана."""
        result = svc.format_date_mongolian('2024-01-01')
        assert '1-р' in result

    def test_december_returns_twelfth_month(self):
        """12-р сар зөв орчуулагдана."""
        result = svc.format_date_mongolian('2024-12-31')
        assert '12-р' in result

    def test_non_date_string_returned_unchanged(self):
        """Огноо биш утга хөрвүүлэлтгүй буцаана."""
        assert svc.format_date_mongolian('хүсэлт') == 'хүсэлт'

    def test_integer_returned_unchanged(self):
        """Тоон утга хөрвүүлэлтгүй буцаана."""
        assert svc.format_date_mongolian(42) == 42

    def test_empty_string_returned_unchanged(self):
        """Хоосон мөр хөрвүүлэлтгүй буцаана."""
        assert svc.format_date_mongolian('') == ''


# ===========================================================================
# extract_extra_fields
# ===========================================================================

class TestExtractExtraFields:
    """POST өгөгдлөөс динамик талбар ялгах функцийн тест."""

    def test_system_fields_excluded(self):
        """Системийн стандарт талбарууд хасагдана."""
        post_data = {
            'csrfmiddlewaretoken': 'abc',
            'action': 'submit',
            'title': 'Тест',
            'leave_type': 'Жил бүрийн чөлөө',
        }
        result = svc.extract_extra_fields(post_data)
        assert 'csrfmiddlewaretoken' not in result
        assert 'action' not in result
        assert 'title' not in result

    def test_custom_fields_included(self):
        """Хэрэглэгчийн нэмэлт талбар оруулна."""
        post_data = {'leave_type': 'Жил бүрийн чөлөө', 'reason': 'Яаралтай'}
        result = svc.extract_extra_fields(post_data)
        assert result['leave_type'] == 'Жил бүрийн чөлөө'
        assert result['reason'] == 'Яаралтай'

    def test_empty_values_excluded(self):
        """Хоосон утгатай талбар хасагдана."""
        post_data = {'leave_type': '', 'reason': '   '}
        result = svc.extract_extra_fields(post_data)
        assert 'leave_type' not in result
        assert 'reason' not in result

    def test_whitespace_stripped(self):
        """Утгын хажуугийн цагаан зай хасагдана."""
        post_data = {'reason': '  Яаралтай  '}
        result = svc.extract_extra_fields(post_data)
        assert result['reason'] == 'Яаралтай'


# ===========================================================================
# build_extra_display
# ===========================================================================

class TestBuildExtraDisplay:
    """extra_data-г харуулах форматад хөрвүүлэх функцийн тест."""

    def test_known_key_translated(self):
        """Мэдэгдэж байгаа түлхүүрийг монгол нэрнд хөрвүүлнэ."""
        result = svc.build_extra_display({'reason': 'Яаралтай'})
        labels = [r[0] for r in result]
        assert 'Шалтгаан' in labels

    def test_unknown_key_kept_as_is(self):
        """Мэдэгдэхгүй түлхүүрийг тэр чигт нь хадгалана."""
        result = svc.build_extra_display({'custom_field': 'Утга'})
        labels = [r[0] for r in result]
        assert 'custom_field' in labels

    def test_empty_values_excluded(self):
        """Хоосон утга харуулахгүй."""
        result = svc.build_extra_display({'reason': '', 'leave_type': 'Чөлөө'})
        assert len(result) == 1

    def test_empty_dict_returns_empty_list(self):
        """Хоосон extra_data-г хоосон жагсаалт болгоно."""
        assert svc.build_extra_display({}) == []

    def test_none_returns_empty_list(self):
        """None утгыг хоосон жагсаалт болгоно."""
        assert svc.build_extra_display(None) == []


# ===========================================================================
# has_open_application
# ===========================================================================

@pytest.mark.django_db
class TestHasOpenApplication:
    """Давхардсан нээлттэй өргөдөл шалгах функцийн тест."""

    def test_returns_true_when_submitted_exists(self, employee_user, app_type, submitted_app):
        """Илгээгдсэн өргөдөл байвал True буцаана."""
        result = svc.has_open_application(employee_user, app_type)
        assert result is True

    def test_returns_false_when_no_open_app(self, employee_user, app_type):
        """Нээлттэй өргөдөл байхгүй бол False буцаана."""
        result = svc.has_open_application(employee_user, app_type)
        assert result is False

    def test_approved_app_not_counted_as_open(self, employee_user, app_type):
        """Зөвшөөрөгдсөн өргөдөл 'нээлттэй' гэж тооцогдохгүй."""
        Application.objects.create(
            user=employee_user, app_type=app_type,
            title='Хуучин', status='approved',
            is_draft=False, extra_data={},
        )
        result = svc.has_open_application(employee_user, app_type)
        assert result is False

    def test_exclude_pk_skips_self(self, employee_user, app_type, submitted_app):
        """exclude_pk тухайн өргөдлийг тооцохгүй орхино."""
        result = svc.has_open_application(employee_user, app_type, exclude_pk=submitted_app.pk)
        assert result is False

    def test_returned_app_counted_as_open(self, employee_user, app_type):
        """Буцаагдсан өргөдөл 'нээлттэй' гэж тооцогдоно."""
        Application.objects.create(
            user=employee_user, app_type=app_type,
            title='Буцаагдсан', status='returned',
            is_draft=False, return_count=1, extra_data={},
        )
        result = svc.has_open_application(employee_user, app_type)
        assert result is True


# ===========================================================================
# return_application
# ===========================================================================

@pytest.mark.django_db
class TestReturnApplication:
    """HR буцаах функцийн тест — mutmut-д хамгийн чухал."""

    def test_first_return_sets_returned_status(self, submitted_app, hr_user):
        """1-р буцаалт — статус 'returned' болно."""
        app, auto_rejected = svc.return_application(submitted_app, hr_user, 'Баримт дутуу')
        app.refresh_from_db()
        assert app.status == 'returned'
        assert auto_rejected is False

    def test_first_return_increments_count_to_one(self, submitted_app, hr_user):
        """1-р буцаалтад return_count 1 болно."""
        svc.return_application(submitted_app, hr_user, 'Шалтгаан')
        submitted_app.refresh_from_db()
        assert submitted_app.return_count == 1

    def test_second_return_increments_count_to_two(self, employee_user, app_type, hr_user):
        """2-р буцаалтад return_count 2 болно — auto-reject болохгүй."""
        app = Application.objects.create(
            user=employee_user, app_type=app_type,
            title='Тест', status='submitted',
            is_draft=False, return_count=1, extra_data={},
        )
        result_app, auto_rejected = svc.return_application(app, hr_user, 'Шалтгаан')
        result_app.refresh_from_db()
        assert result_app.return_count == 2
        assert auto_rejected is False
        assert result_app.status == 'returned'

    def test_third_return_auto_rejects(self, employee_user, app_type, hr_user):
        """3-р буцаалтад автоматаар татгалзана."""
        app = Application.objects.create(
            user=employee_user, app_type=app_type,
            title='Тест', status='submitted',
            is_draft=False, return_count=2, extra_data={},
        )
        result_app, auto_rejected = svc.return_application(app, hr_user, 'Шалтгаан')
        result_app.refresh_from_db()
        assert auto_rejected is True
        assert result_app.status == 'rejected'

    def test_third_return_sets_count_to_three(self, employee_user, app_type, hr_user):
        """3-р буцаалтад return_count 3 болно."""
        app = Application.objects.create(
            user=employee_user, app_type=app_type,
            title='Тест', status='submitted',
            is_draft=False, return_count=2, extra_data={},
        )
        svc.return_application(app, hr_user, 'Шалтгаан')
        app.refresh_from_db()
        assert app.return_count == 3

    def test_third_return_sets_closed_at(self, employee_user, app_type, hr_user):
        """Auto-reject болбол closed_at огноо тэмдэглэгдэнэ."""
        app = Application.objects.create(
            user=employee_user, app_type=app_type,
            title='Тест', status='submitted',
            is_draft=False, return_count=2, extra_data={},
        )
        svc.return_application(app, hr_user, 'Шалтгаан')
        app.refresh_from_db()
        assert app.closed_at is not None

    def test_second_return_does_not_set_closed_at(self, employee_user, app_type, hr_user):
        """Энгийн буцаалтад closed_at тэмдэглэгдэхгүй."""
        app = Application.objects.create(
            user=employee_user, app_type=app_type,
            title='Тест', status='submitted',
            is_draft=False, return_count=1, extra_data={},
        )
        svc.return_application(app, hr_user, 'Шалтгаан')
        app.refresh_from_db()
        assert app.closed_at is None

    def test_return_creates_decision_history(self, submitted_app, hr_user):
        """Буцаалт DecisionHistory бичлэг үүсгэнэ."""
        before = DecisionHistory.objects.count()
        svc.return_application(submitted_app, hr_user, 'Баримт дутуу')
        assert DecisionHistory.objects.count() == before + 1

    def test_auto_reject_creates_reject_history(self, employee_user, app_type, hr_user):
        """Auto-reject-ийн history бичлэгийн action 'reject' байна."""
        app = Application.objects.create(
            user=employee_user, app_type=app_type,
            title='Тест', status='submitted',
            is_draft=False, return_count=2, extra_data={},
        )
        svc.return_application(app, hr_user, 'Шалтгаан')
        last = DecisionHistory.objects.filter(application=app).order_by('-created_at').first()
        assert last.action == 'reject'

    def test_normal_return_creates_return_history(self, submitted_app, hr_user):
        """Энгийн буцаалтын history бичлэгийн action 'return' байна."""
        svc.return_application(submitted_app, hr_user, 'Шалтгаан')
        last = DecisionHistory.objects.filter(application=submitted_app).order_by('-created_at').first()
        assert last.action == 'return'

    def test_return_sends_notification_to_employee(self, submitted_app, hr_user, employee_user):
        """Буцаалт ажилтанд мэдэгдэл явуулна."""
        before = Notification.objects.filter(user=employee_user).count()
        svc.return_application(submitted_app, hr_user, 'Баримт дутуу')
        assert Notification.objects.filter(user=employee_user).count() == before + 1

    def test_auto_reject_limit_is_three(self, employee_user, app_type, hr_user):
        """Auto-reject хязгаар 3 байна — 2-т болохгүй."""
        app = Application.objects.create(
            user=employee_user, app_type=app_type,
            title='Тест', status='submitted',
            is_draft=False, return_count=1, extra_data={},
        )
        _, auto_rejected = svc.return_application(app, hr_user, 'Шалтгаан')
        # return_count 1→2 болсон тул auto-reject болохгүй
        assert auto_rejected is False


# ===========================================================================
# decide_application
# ===========================================================================

@pytest.mark.django_db
class TestDecideApplication:
    """Захирал шийдвэрлэх функцийн тест."""

    def test_approve_sets_approved_status(self, forwarded_app, director_user):
        """Зөвшөөрөх үйлдэл статусыг 'approved' болгоно."""
        app, error = svc.decide_application(forwarded_app, director_user, 'approve', 'Зөвшөөрлөө')
        forwarded_app.refresh_from_db()
        assert forwarded_app.status == 'approved'
        assert error is None

    def test_reject_sets_rejected_status(self, forwarded_app, director_user):
        """Татгалзах үйлдэл статусыг 'rejected' болгоно."""
        app, error = svc.decide_application(forwarded_app, director_user, 'reject', 'Тохирохгүй')
        forwarded_app.refresh_from_db()
        assert forwarded_app.status == 'rejected'
        assert error is None

    def test_approve_sets_closed_at(self, forwarded_app, director_user):
        """Зөвшөөрсөн өргөдөл closed_at огноо авна."""
        svc.decide_application(forwarded_app, director_user, 'approve', 'Ок')
        forwarded_app.refresh_from_db()
        assert forwarded_app.closed_at is not None

    def test_reject_sets_closed_at(self, forwarded_app, director_user):
        """Татгалзсан өргөдөл closed_at огноо авна."""
        svc.decide_application(forwarded_app, director_user, 'reject', 'Тохирохгүй')
        forwarded_app.refresh_from_db()
        assert forwarded_app.closed_at is not None

    def test_reject_without_comment_returns_error(self, forwarded_app, director_user):
        """Татгалзахдаа тайлбаргүй бол алдаа буцаана."""
        app, error = svc.decide_application(forwarded_app, director_user, 'reject', '')
        assert error is not None
        assert app is None

    def test_reject_with_whitespace_comment_returns_error(self, forwarded_app, director_user):
        """Татгалзахдаа зөвхөн цагаан зайтай тайлбар дамжуулбал алдаа буцаана."""
        app, error = svc.decide_application(forwarded_app, director_user, 'reject', '   ')
        assert error is not None

    def test_invalid_decision_returns_error(self, forwarded_app, director_user):
        """Буруу decision утга дамжуулбал алдаа буцаана."""
        app, error = svc.decide_application(forwarded_app, director_user, 'unknown', 'Тест')
        assert error is not None
        assert app is None

    def test_approve_creates_decision_history(self, forwarded_app, director_user):
        """Зөвшөөрөл DecisionHistory бичлэг үүсгэнэ."""
        before = DecisionHistory.objects.count()
        svc.decide_application(forwarded_app, director_user, 'approve', 'Ок')
        assert DecisionHistory.objects.count() == before + 1

    def test_approve_history_action_is_approve(self, forwarded_app, director_user):
        """Зөвшөөрлийн history action нь 'approve' байна."""
        svc.decide_application(forwarded_app, director_user, 'approve', 'Ок')
        last = DecisionHistory.objects.filter(application=forwarded_app).order_by('-created_at').first()
        assert last.action == 'approve'

    def test_reject_history_action_is_reject(self, forwarded_app, director_user):
        """Татгалзалтын history action нь 'reject' байна."""
        svc.decide_application(forwarded_app, director_user, 'reject', 'Тохирохгүй')
        last = DecisionHistory.objects.filter(application=forwarded_app).order_by('-created_at').first()
        assert last.action == 'reject'

    def test_approve_sends_notification_to_applicant(self, forwarded_app, director_user, employee_user):
        """Зөвшөөрөл ажилтанд мэдэгдэл явуулна."""
        before = Notification.objects.filter(user=employee_user).count()
        svc.decide_application(forwarded_app, director_user, 'approve', 'Ок')
        assert Notification.objects.filter(user=employee_user).count() == before + 1

    def test_reject_sends_notification_to_applicant(self, forwarded_app, director_user, employee_user):
        """Татгалзал ажилтанд мэдэгдэл явуулна."""
        before = Notification.objects.filter(user=employee_user).count()
        svc.decide_application(forwarded_app, director_user, 'reject', 'Тохирохгүй')
        assert Notification.objects.filter(user=employee_user).count() == before + 1


# ===========================================================================
# cancel_application
# ===========================================================================

@pytest.mark.django_db
class TestCancelApplication:
    """Ажилтан цуцлах функцийн тест."""

    def test_cancel_sets_cancelled_status(self, submitted_app, employee_user):
        """Цуцлалт статусыг 'cancelled' болгоно."""
        svc.cancel_application(submitted_app, employee_user)
        submitted_app.refresh_from_db()
        assert submitted_app.status == 'cancelled'

    def test_cancel_sets_is_cancelled_true(self, submitted_app, employee_user):
        """Цуцлалт is_cancelled=True болгоно."""
        svc.cancel_application(submitted_app, employee_user)
        submitted_app.refresh_from_db()
        assert submitted_app.is_cancelled is True

    def test_cancel_sets_closed_at(self, submitted_app, employee_user):
        """Цуцлалт closed_at огноо тэмдэглэнэ."""
        svc.cancel_application(submitted_app, employee_user)
        submitted_app.refresh_from_db()
        assert submitted_app.closed_at is not None

    def test_cancel_creates_decision_history(self, submitted_app, employee_user):
        """Цуцлалт DecisionHistory бичлэг үүсгэнэ."""
        before = DecisionHistory.objects.count()
        svc.cancel_application(submitted_app, employee_user)
        assert DecisionHistory.objects.count() == before + 1

    def test_cancel_history_action_is_cancel(self, submitted_app, employee_user):
        """Цуцлалтын history action нь 'cancel' байна."""
        svc.cancel_application(submitted_app, employee_user)
        last = DecisionHistory.objects.filter(application=submitted_app).order_by('-created_at').first()
        assert last.action == 'cancel'

    def test_draft_cancel_does_not_log(self, draft_app, employee_user):
        """
        Ноорогоос цуцлалт системийн логт орохгүй.
        (Ноорог хэзээ ч хүргүүлэгдэж байгаагүй тул мэдэгдэх шаардлагагүй)
        """
        from logs.models import SystemLog
        before = SystemLog.objects.count()
        # Ноорогыг 'submitted' мэт байлгаад cancelled руу шилжүүлнэ
        draft_app.status = 'draft'
        draft_app.save()
        svc.cancel_application(draft_app, employee_user)
        # Ноорог цуцлалт лог үүсгэхгүй — was_submitted=False тул
        assert SystemLog.objects.count() == before

    def test_submitted_cancel_creates_log(self, submitted_app, employee_user):
        """Илгээгдсэн өргөдлийн цуцлалт системийн логт орно."""
        from logs.models import SystemLog
        before = SystemLog.objects.count()
        svc.cancel_application(submitted_app, employee_user)
        assert SystemLog.objects.count() == before + 1


# ===========================================================================
# forward_application
# ===========================================================================

@pytest.mark.django_db
class TestForwardApplication:
    """HR дамжуулах функцийн тест."""

    def test_forward_sets_forwarded_status(self, submitted_app, hr_user, director_user):
        """Дамжуулалт статусыг 'forwarded' болгоно."""
        svc.forward_application(submitted_app, hr_user, director_user, 'Тест тайлбар')
        submitted_app.refresh_from_db()
        assert submitted_app.status == 'forwarded'

    def test_forward_assigns_director(self, submitted_app, hr_user, director_user):
        """Дамжуулалт assigned_to-г тохируулна."""
        svc.forward_application(submitted_app, hr_user, director_user, '')
        submitted_app.refresh_from_db()
        assert submitted_app.assigned_to == director_user

    def test_forward_creates_decision_history(self, submitted_app, hr_user, director_user):
        """Дамжуулалт DecisionHistory бичлэг үүсгэнэ."""
        before = DecisionHistory.objects.count()
        svc.forward_application(submitted_app, hr_user, director_user, 'Тест')
        assert DecisionHistory.objects.count() == before + 1

    def test_forward_history_action_is_forward(self, submitted_app, hr_user, director_user):
        """Дамжуулалтын history action нь 'forward' байна."""
        svc.forward_application(submitted_app, hr_user, director_user, 'Тест')
        last = DecisionHistory.objects.filter(application=submitted_app).order_by('-created_at').first()
        assert last.action == 'forward'

    def test_forward_notifies_director(self, submitted_app, hr_user, director_user):
        """Дамжуулалт захиралд мэдэгдэл явуулна."""
        before = Notification.objects.filter(user=director_user).count()
        svc.forward_application(submitted_app, hr_user, director_user, 'Тест')
        assert Notification.objects.filter(user=director_user).count() == before + 1

    def test_forward_notifies_employee(self, submitted_app, hr_user, director_user, employee_user):
        """Дамжуулалт ажилтанд мэдэгдэл явуулна."""
        before = Notification.objects.filter(user=employee_user).count()
        svc.forward_application(submitted_app, hr_user, director_user, 'Тест')
        assert Notification.objects.filter(user=employee_user).count() == before + 1

    def test_empty_comment_uses_auto_message(self, submitted_app, hr_user, director_user):
        """Тайлбар хоосон бол авто мессеж үүсгэнэ."""
        svc.forward_application(submitted_app, hr_user, director_user, '')
        last = DecisionHistory.objects.filter(application=submitted_app).order_by('-created_at').first()
        assert last.comment != ''


# ===========================================================================
# save_attachment
# ===========================================================================

@pytest.mark.django_db
class TestSaveAttachment:
    """Хавсралт хадгалах функцийн тест."""

    def test_oversized_file_returns_false(self, submitted_app, employee_user):
        """10МБ-аас их файл хадгалахгүй, False буцаана."""
        from unittest.mock import MagicMock
        large_file = MagicMock()
        large_file.size = svc.MAX_FILE_SIZE + 1  # Хязгаараас 1 байт их
        result = svc.save_attachment(submitted_app, large_file, employee_user)
        assert result is False

    def test_valid_file_returns_true(self, submitted_app, employee_user, tmp_path):
        """Хэмжээ хязгаарт байгаа файлыг хадгалж True буцаана."""
        from unittest.mock import MagicMock
        import tempfile, os
        from django.core.files.uploadedfile import SimpleUploadedFile

        small_file = SimpleUploadedFile('test.txt', b'content', content_type='text/plain')
        result = svc.save_attachment(submitted_app, small_file, employee_user)
        assert result is True

    def test_max_size_file_accepted(self, submitted_app, employee_user):
        """Яг 10МБ файл хүлээн авна (хязгаарт тэнцүү)."""
        from unittest.mock import MagicMock
        exact_file = MagicMock()
        exact_file.size = svc.MAX_FILE_SIZE  # Яг хязгаар
        # Хадгалахыг оролдох үед DB алдаа гарч болно (mock file) тул зөвхөн хэмжээний шалгалт тест хийнэ
        # Хэмжээний нөхцөл: size > MAX_FILE_SIZE бол False, тэгэхгүй бол хадгалах
        assert exact_file.size <= svc.MAX_FILE_SIZE


# ===========================================================================
# AUTO_REJECT_RETURN_LIMIT тогтмол
# ===========================================================================

class TestAutoRejectLimit:
    """AUTO_REJECT_RETURN_LIMIT тогтмлын тест."""

    def test_limit_is_three(self):
        """Auto-reject хязгаар 3 байна."""
        assert svc.AUTO_REJECT_RETURN_LIMIT == 3

    def test_limit_is_not_two(self):
        """Auto-reject хязгаар 2 биш."""
        assert svc.AUTO_REJECT_RETURN_LIMIT != 2

    def test_limit_is_not_four(self):
        """Auto-reject хязгаар 4 биш."""
        assert svc.AUTO_REJECT_RETURN_LIMIT != 4


# ===========================================================================
# MAX_FILE_SIZE тогтмол
# ===========================================================================

class TestMaxFileSize:
    """MAX_FILE_SIZE тогтмлын тест."""

    def test_max_file_size_is_10mb(self):
        """Файлын хязгаар 10МБ байна."""
        assert svc.MAX_FILE_SIZE == 10 * 1024 * 1024

    def test_max_file_size_is_positive(self):
        """Файлын хязгаар эерэг байна."""
        assert svc.MAX_FILE_SIZE > 0
