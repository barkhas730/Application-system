from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import SystemLog, ACTION_LABELS


def sysadmin_required(view_func):
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_sysadmin:
            messages.error(request, 'Энэ хуудсанд хандах эрх байхгүй.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@sysadmin_required
def log_list_view(request):
    logs = SystemLog.objects.select_related('user').all()
    q = request.GET.get('q', '')
    action = request.GET.get('action', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    if q:
        logs = logs.filter(Q(target__icontains=q) | Q(user__username__icontains=q))
    if action:
        logs = logs.filter(action=action)
    if date_from:
        logs = logs.filter(created_at__date__gte=date_from)
    if date_to:
        logs = logs.filter(created_at__date__lte=date_to)

    paginator = Paginator(logs, 30)
    page_obj = paginator.get_page(request.GET.get('page'))

    # Dropdown-д ACTION_LABELS-с бүх боломжит үйлдлийг харуулна (DB-д бүртгэгдсэн эсэхийг үл харгалзан)
    action_choices = list(ACTION_LABELS.items())

    return render(request, 'admin_panel/log_list.html', {
        'page_obj': page_obj,
        'q': q,
        'action': action,
        'date_from': date_from,
        'date_to': date_to,
        'action_choices': action_choices,
    })
