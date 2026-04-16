from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification


@login_required
def notification_list_view(request):
    # Бүх мэдэгдлийг авах — уншсан/уншаагүй хоёуланг нь харуулна
    notifications = Notification.objects.filter(user=request.user)
    unread_count = notifications.filter(is_read=False).count()
    return render(request, 'notifications/list.html', {
        'notifications': notifications,
        'unread_count': unread_count,
    })


@login_required
def notification_mark_read_view(request, pk):
    # Тодорхой нэг мэдэгдлийг уншсан болгоно
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.is_read = True
    notif.save()
    return redirect('notification_list')


@login_required
def notification_mark_all_read_view(request):
    # Бүх уншаагүй мэдэгдлийг нэг дор уншсан болгоно
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect('notification_list')
