"""
Хэрэглэгчийн нэвтрэлт, профайл болон системийн админы view функцүүд.

Бизнес логик (rate limiting, dashboard статистик) нь accounts.services модульд байна.
Энд зөвхөн HTTP request/response зохицуулна.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator

from .models import CustomUser
from .forms import ProfileForm, CustomPasswordChangeForm, UserCreateForm, UserEditForm
from . import services as auth_service
from logs.utils import log_action


def sysadmin_required(view_func):
    """Зөвхөн системийн админд зориулсан декоратор."""
    from functools import wraps

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_sysadmin:
            messages.error(request, 'Энэ хуудсанд хандах эрх байхгүй.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)

    return wrapper


# ---------------------------------------------------------------------------
# Нэвтрэх / Гарах
# ---------------------------------------------------------------------------

def login_view(request):
    """
    Нэвтрэх хуудас.
    Rate limiting болон session блоклолтыг auth_service гүйцэтгэнэ.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        # Блоклогдсон эсэхийг эхлээд шалгана
        locked, remaining_minutes = auth_service.check_login_lockout(request.session)
        if locked:
            messages.error(
                request,
                f'Хэт олон удаа буруу оруулсан. {remaining_minutes} минутын дараа дахин оролдоно уу.'
            )
            return render(request, 'accounts/login.html')

        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        result   = auth_service.process_login_attempt(request, username, password)

        if result['success']:
            log_action(result['user'], 'LOGIN', f'Нэвтэрсэн: {result["user"].username}')
            return redirect('dashboard')

        if result['inactive']:
            messages.error(request, 'Таны бүртгэл идэвхгүй байна.')
        elif result['locked']:
            messages.error(
                request,
                f'Хэт олон удаа буруу оруулсан. '
                f'{result["locked_minutes"]} минутын дараа дахин оролдоно уу.'
            )
        elif result['remaining'] <= 2:
            messages.error(
                request,
                f'Хэрэглэгчийн нэр эсвэл нууц үг буруу байна. '
                f'({result["remaining"]} оролдлого үлдлээ)'
            )
        else:
            messages.error(request, 'Хэрэглэгчийн нэр эсвэл нууц үг буруу байна.')

    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    """Системээс гарна."""
    log_action(request.user, 'LOGOUT', f'Гарсан: {request.user.username}')
    logout(request)
    return redirect('login')


# ---------------------------------------------------------------------------
# Дэлгэцийн самбар
# ---------------------------------------------------------------------------

@login_required
def dashboard_view(request):
    """
    Хэрэглэгчийн эрхэд тохируулан дэлгэцийн самбар харуулна.
    Статистик болон графикийн өгөгдлийг auth_service бэлдэнэ.
    """
    context = auth_service.get_dashboard_data(request.user)
    context['user'] = request.user
    return render(request, 'dashboard.html', context)


# ---------------------------------------------------------------------------
# Профайл
# ---------------------------------------------------------------------------

@login_required
def profile_view(request):
    """Профайл харах болон засварлах."""
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профайл амжилттай шинэчлэгдлээ.')
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def change_password_view(request):
    """Нууц үг солих."""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Нууц үг амжилттай солигдлоо.')
            return redirect('profile')
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})


# ---------------------------------------------------------------------------
# Ажилтны лавлах
# ---------------------------------------------------------------------------

@login_required
def employee_directory_view(request):
    """Байгууллагын ажилтнуудын лавлах — хэлтсээр бүлэглэн харуулна."""
    q    = request.GET.get('q', '')
    dept = request.GET.get('dept', '')

    users = CustomUser.objects.filter(is_active=True).order_by(
        'department', 'last_name', 'first_name', 'username'
    )

    if q:
        users = users.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) |
            Q(username__icontains=q)   | Q(email__icontains=q) |
            Q(phone__icontains=q)
        )
    if dept:
        users = users.filter(department__icontains=dept)

    departments = (
        CustomUser.objects.filter(is_active=True)
        .exclude(department='')
        .values_list('department', flat=True)
        .distinct().order_by('department')
    )

    # Албан тушаалын зэрэглэл: захирал > хүний нөөц > ажилтан > системийн админ
    ROLE_ORDER = {'admin_role': 0, 'hr': 1, 'employee': 2, 'sysadmin': 3}

    grouped = {}
    for u in users:
        if u.department and u.department.strip():
            grouped.setdefault(u.department.strip(), []).append(u)

    for dept_name in grouped:
        grouped[dept_name].sort(
            key=lambda u: (ROLE_ORDER.get(u.role, 99), u.last_name, u.first_name)
        )

    return render(request, 'accounts/directory.html', {
        'grouped_list': sorted(grouped.items()),
        'total':        users.count(),
        'q':            q,
        'dept':         dept,
        'departments':  departments,
    })


