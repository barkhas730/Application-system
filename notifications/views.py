from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Notification


@login_required
def notification_list_view(request):
    notifications = Notification.objects.filter(user=request.user)
    # Хуудас нээхэд бүх уншаагүй мэдэгдлийг уншсан болгоно
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'notifications/list.html', {'notifications': notifications})


@login_required
def notification_mark_read_view(request, pk):
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.is_read = True
    notif.save()
    return redirect('notification_list')
