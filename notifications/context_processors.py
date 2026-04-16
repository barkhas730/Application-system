from .models import Notification


def unread_notifications_count(request):
    if request.user.is_authenticated:
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return {'unread_notifications_count': count}
    return {'unread_notifications_count': 0}


def draft_count(request):
    """
    Ажилтны дуусгаагүй ноорог тоог бүх template-д дамжуулна.
    Зөвхөн is_employee эрхтэй хэрэглэгчид хамаарна.
    """
    if request.user.is_authenticated and hasattr(request.user, 'is_employee') and request.user.is_employee:
        from applications.models import Application
        count = Application.objects.filter(
            user=request.user,
            status='draft',
            is_draft=True,
        ).count()
        return {'sidebar_draft_count': count}
    return {'sidebar_draft_count': 0}
