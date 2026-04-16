
"""
Өргөдлийн удирдлагын системийн бизнес логик давхарга (Application Service Layer).

Энэ модуль нь view функцүүдээс бизнес дүрмийг тусгаарлаж,
цэвэр Python функцүүдээр workflow логикийг хэрэгжүүлнэ.
View-ууд зөвхөн HTTP request/response-г зохицуулна —
бизнес шийдвэр гаргах ажил энд явагдана.
"""

import json
import re
from datetime import date
from django.utils import timezone

from .models import Application, ApplicationType, Attachment, DecisionHistory
from notifications.utils import create_notification
from logs.utils import log_action

# Хавсралт файлын хамгийн их хэмжээ (10МБ)
MAX_FILE_SIZE = 10 * 1024 * 1024

# POST өгөгдлөөс хасах системийн талбарууд — динамик extra_data-г тусгаарлахад хэрэглэнэ
_SYSTEM_FIELDS = frozenset({
    'csrfmiddlewaretoken', 'action', 'title', 'description',
    'app_type', 'priority', 'due_date', 'extra_data', 'file', 'assigned_to',
})

# Динамик маягтын талбарын монгол нэрийн толь бичиг
_FIELD_LABELS = {
    'purpose': 'Зориулалт',
    'work_period': 'Ажилласан хугацаа',
    'employee_name': 'Ажилтны нэр',
    'current_position': 'Одоогийн албан тушаал',
    'new_position': 'Шинэ албан тушаал',
    'change_type': 'Өөрчлөлтийн төрөл',
    'reason': 'Шалтгаан',
    'effective_date': 'Хүчин төгөлдөр болох огноо',
    'destination_country': 'Очих улс / хот',
    'travel_purpose': 'Зорилго',
    'travel_start': 'Эхлэх огноо',
    'travel_end': 'Дуусах огноо',
    'organization': 'Урьсан байгууллага',
    'estimated_cost': 'Тооцоолсон зардал (₮)',
    'contract_type': 'Гэрээний төрөл',
    'counterparty': 'Гэрээний нөгөө тал',
    'summary': 'Гэрээний товч агуулга',
    'contract_value': 'Гэрээний дүн (₮)',
    'contract_period': 'Гэрээний дуусах огноо',
    'expense_type': 'Зардлын төрөл',
    'expense_amount': 'Нийт дүн (₮)',
    'expense_date': 'Зардлын огноо',
    'description': 'Дэлгэрэнгүй тайлбар',
    'location': 'Байршил / өрөөний дугаар',
    'issue_type': 'Асуудлын төрөл',
    'urgency': 'Яаралтай байдал',
    'overtime_date': 'Илүү цаг ажилласан огноо',
    'hours': 'Цагийн тоо',
    'supervisor': 'Хариуцсан ажилтан',
    'system_name': 'Системийн нэр',
    'access_type': 'Эрхийн төрөл',
    'duration': 'Эрхийн хугацаа',
    'training_name': 'Сургалтын нэр',
    'training_org': 'Зохион байгуулагч байгууллага',
    'training_date': 'Огноо',
    'training_cost': 'Зардал (₮)',
    'relevance': 'Ажилд хамаарах байдал',
    'item_name': 'Нэр',
    'quantity': 'Тоо хэмжээ',
    'specs': 'Техникийн үзүүлэлт',
    'language': 'Хэрэгтэй хэл',
    'advance_amount': 'Урьдчилгааны дүн (₮)',
    'repayment_months': 'Эргэн төлөх хугацаа (сар)',
    'leave_type': 'Чөлөөний төрөл',
    'leave_start': 'Эхлэх огноо',
    'leave_end': 'Дуусах огноо',
    'leave_reason': 'Шалтгаан',
    'position': 'Албан тушаал',
    'headcount': 'Авах тоо',
    'requirements': 'Тавих шаардлага',
    'work_type': 'Ажлын хэлбэр',
    'start_date': 'Ажилд гарах хугацаа',
    # seed_apps хуучин түлхүүрүүд
    'cert_purpose': 'Зориулалт',
    'cert_language': 'Хэрэгтэй хэл',
    'ref_purpose': 'Зориулалт',
    'ref_detail': 'Дэлгэрэнгүй',
    'travel_destination': 'Очих газар',
    'travel_date': 'Огноо',
    'travel_budget': 'Төсөв (₮)',
    'expense_note': 'Тэмдэглэл',
    'other_title': 'Гарчиг',
    'other_detail': 'Дэлгэрэнгүй',
}

