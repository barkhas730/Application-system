from .models import SystemLog


def log_action(user, action, target, request=None):
    ip = None
    if request:
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            ip = x_forwarded.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
    SystemLog.objects.create(user=user, action=action, target=target, ip_address=ip)
