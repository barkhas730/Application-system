"""
Тайлангийн бизнес логик (Report Service Layer).

Хэрэглэгчийн эрхэд тохируулан өргөдлийн queryset шүүх,
статистик болон графикийн өгөгдөл тооцоолох логикийг
view функцүүдээс тусгаарлан энд төвлөрүүлнэ.
"""

import json
from datetime import date
from django.db.models import Count

from applications.models import Application

# Статусын монгол нэрийн толь бичиг
STATUS_MN = {
    'submitted':  'Илгээгдсэн',
    'forwarded':  'Дамжуулагдсан',
    'approved':   'Зөвшөөрсөн',
    'rejected':   'Татгалзсан',
    'returned':   'Буцаагдсан',
    'cancelled':  'Цуцалсан',
}

# Excel export-т хэрэглэх орчуулгын хүснэгт
STATUS_MAP_EXCEL = {
    'draft':      'Ноорог',
    'submitted':  'Илгээгдсэн',
    'forwarded':  'Дамжуулагдсан',
    'approved':   'Зөвшөөрсөн',
    'rejected':   'Татгалзсан',
    'returned':   'Буцаагдсан',
    'cancelled':  'Цуцалсан',
}

PRIORITY_MAP_EXCEL = {
    'urgent': 'Маш яаралтай',
    'high':   'Яаралтай',
    'normal': 'Энгийн',
}


def get_report_queryset(user, date_from='', date_to='', dept=''):
    """
    Хэрэглэгчийн эрхэд тохируулан тайлангийн queryset буцаана.

    Дүрмүүд:
    - Захирал (admin_role): зөвхөн өөрт дамжуулагдсан forwarded/approved/rejected өргөдлүүд
    - HR / sysadmin: ноорог болон ноорог-цуцалсан өргөдлийг хасна

    Parameters
    ----------
    user      : CustomUser
    date_from : str 'YYYY-MM-DD' | '' — шүүлтийн эхлэх огноо
    date_to   : str 'YYYY-MM-DD' | '' — шүүлтийн дуусах огноо
    dept      : str | '' — хэлтсийн нэрээр шүүнэ (хэсэгчлэн тохируулах)

    Returns
    -------
    QuerySet[Application]
    """
    if user.is_admin_role:
        # Захирал — зөвхөн forwarded/approved/rejected өргөдлийг харна
        apps = Application.objects.filter(
            assigned_to=user,
            status__in=['forwarded', 'approved', 'rejected'],
        )
    else:
        # HR / sysadmin — ноорог болон ноорог-цуцалсан өргөдлийг хасна
        apps = Application.objects.exclude(status='draft').exclude(
            status='cancelled', is_draft=True
        )

    apps = apps.select_related('user', 'app_type')

    if date_from:
        apps = apps.filter(created_at__date__gte=date_from)
    if date_to:
        apps = apps.filter(created_at__date__lte=date_to)
    if dept:
        apps = apps.filter(user__department__icontains=dept)

    return apps


def get_report_stats(apps):
    """
    Queryset-ийн үндсэн статистикийг тооцоолно.

    Returns
    -------
    dict дараах түлхүүрүүдтэй:
        total, approved, rejected, pending, returned, approval_rate
    """
    total = apps.count()
    approved = apps.filter(status='approved').count()
    rejected = apps.filter(status='rejected').count()
    pending = apps.filter(status__in=['submitted', 'forwarded']).count()
    returned = apps.filter(status='returned').count()
    approval_rate = round(approved / total * 100) if total > 0 else 0

    return {
        'total': total,
        'approved': approved,
        'rejected': rejected,
        'pending': pending,
        'returned': returned,
        'approval_rate': approval_rate,
    }


def get_chart_data(apps):
    """
    Тайлангийн хуудасны графикт зориулсан өгөгдлийг JSON болгоно.

    Returns
    -------
    dict дараах түлхүүрүүдтэй (бүгд JSON string):
        status_labels, status_counts
        type_labels, type_counts
        dept_labels, dept_counts
        month_labels, month_counts
    """
    # Төлөвийн задаргаа
    status_rows = apps.values('status').annotate(count=Count('id')).order_by('-count')
    status_labels = [STATUS_MN.get(d['status'], d['status']) for d in status_rows]
    status_counts = [d['count'] for d in status_rows]

    # Өргөдлийн төрлийн задаргаа
    type_rows = apps.values('app_type__name').annotate(count=Count('id')).order_by('-count')
    type_labels = [d['app_type__name'] or 'Тодорхойгүй' for d in type_rows]
    type_counts = [d['count'] for d in type_rows]

    # Хэлтсийн задаргаа (хамгийн их 12 хэлтэс)
    dept_rows = (
        apps.filter(user__department__isnull=False)
        .exclude(user__department='')
        .values('user__department')
        .annotate(count=Count('id'))
        .order_by('-count')[:12]
    )
    dept_labels = [d['user__department'] for d in dept_rows]
    dept_counts = [d['count'] for d in dept_rows]

    # Сарын явц — сүүлийн 6 сар
    today = date.today().replace(day=1)
    month_labels, month_counts = [], []
    for i in range(5, -1, -1):
        m = (today.month - i - 1) % 12 + 1
        y = today.year - ((i + today.month - 1) // 12)
        month_labels.append(f'{y}-{m:02d}')
        month_counts.append(apps.filter(created_at__year=y, created_at__month=m).count())

    return {
        'status_labels': json.dumps(status_labels, ensure_ascii=False),
        'status_counts': json.dumps(status_counts),
        'type_labels':   json.dumps(type_labels, ensure_ascii=False),
        'type_counts':   json.dumps(type_counts),
        'dept_labels':   json.dumps(dept_labels, ensure_ascii=False),
        'dept_counts':   json.dumps(dept_counts),
        'month_labels':  json.dumps(month_labels),
        'month_counts':  json.dumps(month_counts),
    }