_MN_MONTHS = [
    '1-р', '2-р', '3-р', '4-р', '5-р', '6-р',
    '7-р', '8-р', '9-р', '10-р', '11-р', '12-р',
]

# Хэдэн удаа буцаагдвал автоматаар татгалзах вэ гэдэг хязгаар
AUTO_REJECT_RETURN_LIMIT = 3


# ---------------------------------------------------------------------------
# Туслах (утилити) функцүүд
# ---------------------------------------------------------------------------

def format_date_mongolian(value):
    """
    'YYYY-MM-DD' форматын огноог монгол хэлнд хөрвүүлнэ.
    Бусад утгыг хөрвүүлэлтгүй буцаана.

    Жишээ:
        format_date_mongolian('2024-03-15') → '2024 оны 3-р сарын 15'
    """
    if isinstance(value, str) and re.match(r'^\d{4}-\d{2}-\d{2}$', value):
        try:
            d = date.fromisoformat(value)
            return f'{d.year} оны {_MN_MONTHS[d.month - 1]} сарын {d.day}'
        except (ValueError, IndexError):
            pass
    return value


def build_extra_display(extra_data):
    """
    extra_data JSON-г template дотор харуулах (нэр, утга) хосын жагсаалт болгоно.
    Хоосон утгатай талбаруудыг хасна.
    """
    if not extra_data:
        return []
    return [
        (_FIELD_LABELS.get(k, k), format_date_mongolian(v))
        for k, v in extra_data.items()
        if v
    ]


def extract_extra_fields(post_data):
    """
    POST QueryDict-ээс маягтын динамик талбаруудыг ялгаж авна.
    Системийн стандарт талбаруудыг (_SYSTEM_FIELDS) автоматаар хасна.
    Хоосон утгатай талбаруудыг хасна.

    Returns:
        dict — гүйцэтгэгчийн бөглөсөн нэмэлт талбарууд
    """
    extra = {}
    for key, val in post_data.items():
        if key not in _SYSTEM_FIELDS:
            stripped = val.strip()
            if stripped:
                extra[key] = stripped
    return extra


def get_assigned_admin(assigned_to_id):
    """
    Хариуцах захирал / ахлах ажилтаныг ID-аар хайна.
    Олдохгүй бол None буцаана — Exception дэвшүүлэхгүй.
    Идэвхгүй болон буруу эрхтэй хэрэглэгчийг буцаахгүй.
    """
    if not assigned_to_id:
        return None
    from accounts.models import CustomUser
    try:
        return CustomUser.objects.get(
            pk=assigned_to_id, is_active=True, role='admin_role'
        )
    except CustomUser.DoesNotExist:
        return None


def save_attachment(application, file_obj, uploaded_by):
    """
    Өргөдөлд хавсралт файл хавсаргана.
    Файлын хэмжээ MAX_FILE_SIZE-ээс хэтэрвэл хадгалахгүй, False буцаана.

    Returns:
        True  — амжилттай хадгалагдсан
        False — файл хэт том
    """
    if file_obj.size > MAX_FILE_SIZE:
        return False
    Attachment.objects.create(
        application=application,
        file=file_obj,
        file_name=file_obj.name,
        file_size=file_obj.size,
        uploaded_by=uploaded_by,
    )
    return True


def has_open_application(user, app_type, exclude_pk=None):
    """
    Тухайн ажилтанд тухайн төрлийн нээлттэй өргөдөл байгаа эсэхийг шалгана.
    Нээлттэй гэдэгт: draft, submitted, forwarded, returned орно.
    exclude_pk — засварлах үед одоогийн өргөдлийг хасахад хэрэглэнэ.
    """
    qs = Application.objects.filter(
        user=user,
        app_type=app_type,
        status__in=['draft', 'submitted', 'forwarded', 'returned'],
    )
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


# ---------------------------------------------------------------------------
# Workflow үйлдлүүд — application state machine
# ---------------------------------------------------------------------------

