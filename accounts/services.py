"""
Хэрэглэгчийн нэвтрэлт болон дэлгэцийн самбарын бизнес логик (Auth Service Layer).

Нэвтрэх хязгаарлалт (rate limiting), дэлгэцийн самбарын өгөгдөл бэлдэх
зэрэг логикийг view функцүүдээс тусгаарлан энд төвлөрүүлнэ.
"""

import time
import json
from datetime import date

from django.contrib.auth import authenticate, login

# Нэвтрэх оролдлогын хязгаарлалт
MAX_LOGIN_ATTEMPTS = 5       # Хамгийн их оролдлогын тоо
LOCKOUT_MINUTES = 10        # Блоклолтын хугацаа (минутаар)


# ---------------------------------------------------------------------------
# Нэвтрэлтийн үйлчилгээ
# ---------------------------------------------------------------------------

def check_login_lockout(session):
    """
    Session-аас блоклолтын мэдээлэл уншина.
    Блоклогдоогүй бол (False, 0) буцаана.
    Блоклогдсон бол (True, үлдсэн_минут) буцаана.
    """
    now = time.time()
    lockout_until = session.get('login_lockout_until', 0)
    if lockout_until and now < lockout_until:
        remaining_minutes = int((lockout_until - now) / 60) + 1
        return True, remaining_minutes
    return False, 0


def process_login_attempt(request, username, password):
    """
    Нэвтрэх оролдлогыг боловсруулна. Session-д оролдлогын тоог хадгална.
    Амжилтгүй бол оролдлогын тоо нэмэгдэж, хязгаарт хүрэхэд блоклоно.

    Returns
    -------
    dict дараах түлхүүрүүдтэй:
        success         : bool   — нэвтрэлт амжилттай эсэх
        user            : CustomUser | None
        locked          : bool   — блоклогдсон эсэх
        remaining       : int    — үлдсэн оролдлогын тоо
        locked_minutes  : int    — блоклолтын хугацаа (минутаар)
        inactive        : bool   — хэрэглэгч идэвхгүй эсэх
    """
    now = time.time()

    user = authenticate(request, username=username, password=password)

    if user is not None:
        if user.is_active:
            # Амжилттай нэвтрэлт — session цэвэрлэнэ
            request.session.pop('login_attempts', None)
            request.session.pop('login_lockout_until', None)
            login(request, user)
            return {
                'success': True,
                'user': user,
                'locked': False,
                'remaining': MAX_LOGIN_ATTEMPTS,
                'locked_minutes': 0,
                'inactive': False,
            }
        else:
            # Бүртгэл идэвхгүй
            return {
                'success': False,
                'user': None,
                'locked': False,
                'remaining': MAX_LOGIN_ATTEMPTS,
                'locked_minutes': 0,
                'inactive': True,
            }

    # Буруу нэр/нууц үг — оролдлогын тоо нэмнэ
    attempts = request.session.get('login_attempts', 0) + 1
    request.session['login_attempts'] = attempts
    remaining = MAX_LOGIN_ATTEMPTS - attempts

    if attempts >= MAX_LOGIN_ATTEMPTS:
        # Хязгаарт хүрсэн — блоклоно
        request.session['login_lockout_until'] = now + LOCKOUT_MINUTES * 60
        request.session['login_attempts'] = 0
        return {
            'success': False,
            'user': None,
            'locked': True,
            'remaining': 0,
            'locked_minutes': LOCKOUT_MINUTES,
            'inactive': False,
        }

    return {
        'success': False,
        'user': None,
        'locked': False,
        'remaining': remaining,
        'locked_minutes': 0,
        'inactive': False,
    }


# ---------------------------------------------------------------------------
# Дэлгэцийн самбарын өгөгдөл
# ---------------------------------------------------------------------------

def get_dashboard_data(user):
    """
    Хэрэглэгчийн эрхийн түвшинд тохируулан дэлгэцийн самбарын
    статистик болон графикийн өгөгдлийг бэлдэнэ.

    Returns:
        dict — template-д шууд дамжуулах context
    """
    from applications.models import Application

    if user.is_employee:
        return _employee_dashboard(user)
    elif user.is_hr:
        return _hr_dashboard()
    elif user.is_admin_role:
        return _director_dashboard(user)
    elif user.is_sysadmin:
        return _sysadmin_dashboard()
    return {}