# ---------------------------------------------------------------------------
# Системийн админы хуудсууд — хэрэглэгч удирдлага
# ---------------------------------------------------------------------------

@login_required
@sysadmin_required
def user_list_view(request):
    """Системийн бүх хэрэглэгчийн жагсаалт."""
    q    = request.GET.get('q', '')
    role = request.GET.get('role', '')
    users = CustomUser.objects.all().order_by('username')

    if q:
        users = users.filter(
            Q(username__icontains=q) | Q(first_name__icontains=q) |
            Q(last_name__icontains=q) | Q(email__icontains=q)
        )
    if role:
        users = users.filter(role=role)

    paginator = Paginator(users, 20)
    page      = paginator.get_page(request.GET.get('page'))
    return render(request, 'admin_panel/user_list.html', {
        'page_obj': page, 'q': q, 'role': role
    })


@login_required
@sysadmin_required
def user_create_view(request):
    """Шинэ хэрэглэгч үүсгэнэ."""
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            log_action(request.user, 'USER_CREATE', f'Хэрэглэгч үүсгэсэн: {user.username}')
            messages.success(request, f'"{user.username}" хэрэглэгч амжилттай үүслээ.')
            return redirect('user_list')
    else:
        form = UserCreateForm()
    return render(request, 'admin_panel/user_form.html', {
        'form': form, 'title': 'Хэрэглэгч нэмэх'
    })


@login_required
@sysadmin_required
def user_edit_view(request, pk):
    """Хэрэглэгчийн мэдээллийг засварлана."""
    user = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            log_action(request.user, 'USER_EDIT', f'Хэрэглэгч засварласан: {user.username}')
            messages.success(request, f'"{user.username}" хэрэглэгч шинэчлэгдлээ.')
            return redirect('user_list')
    else:
        form = UserEditForm(instance=user)
    return render(request, 'admin_panel/user_form.html', {
        'form': form, 'title': 'Хэрэглэгч засах', 'edit_user': user
    })


@login_required
@sysadmin_required
def user_reset_password_view(request, pk):
    """Хэрэглэгчийн нууц үгийг шинэчилнэ."""
    user = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        new_password = request.POST.get('new_password', '').strip()
        if len(new_password) < 6:
            messages.error(request, 'Нууц үг хамгийн багадаа 6 тэмдэгт байх ёстой.')
        else:
            user.set_password(new_password)
            user.save()
            log_action(request.user, 'PASSWORD_RESET', f'Нууц үг шинэчилсэн: {user.username}')
            messages.success(request, f'"{user.username}" нууц үг шинэчлэгдлээ.')
            return redirect('user_list')
    return render(request, 'admin_panel/reset_password.html', {'edit_user': user})


@login_required
@sysadmin_required
def user_bulk_action_view(request):
    """Олон хэрэглэгчийг нэгэн зэрэг идэвхжүүлэх / идэвхгүй болгох."""
    if request.method == 'POST':
        action   = request.POST.get('action')
        user_ids = request.POST.getlist('user_ids')

        if not user_ids:
            messages.warning(request, 'Хэрэглэгч сонгоогүй байна.')
            return redirect('user_list')

        # Өөрийгөө дотруулахгүй
        users = CustomUser.objects.filter(pk__in=user_ids).exclude(pk=request.user.pk)

        if action == 'activate':
            users.update(is_active=True)
            messages.success(request, f'{users.count()} хэрэглэгч идэвхжүүлэгдлээ.')
        elif action == 'deactivate':
            users.update(is_active=False)
            messages.success(request, f'{users.count()} хэрэглэгч идэвхгүй болгогдлоо.')
        else:
            messages.warning(request, 'Үйлдэл сонгоогүй байна.')

    return redirect('user_list')