def submit_new_application(app, user, assigned_to, action, file=None):
    """
    Шинэ өргөдөл үүсгэж хадгална (draft эсвэл submit).

    Parameters
    ----------
    app         : Application — form.save(commit=False)-р үүссэн, DB-д хадгалагдаагүй объект
    user        : CustomUser — өргөдөл гаргагч ажилтан
    assigned_to : CustomUser | None — урьдчилан сонгосон хариуцах захирал
    action      : 'draft' | 'submit'
    file        : UploadedFile | None

    Returns
    -------
    tuple (Application, error_message | None)
    """
    # Давхардсан нээлттэй өргөдөл шалгана — зөвхөн submit үед
    if action == 'submit':
        if has_open_application(user, app.app_type):
            return None, 'Энэ төрлийн нээлттэй өргөдөл аль хэдийн байна.'

    # Хэрэглэгч болон гарчгийг тохируулна
    app.user = user
    if not app.title:
        app.title = '(Ноорог)'

    # Хариуцах захирлыг тохируулна (ажилтан урьдчилан сонгосон бол)
    if assigned_to is not None:
        app.assigned_to = assigned_to

    # Статус тохируулна
    if action == 'submit':
        app.status = 'submitted'
        app.is_draft = False
        app.submitted_at = timezone.now()
    else:
        app.status = 'draft'
        app.is_draft = True

    app.save()

    # Хавсралт файл хадгална
    if file is not None:
        save_attachment(app, file, user)

    # Шийдвэрийн түүхэнд тэмдэглэнэ
    DecisionHistory.objects.create(
        application=app,
        actor=user,
        action='submit',
        comment=(
            'Өргөдөл үүсгэгдлээ.' if action == 'draft'
            else 'Өргөдөл илгээгдлээ.'
        ),
    )

    # Submit үед систем лог болон HR мэдэгдэл явуулна
    if action == 'submit':
        log_action(user, 'APP_CREATE', f'Өргөдөл илгээгдсэн: {app.app_number}')
        _notify_hr_new_application(user, app)

    return app, None


def resubmit_application(app, user, assigned_to, action, file=None):
    """
    Буцаагдсан / ноорог өргөдлийг засварлаж дахин хадгалах эсвэл илгээх.

    Parameters
    ----------
    app         : Application — засварлагдаж буй өргөдөл (DB-д аль хэдийн байгаа)
    user        : CustomUser — өргөдлийн эзэн
    assigned_to : CustomUser | None
    action      : 'draft' | 'submit'
    file        : UploadedFile | None — нэмэлт хавсралт

    Returns
    -------
    Application (алдаа байхгүй, view талд form.is_valid() тулгуурна)
    """
    if assigned_to is not None:
        app.assigned_to = assigned_to

    if action == 'submit':
        app.status = 'submitted'
        app.is_draft = False
        # Анхны илгээлтийн огноог хадгалж үлдэнэ
        if not app.submitted_at:
            app.submitted_at = timezone.now()

        DecisionHistory.objects.create(
            application=app,
            actor=user,
            action='resubmit',
            comment='Өргөдөл засч дахин илгээгдлээ.',
        )
        _notify_hr_resubmit(user, app)
    else:
        app.status = 'draft'
        app.is_draft = True

    app.save()

    # Нэмэлт хавсралт файл байвал хадгална
    if file is not None:
        save_attachment(app, file, user)

    # Дахин submit үед л логдоно
    if action == 'submit':
        log_action(user, 'APP_EDIT', f'Өргөдөл засварлаж дахин илгээгдсэн: {app.app_number}')

    return app


def cancel_application(app, actor):
    """
    Ажилтан өөрийн өргөдлийг цуцална.
    Зөвхөн app.can_cancel == True үед дуудагдах ёстой (view шалгана).

    Зөвхөн өмнө нь хүргүүлэгдсэн өргөдлийн цуцлалтыг лог болгоно —
    ноорогоос цуцалсан бол хэн ч мэдэх шаардлагагүй.

    Returns:
        Application — хадгалагдсан объект
    """
    # Цуцлахаас өмнөх статусыг тэмдэглэнэ (лог шаардлага тодорхойлох)
    was_submitted = app.status in ('submitted', 'returned')

    app.status = 'cancelled'
    app.is_cancelled = True
    app.closed_at = timezone.now()
    app.save()

    DecisionHistory.objects.create(
        application=app,
        actor=actor,
        action='cancel',
        comment='Ажилтан өргөдлийг цуцаллаа.',
    )

    if was_submitted:
        log_action(actor, 'APP_CANCEL', f'Өргөдөл цуцалсан: {app.app_number}')

    return app