def _monthly_stacked(qs, months=6):
    """
    Сар бүрийн өргөдлийг статусаар задалсан stacked bar chart өгөгдөл.
    Ноорог статусыг хасна (харуулах шаардлагагүй).
    """
    today = date.today().replace(day=1)
    labels = []
    for i in range(months - 1, -1, -1):
        m = (today.month - i - 1) % 12 + 1
        y = today.year - ((i + today.month - 1) // 12)
        labels.append(f'{y}-{m:02d}')

    # Харуулах статусуудыг монгол нэр болон өнгөтэй нь тодорхойлно
    STATUS_GROUPS = [
        ('submitted',  'Илгээгдсэн',     '#3b82f6'),
        ('forwarded',  'Дамжуулагдсан',   '#06b6d4'),
        ('approved',   'Зөвшөөрсөн',      '#10b981'),
        ('rejected',   'Татгалзсан',       '#ef4444'),
        ('returned',   'Буцаагдсан',       '#f59e0b'),
        ('cancelled',  'Цуцалсан',          '#94a3b8'),
    ]
    datasets = []
    for status, label, color in STATUS_GROUPS:
        data = []
        for lbl in labels:
            y_str, m_str = lbl.split('-')
            cnt = qs.filter(
                status=status,
                created_at__year=int(y_str),
                created_at__month=int(m_str),
            ).count()
            data.append(cnt)
        # Бүх утга 0 бол энэ статусыг диаграмд оруулахгүй
        if any(d > 0 for d in data):
            datasets.append({'label': label, 'data': data, 'color': color})

    return json.dumps({'labels': labels, 'datasets': datasets}, ensure_ascii=False)


def _status_chart(qs):
    """Статусаар задалсан pie chart-д зориулсан өгөгдөл."""
    statuses = ['draft', 'submitted', 'forwarded', 'approved', 'rejected', 'returned', 'cancelled']
    labels_mn = ['Ноорог', 'Илгээгдсэн', 'Дамжуулагдсан', 'Зөвшөөрсөн', 'Татгалзсан', 'Буцаагдсан', 'Цуцалсан']
    data = [qs.filter(status=s).count() for s in statuses]
    filtered = [(l, d) for l, d in zip(labels_mn, data) if d > 0]
    if not filtered:
        return json.dumps({'labels': [], 'data': []})
    fl, fd = zip(*filtered)
    return json.dumps({'labels': list(fl), 'data': list(fd)})


def _employee_dashboard(user):
    """Ажилтны дэлгэцийн самбарын өгөгдөл."""
    from applications.models import Application

    # Ноорог-цуцалсан өргөдлийг хасна (хэзээ ч хүргүүлэгдэж байгаагүй)
    apps = Application.objects.filter(user=user).exclude(
        status='cancelled', is_draft=True
    ).order_by('-created_at')

    # Ноорог нь "бэлтгэж буй ажил" — нийт өргөдлийн тоонд ордоггүй
    submitted_apps = apps.exclude(status='draft')

    # Төрлөөр задалсан тоо
    type_counts = {}
    for app in submitted_apps:
        name = app.app_type.name
        type_counts[name] = type_counts.get(name, 0) + 1

    return {
        'my_apps': submitted_apps[:6],
        'total': submitted_apps.count(),
        'draft_count': apps.filter(status='draft').count(),
        'submitted_count': apps.filter(status='submitted').count(),
        'forwarded_count': apps.filter(status='forwarded').count(),
        'approved_count': apps.filter(status='approved').count(),
        'returned_count': apps.filter(status='returned').count(),
        'rejected_count': apps.filter(status='rejected').count(),
        'chart_monthly': _monthly_stacked(submitted_apps),
        'chart_status': _status_chart(submitted_apps),
        'chart_type': json.dumps({
            'labels': list(type_counts.keys()),
            'data': list(type_counts.values()),
        }),
    }


def _hr_dashboard():
    """HR ажилтны дэлгэцийн самбарын өгөгдөл."""
    from applications.models import Application

    # Ноорог болон ноорог-цуцалсан өргөдлийг HR-д харуулахгүй
    apps = Application.objects.exclude(status='draft').exclude(
        status='cancelled', is_draft=True
    ).order_by('-created_at')

    return {
        'pending_apps': apps.filter(status='submitted')[:10],
        'total': apps.count(),
        'submitted_count': apps.filter(status='submitted').count(),
        'forwarded_count': apps.filter(status='forwarded').count(),
        'approved_count': apps.filter(status='approved').count(),
        'rejected_count': apps.filter(status='rejected').count(),
        'chart_monthly': _monthly_stacked(apps),
        'chart_status': _status_chart(apps),
    }


def _director_dashboard(user):
    """Захирлын дэлгэцийн самбарын өгөгдөл."""
    from applications.models import Application

    # Захирал — зөвхөн forwarded/approved/rejected өргөдлийг харна
    apps = Application.objects.filter(
        assigned_to=user,
        status__in=['forwarded', 'approved', 'rejected'],
    ).order_by('-created_at')

    return {
        'pending_apps': apps.filter(status='forwarded')[:10],
        'total': apps.count(),
        'forwarded_count': apps.filter(status='forwarded').count(),
        'approved_count': apps.filter(status='approved').count(),
        'rejected_count': apps.filter(status='rejected').count(),
        'chart_monthly': _monthly_stacked(apps),
        'chart_status': _status_chart(apps),
    }


def _sysadmin_dashboard():
    """Системийн админы дэлгэцийн самбарын өгөгдөл."""
    from applications.models import Application
    from accounts.models import CustomUser

    apps = Application.objects.exclude(status='draft').exclude(
        status='cancelled', is_draft=True
    ).order_by('-created_at')

    return {
        'recent_apps': apps[:8],
        'total': apps.count(),
        'user_count': CustomUser.objects.count(),
        'active_user_count': CustomUser.objects.filter(is_active=True).count(),
        'submitted_count': apps.filter(status='submitted').count(),
        'approved_count': apps.filter(status='approved').count(),
        'chart_monthly': _monthly_stacked(apps),
        'chart_status': _status_chart(apps),
    }