def forward_application(app, hr_actor, assigned_admin, comment=''):
    """
    HR ажилтан өргөдлийг захиргаанд дамжуулна.
    Зөвхөн status='submitted' үед дуудагдана (view шалгана).

    Parameters
    ----------
    app            : Application
    hr_actor       : CustomUser (HR эрхтэй)
    assigned_admin : CustomUser (admin_role эрхтэй) — хариуцах захирал
    comment        : str — HR-ийн тайлбар

    Returns:
        Application — шинэчлэгдсэн объект
    """
    app.status = 'forwarded'
    app.assigned_to = assigned_admin
    app.save()

    # Дамжуулалтын тайлбар — тайлбар хоосон бол авто мессеж үүсгэнэ
    final_comment = comment or (
        f'{assigned_admin.get_full_name() or assigned_admin.username} захиралд дамжуулагдлаа.'
    )
    DecisionHistory.objects.create(
        application=app,
        actor=hr_actor,
        action='forward',
        comment=final_comment,
    )

    # Захиралд болон өргөдлийн эзэнд мэдэгдэл явуулна
    create_notification(
        assigned_admin,
        f'Өргөдөл дамжуулагдлаа: {app.app_number}',
        f'HR {hr_actor.get_full_name() or hr_actor.username} өргөдлийг таньд дамжуулав.',
    )
    create_notification(
        app.user,
        f'Таны өргөдөл дамжуулагдлаа: {app.app_number}',
        'Таны өргөдлийг HR захиргаанд дамжууллаа.',
    )

    log_action(hr_actor, 'APP_FORWARD', f'Өргөдөл дамжуулсан: {app.app_number}')
    return app


def return_application(app, hr_actor, comment):
    """
    HR ажилтан өргөдлийг ажилтанд буцаана.
    Зөвхөн status='submitted' үед дуудагдана (view шалгана).

    return_count >= AUTO_REJECT_RETURN_LIMIT болбол автоматаар татгалзана.

    Parameters
    ----------
    app      : Application
    hr_actor : CustomUser (HR эрхтэй)
    comment  : str — буцаалтын шалтгаан (заавал)

    Returns
    -------
    tuple (Application, auto_rejected: bool)
        auto_rejected=True  → 3 дахь буцаалтаар татгалзагдсан
        auto_rejected=False → энгийн буцаалт
    """
    app.return_count += 1

    if app.return_count >= AUTO_REJECT_RETURN_LIMIT:
        # 3 дахь буцаалт — автоматаар татгалзана
        app.status = 'rejected'
        app.closed_at = timezone.now()
        app.save()

        DecisionHistory.objects.create(
            application=app,
            actor=hr_actor,
            action='reject',
            comment=f'3 дахь буцаалт — автоматаар татгалзагдлаа. {comment}',
        )
        create_notification(
            app.user,
            f'Таны өргөдөл татгалзагдлаа: {app.app_number}',
            '3 удаа буцаагдсантай холбоотойгоор өргөдөл автоматаар татгалзагдлаа.',
        )
        log_action(hr_actor, 'APP_RETURN', f'Өргөдөл буцаасан: {app.app_number}')
        return app, True

    # Энгийн буцаалт — ажилтанд засварлах боломж олгоно
    app.status = 'returned'
    app.save()

    DecisionHistory.objects.create(
        application=app,
        actor=hr_actor,
        action='return',
        comment=comment,
    )
    create_notification(
        app.user,
        f'Таны өргөдөл буцаагдлаа: {app.app_number}',
        f'HR: {comment}',
    )
    log_action(hr_actor, 'APP_RETURN', f'Өргөдөл буцаасан: {app.app_number}')
    return app, False


def decide_application(app, director, decision, comment):
    """
    Захирал дамжуулагдсан өргөдлийг зөвшөөрөх эсвэл татгалзана.
    Зөвхөн status='forwarded' болон app.assigned_to==director үед дуудагдана (view шалгана).

    Parameters
    ----------
    app      : Application
    director : CustomUser (admin_role эрхтэй)
    decision : 'approve' | 'reject'
    comment  : str — шийдвэрийн тайлбар (татгалзах үед заавал байх ёстой)

    Returns
    -------
    tuple (Application, error_message | None)
    """
    if decision not in ('approve', 'reject'):
        return None, 'Буруу үйлдэл.'

    if decision == 'reject' and not comment.strip():
        return None, 'Татгалзахдаа тайлбар заавал бичнэ үү.'

    if decision == 'approve':
        app.status = 'approved'
        app.closed_at = timezone.now()
        app.save()

        DecisionHistory.objects.create(
            application=app, actor=director,
            action='approve', comment=comment,
        )
        create_notification(
            app.user,
            f'Таны өргөдөл зөвшөөрөгдлөө: {app.app_number}',
            'Захиргааны шийдвэр: Зөвшөөрсөн.',
        )
    else:
        # decision == 'reject'
        app.status = 'rejected'
        app.closed_at = timezone.now()
        app.save()

        DecisionHistory.objects.create(
            application=app, actor=director,
            action='reject', comment=comment,
        )
        create_notification(
            app.user,
            f'Таны өргөдөл татгалзагдлаа: {app.app_number}',
            'Захиргааны шийдвэр: Татгалзсан.',
        )

    log_action(director, 'APP_DECIDE', f'Өргөдөл шийдвэрлэсэн ({decision}): {app.app_number}')
    return app, None


# ---------------------------------------------------------------------------
# Frontend-д хэрэгтэй JSON өгөгдлүүд
# ---------------------------------------------------------------------------

def get_app_types_json():
    """
    Идэвхтэй өргөдлийн төрлүүдийг template-ийн JavaScript-д зориулж JSON болгоно.
    required_fields, instructions, requires_attachment орно.
    """
    types = {}
    for t in ApplicationType.objects.filter(is_active=True):
        types[str(t.pk)] = {
            'name': t.name,
            'requires_attachment': t.requires_attachment,
            'required_fields': t.required_fields,
            'instructions': t.instructions,
        }
    return json.dumps(types, ensure_ascii=False)


def get_recipients_json(current_user=None):
    """
    Өргөдлийн төрөл тус бүрийн боломжит шийдвэрлэгчдийн жагсаалтыг JSON болгоно.
    ApplicationType.target_department-ийн утгаар захирлуудыг шүүнэ:
        ''             → бүх захирлууд
        '__own_dept__' → ажилтантай ижил хэлтсийн захирлууд
        'ХэлтэсийнНэр' → тодорхой хэлтсийн захирлууд
    """
    from accounts.models import CustomUser

    # Нийт идэвхтэй захирлуудыг нэг л удаа татна — N+1 асуудлаас сэргийлнэ
    all_staff = list(
        CustomUser.objects.filter(role='admin_role', is_active=True)
        .order_by('last_name', 'first_name')
    )
    own_dept = current_user.department if current_user else ''
    result = {}

    for app_type in ApplicationType.objects.filter(is_active=True):
        dept = app_type.target_department

        if dept == '__own_dept__':
            # Тухайн ажилтантай ижил хэлтсийн захирлуудыг харуулна
            users = [u for u in all_staff if u.department == own_dept] if own_dept else []
        elif not dept:
            # Хоосон → бүх захирлуудыг харуулна
            users = list(all_staff)
        else:
            # Тодорхой хэлтэс заагдсан
            users = [u for u in all_staff if u.department == dept]

        result[str(app_type.pk)] = [
            {
                'id': u.pk,
                'name': u.get_full_name() or u.username,
                'dept': u.department,
                'role': u.get_role_display(),
            }
            for u in users
        ]

    return json.dumps(result, ensure_ascii=False)


def get_dept_heads_json(current_user):
    """
    Тухайн ажилтантай ижил хэлтсийн захирлуудыг JSON болгоно.
    Ажилтан хэлтэсгүй бол хоосон жагсаалт буцаана.
    """
    from accounts.models import CustomUser

    dept = current_user.department
    if not dept:
        return '[]'

    users = CustomUser.objects.filter(
        department=dept, role='admin_role', is_active=True
    ).order_by('last_name', 'first_name')

    return json.dumps([
        {
            'id': u.pk,
            'name': u.get_full_name() or u.username,
            'dept': u.department,
            'role': u.get_role_display(),
        }
        for u in users
    ], ensure_ascii=False)


# ---------------------------------------------------------------------------
# Дотоод туслах функцүүд (private)
# ---------------------------------------------------------------------------

def _notify_hr_new_application(submitter, app):
    """Шинэ өргөдөл илгээгдэхэд бүх HR-д мэдэгдэл явуулна."""
    from accounts.models import CustomUser
    name = submitter.get_full_name() or submitter.username
    for hr in CustomUser.objects.filter(role='hr', is_active=True):
        create_notification(
            hr,
            f'Шинэ өргөдөл ирлээ: {app.app_number}',
            f'{name} өргөдөл илгээлээ.',
        )


def _notify_hr_resubmit(submitter, app):
    """Буцаагдсан өргөдлийг засч дахин илгээхэд бүх HR-д мэдэгдэл явуулна."""
    from accounts.models import CustomUser
    name = submitter.get_full_name() or submitter.username
    for hr in CustomUser.objects.filter(role='hr', is_active=True):
        create_notification(
            hr,
            f'Өргөдөл дахин илгээгдлээ: {app.app_number}',
            f'{name} өргөдлийг засч дахин илгээлээ.',
        )
