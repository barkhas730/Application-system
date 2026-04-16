"""
Өргөдлийн удирдлагын системийн view функцүүд.

Энэ модуль нь зөвхөн HTTP request/response зохицуулна:
маягт (form) шалгах, URL-д redirect хийх, template render хийх.
Бизнес логик нь applications.services модульд байна.
"""

import os

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import Http404

from .models import Application, ApplicationType, Attachment, DecisionHistory
from .forms import ApplicationForm, AttachmentForm, DecisionForm, ApplicationTypeForm
from . import services as app_service
from logs.utils import log_action
from accounts.views import sysadmin_required
# CustomUser-ийг application_list_view дотор ашиглах тул файлын эхэнд нэг удаа import хийнэ
from accounts.models import CustomUser


def role_required(*roles):
    """
    Тодорхой эрхтэй хэрэглэгчид л хандах боломжтой болгох декоратор.
    Нэвтрээгүй бол login хуудас руу, эрхгүй бол dashboard руу чиглүүлнэ.
    """
    from functools import wraps

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.role not in roles:
                messages.error(request, 'Энэ үйлдэл хийх эрх байхгүй.')
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


# ---------------------------------------------------------------------------
# Ноорог
# ---------------------------------------------------------------------------

@login_required
@role_required('employee')
def draft_list_view(request):
    """Ажилтны нооргийн жагсаалт — зөвхөн status='draft' өргөдлүүд."""
    drafts = Application.objects.filter(
        user=request.user,
        status='draft',
        is_draft=True,
    ).select_related('app_type').order_by('-created_at')

    return render(request, 'applications/draft_list.html', {'drafts': drafts})


@login_required
@role_required('employee')
def draft_delete_view(request, pk):
    """
    Ноорогыг DB-с бүрэн устгана (цуцлах биш).
    Зөвхөн ноорог статустай өргөдлийг устгаж болно.
    Хавсарсан файлуудыг диск дээрээс хамт устгана.
    """
    app = get_object_or_404(Application, pk=pk, user=request.user)

    # Зөвхөн ноорог статустай байвал устгаж болно
    if app.status != 'draft' or not app.is_draft:
        messages.error(request, 'Зөвхөн ноорог өргөдлийг устгаж болно.')
        return redirect('draft_list')

    if request.method == 'POST':
        # Хавсарсан файлуудыг диск дээрээс устгана
        for att in app.attachments.all():
            if att.file and os.path.isfile(att.file.path):
                os.remove(att.file.path)

        app_number = app.app_number
        app.delete()
        messages.success(request, f'Ноорог {app_number} устгагдлаа.')
        return redirect('draft_list')

    return redirect('draft_list')


# ---------------------------------------------------------------------------
# Өргөдлийн жагсаалт
# ---------------------------------------------------------------------------

@login_required
def application_list_view(request):
    """
    Хэрэглэгчийн эрхэд тохируулсан өргөдлийн жагсаалт.
    Хайлт, шүүлт, эрэмбэлэлт болон хуудасчлалтыг зохицуулна.
    """
    user = request.user
    apps = Application.objects.select_related('user', 'app_type').all()

    if user.is_employee:
        # Ноорог болон ноорог-цуцалсан өргөдлийг "Бүгд" жагсаалтаас хасна
        apps = apps.filter(user=user).exclude(status='draft').exclude(
            status='cancelled', is_draft=True
        )
    elif user.is_admin_role:
        # Захирал — HR дамжуулсны дараа харна (submitted үед харагдахгүй)
        apps = apps.filter(assigned_to=user).exclude(
            status__in=['draft', 'submitted']
        ).exclude(status='cancelled', is_draft=True)
    elif user.is_hr or user.is_sysadmin:
        # HR, sysadmin — ноорог болон ноорог-цуцалсан харагдахгүй
        apps = apps.exclude(status='draft').exclude(
            status='cancelled', is_draft=True
        )
    else:
        apps = apps.filter(user=user)

    # Шүүлтийн параметрүүд
    status     = request.GET.get('status', '')
    app_type   = request.GET.get('app_type', '')
    priority   = request.GET.get('priority', '')
    date_from  = request.GET.get('date_from', '')
    date_to    = request.GET.get('date_to', '')
    q          = request.GET.get('q', '')
    employee_name = request.GET.get('employee_name', '')
    dept       = request.GET.get('dept', '')
    sort       = request.GET.get('sort', '-created_at')

    if status:
        apps = apps.filter(status=status)
    if app_type:
        apps = apps.filter(app_type_id=app_type)
    if priority:
        apps = apps.filter(priority=priority)
    if date_from:
        apps = apps.filter(created_at__date__gte=date_from)
    if date_to:
        apps = apps.filter(created_at__date__lte=date_to)
    if q:
        apps = apps.filter(
            Q(title__icontains=q) | Q(app_number__icontains=q) | Q(description__icontains=q)
        )
    if employee_name:
        apps = apps.filter(
            Q(user__first_name__icontains=employee_name) |
            Q(user__last_name__icontains=employee_name) |
            Q(user__username__icontains=employee_name)
        )
    if dept:
        apps = apps.filter(user__department__icontains=dept)

    # Зөвшөөрөгдсөн эрэмбэлэлтийн сонголтууд
    allowed_sorts = [
        'created_at', '-created_at', 'status', '-status',
        'priority', '-priority', 'due_date', '-due_date',
        'app_number', '-app_number',
    ]
    if sort not in allowed_sorts:
        sort = '-created_at'
    apps = apps.order_by(sort)

    paginator = Paginator(apps, 15)
    page_obj  = paginator.get_page(request.GET.get('page'))

    # CustomUser нь файлын эхэнд import хийгдсэн
    departments = (
        CustomUser.objects.filter(is_active=True)
        .exclude(department='')
        .values_list('department', flat=True)
        .distinct().order_by('department')
    )

    context = {
        'page_obj': page_obj,
        'app_types': ApplicationType.objects.filter(is_active=True),
        'status_choices': Application.STATUS_CHOICES,
        'priority_choices': Application.PRIORITY_CHOICES,
        'departments': departments,
        'has_advanced': bool(employee_name or dept or date_from or date_to),
        'current_filters': {
            'status': status, 'app_type': app_type, 'priority': priority,
            'date_from': date_from, 'date_to': date_to, 'q': q, 'sort': sort,
            'employee_name': employee_name, 'dept': dept,
        },
    }
    return render(request, 'applications/list.html', context)


# ---------------------------------------------------------------------------
# Өргөдөл үүсгэх / засварлах
# ---------------------------------------------------------------------------

@login_required
@role_required('employee')
def application_new_view(request):
    """
    Шинэ өргөдөл үүсгэх.
    Service layer нь давхардсан нээлттэй өргөдөл шалгах,
    статус тохируулах, мэдэгдэл явуулах ажлыг гүйцэтгэнэ.
    """
    if request.method == 'POST':
        form  = ApplicationForm(request.POST)
        action = request.POST.get('action', 'draft')

        # Ноорог хадгалах үед гарчиг, тайлбар заавал биш
        if action == 'draft':
            form.fields['title'].required       = False
            form.fields['description'].required = False

        if form.is_valid():
            # Динамик нэмэлт талбаруудыг POST-оос цуглуулна
            extra_data  = app_service.extract_extra_fields(request.POST)
            assigned_to = app_service.get_assigned_admin(
                request.POST.get('assigned_to', '').strip()
            )

            # form.save(commit=False) — DB-д хадгалагдаагүй объект дамжуулна
            app_obj = form.save(commit=False)
            app_obj.extra_data = extra_data

            file = request.FILES.get('file')
            app_obj, error = app_service.submit_new_application(
                app=app_obj,
                user=request.user,
                assigned_to=assigned_to,
                action=action,
                file=file,
            )

            if error:
                messages.warning(request, error)
                return render(request, 'applications/form.html', {
                    'form': form,
                    'app_types_json':  app_service.get_app_types_json(),
                    'recipients_json': app_service.get_recipients_json(request.user),
                    'dept_heads_json': app_service.get_dept_heads_json(request.user),
                })

            if action == 'submit':
                messages.success(request, f'Өргөдөл {app_obj.app_number} амжилттай илгээгдлээ.')
            else:
                messages.success(request, f'Өргөдөл {app_obj.app_number} ноорог хэлбэрээр хадгалагдлаа.')

            return redirect('application_detail', pk=app_obj.pk)
    else:
        form = ApplicationForm()

    return render(request, 'applications/form.html', {
        'form':            form,
        'app_types_json':  app_service.get_app_types_json(),
        'recipients_json': app_service.get_recipients_json(request.user),
        'dept_heads_json': app_service.get_dept_heads_json(request.user),
    })


@login_required
def application_detail_view(request, pk):
    """
    Өргөдлийн дэлгэрэнгүй мэдээлэл.
    Хэрэглэгчийн эрхэд тохируулан харах боломжийг шалгана.
    """
    app  = get_object_or_404(Application, pk=pk)
    user = request.user

    # Ажилтан зөвхөн өөрийн өргөдлийг харна
    if user.is_employee and app.user != user:
        messages.error(request, 'Энэ өргөдлийг харах эрх байхгүй.')
        return redirect('application_list')

    # Ноорог өргөдлийг зөвхөн эзэн нь харна
    if app.status == 'draft' and app.user != user:
        messages.error(request, 'Ноорог өргөдлийг харах эрх байхгүй.')
        return redirect('application_list')

    # Захирал — зөвхөн forwarded болсон, өөрт хуваарилагдсан өргөдлийг харна
    if user.is_admin_role and (app.assigned_to != user or app.status == 'submitted'):
        messages.error(request, 'Энэ өргөдлийг харах эрх байхгүй.')
        return redirect('application_list')

    history     = app.history.select_related('actor').order_by('created_at')
    attachments = app.attachments.all()
    extra_display = app_service.build_extra_display(app.extra_data)

    return render(request, 'applications/detail.html', {
        'app':          app,
        'history':      history,
        'attachments':  attachments,
        'extra_display': extra_display,
    })


@login_required
@role_required('employee')
def application_edit_view(request, pk):
    """Буцаагдсан / ноорог өргөдлийг засварлаж дахин илгээх."""
    app = get_object_or_404(Application, pk=pk, user=request.user)

    if not app.can_edit:
        messages.error(request, 'Энэ өргөдлийг засах боломжгүй.')
        return redirect('application_detail', pk=pk)

    if request.method == 'POST':
        form   = ApplicationForm(request.POST, instance=app)
        action = request.POST.get('action', 'draft')

        if action == 'draft':
            form.fields['title'].required       = False
            form.fields['description'].required = False

        if form.is_valid():
            extra_data  = app_service.extract_extra_fields(request.POST)
            assigned_to = app_service.get_assigned_admin(
                request.POST.get('assigned_to', '').strip()
            )

            app_obj = form.save(commit=False)
            app_obj.extra_data = extra_data

            file = None
            if request.FILES.get('file'):
                uploaded_file = request.FILES['file']
                if uploaded_file.size > app_service.MAX_FILE_SIZE:
                    messages.warning(request, 'Хавсралт файл 10МБ-аас хэтэрсэн тул хавсаргагдсангүй.')
                else:
                    file = uploaded_file

            app_service.resubmit_application(
                app=app_obj,
                user=request.user,
                assigned_to=assigned_to,
                action=action,
                file=file,
            )

            if action == 'submit':
                messages.success(request, 'Өргөдөл дахин илгээгдлээ.')
            else:
                messages.success(request, 'Өргөдөл хадгалагдлаа.')

            return redirect('application_detail', pk=app_obj.pk)
    else:
        form = ApplicationForm(instance=app)

    return render(request, 'applications/form.html', {
        'form':            form,
        'attachment_form': AttachmentForm(),
        'app':             app,
        'app_types_json':  app_service.get_app_types_json(),
        'recipients_json': app_service.get_recipients_json(request.user),
        'dept_heads_json': app_service.get_dept_heads_json(request.user),
    })


@login_required
def attachment_delete_view(request, pk):
    """
    Өргөдлийн хавсралтыг устгана.
    Зөвхөн өргөдлийн эзэн нь, засах боломжтой үед (returned/draft) устгаж болно.
    """
    att = get_object_or_404(Attachment, pk=pk)
    app = att.application

    # Зөвхөн өргөдлийн эзэн нь өөрийн хавсралтыг устгаж болно
    if app.user != request.user:
        messages.error(request, 'Энэ хавсралтыг устгах эрх байхгүй.')
        return redirect('application_detail', pk=app.pk)

    # Зөвхөн засварлах боломжтой горимд устгана (returned эсвэл draft)
    if not app.can_edit:
        messages.error(request, 'Одоогийн горимд хавсралт устгах боломжгүй.')
        return redirect('application_detail', pk=app.pk)

    if request.method == 'POST':
        if att.file and os.path.isfile(att.file.path):
            os.remove(att.file.path)
        att.delete()
        messages.success(request, f'Хавсралт "{att.file_name}" устгагдлаа.')
        return redirect('application_edit', pk=app.pk)

    return redirect('application_edit', pk=app.pk)


# ---------------------------------------------------------------------------
# Workflow үйлдлүүд
# ---------------------------------------------------------------------------

@login_required
@role_required('employee')
def application_cancel_view(request, pk):
    """Ажилтан өөрийн өргөдлийг цуцална."""
    app = get_object_or_404(Application, pk=pk, user=request.user)

    if not app.can_cancel:
        messages.error(request, 'Энэ өргөдлийг цуцлах боломжгүй.')
        return redirect('application_detail', pk=pk)

    if request.method == 'POST':
        app_service.cancel_application(app=app, actor=request.user)
        messages.success(request, 'Өргөдөл цуцлагдлаа.')
        return redirect('application_list')

    return render(request, 'applications/confirm_cancel.html', {'app': app})


@login_required
@role_required('hr')
def application_forward_view(request, pk):
    """HR ажилтан өргөдлийг захиргаанд дамжуулна."""
    app = get_object_or_404(Application, pk=pk)

    if app.status != 'submitted':
        messages.error(request, 'Зөвхөн "Илгээгдсэн" өргөдлийг дамжуулах боломжтой.')
        return redirect('application_detail', pk=pk)

    from accounts.models import CustomUser
    admin_users = CustomUser.objects.filter(
        role='admin_role', is_active=True
    ).order_by('last_name', 'first_name')

    if request.method == 'POST':
        assigned_to_id = request.POST.get('assigned_to', '').strip()

        if not assigned_to_id:
            messages.error(request, 'Хариуцах захирал / ахлах ажилтаныг заавал сонгоно уу.')
            return render(request, 'applications/action_confirm.html', {
                'app': app, 'action': 'forward',
                'action_label': 'Захиргаанд дамжуулах',
                'admin_users': admin_users,
            })

        assigned_admin = app_service.get_assigned_admin(assigned_to_id)
        if assigned_admin is None:
            messages.error(request, 'Буруу захирал сонгосон байна.')
            return redirect('application_detail', pk=pk)

        comment = request.POST.get('comment', '').strip()
        app_service.forward_application(
            app=app, hr_actor=request.user,
            assigned_admin=assigned_admin, comment=comment,
        )
        messages.success(
            request,
            f'Өргөдөл {assigned_admin.get_full_name() or assigned_admin.username} захиралд дамжуулагдлаа.'
        )
        return redirect('application_list')

    return render(request, 'applications/action_confirm.html', {
        'app': app, 'action': 'forward',
        'action_label': 'Захиргаанд дамжуулах',
        'admin_users': admin_users,
    })


@login_required
@role_required('hr')
def application_return_view(request, pk):
    """
    HR ажилтан өргөдлийг ажилтанд буцаана.
    3 дахь буцаалтад автоматаар татгалзана.
    """
    app = get_object_or_404(Application, pk=pk)

    if app.status != 'submitted':
        messages.error(request, 'Зөвхөн "Илгээгдсэн" өргөдлийг буцаах боломжтой.')
        return redirect('application_detail', pk=pk)

    if request.method == 'POST':
        form = DecisionForm(request.POST)
        if form.is_valid():
            comment = form.cleaned_data['comment']
            _, auto_rejected = app_service.return_application(
                app=app, hr_actor=request.user, comment=comment
            )
            if auto_rejected:
                messages.warning(request, '3 дахь буцаалт — өргөдөл автоматаар татгалзагдлаа.')
            else:
                messages.success(request, 'Өргөдөл буцаагдлаа.')
            return redirect('application_list')
    else:
        form = DecisionForm()

    return render(request, 'applications/action_confirm.html', {
        'app': app, 'action': 'return',
        'action_label': 'Буцаах', 'form': form,
    })


@login_required
@role_required('admin_role')
def application_decide_view(request, pk):
    """Захирал дамжуулагдсан өргөдлийг зөвшөөрөх эсвэл татгалзана."""
    app = get_object_or_404(Application, pk=pk)

    if app.assigned_to != request.user:
        messages.error(request, 'Энэ өргөдлийг шийдвэрлэх эрх байхгүй.')
        return redirect('application_list')

    if app.status != 'forwarded':
        messages.error(request, 'Зөвхөн "Дамжуулагдсан" өргөдлийг шийдвэрлэх боломжтой.')
        return redirect('application_detail', pk=pk)

    if request.method == 'POST':
        decision = request.POST.get('decision')
        comment  = request.POST.get('comment', '')

        _, error = app_service.decide_application(
            app=app, director=request.user,
            decision=decision, comment=comment,
        )

        if error:
            messages.error(request, error)
            return render(request, 'applications/action_confirm.html', {
                'app': app, 'action': 'decide',
                'action_label': 'Шийдвэрлэх',
                'form': DecisionForm(request.POST),
            })

        if decision == 'approve':
            messages.success(request, 'Өргөдөл зөвшөөрөгдлөө.')
        else:
            messages.warning(request, 'Өргөдөл татгалзагдлаа.')

        return redirect('application_list')

    return render(request, 'applications/action_confirm.html', {
        'app': app, 'action': 'decide',
        'action_label': 'Шийдвэрлэх', 'form': DecisionForm(),
    })


@login_required
def application_pdf_view(request, pk):
    """Өргөдлийн PDF загвар харуулна (browser print-to-PDF ашиглана)."""
    app  = get_object_or_404(Application, pk=pk)
    user = request.user

    # Ажилтан зөвхөн өөрийн өргөдлийн PDF авна
    if user.is_employee and app.user != user:
        raise Http404

    # Ажилтанд зөвхөн зөвшөөрөгдсөн өргөдлийн PDF боломжтой
    if user.is_employee and app.status != 'approved':
        messages.error(request, 'Зөвхөн зөвшөөрөгдсөн өргөдлийн PDF авах боломжтой.')
        return redirect('application_detail', pk=pk)

    history       = app.history.select_related('actor').order_by('created_at')
    extra_display = app_service.build_extra_display(app.extra_data)

    return render(request, 'applications/pdf_template.html', {
        'app':          app,
        'history':      history,
        'extra_display': extra_display,
    })


# ---------------------------------------------------------------------------
# Системийн админ: өргөдлийн төрлийн удирдлага
# ---------------------------------------------------------------------------

@login_required
@sysadmin_required
def app_type_list_view(request):
    """Өргөдлийн бүх төрлийн жагсаалт."""
    types = ApplicationType.objects.all().order_by('name')
    return render(request, 'admin_panel/app_type_list.html', {'types': types})


@login_required
@sysadmin_required
def app_type_create_view(request):
    """Шинэ өргөдлийн төрөл үүсгэнэ."""
    if request.method == 'POST':
        import json as _json
        form = ApplicationTypeForm(request.POST)
        if form.is_valid():
            # required_fields-ийг hidden input-ээс JSON хэлбэрт авна (form field биш)
            t   = form.save(commit=False)
            raw = request.POST.get('required_fields_json', '[]').strip()
            try:
                t.required_fields = _json.loads(raw) if raw else []
            except (_json.JSONDecodeError, ValueError):
                t.required_fields = []
            t.save()
            log_action(request.user, 'TYPE_CREATE', f'Өргөдлийн төрөл үүсгэсэн: {t.name}')
            messages.success(request, f'"{t.name}" төрөл үүслээ.')
            return redirect('app_type_list')
    else:
        form = ApplicationTypeForm()

    return render(request, 'admin_panel/app_type_form.html', {
        'form': form,
        'title': 'Төрөл нэмэх',
        'existing_fields_json': '[]',
    })


@login_required
@sysadmin_required
def app_type_edit_view(request, pk):
    """Өргөдлийн төрлийг засварлана."""
    import json as _json
    t = get_object_or_404(ApplicationType, pk=pk)

    if request.method == 'POST':
        form = ApplicationTypeForm(request.POST, instance=t)
        if form.is_valid():
            obj = form.save(commit=False)
            raw = request.POST.get('required_fields_json', '').strip()
            try:
                obj.required_fields = _json.loads(raw) if raw else []
            except (_json.JSONDecodeError, ValueError):
                obj.required_fields = []
            obj.save()
            log_action(request.user, 'TYPE_EDIT', f'Өргөдлийн төрөл засварласан: {t.name}')
            messages.success(request, f'"{t.name}" төрөл шинэчлэгдлээ.')
            return redirect('app_type_list')
    else:
        form = ApplicationTypeForm(instance=t)

    return render(request, 'admin_panel/app_type_form.html', {
        'form':  form,
        'title': 'Төрөл засах',
        'edit_type': t,
        # Одоогийн талбарын тодорхойлолтыг JSON болгож template-д дамжуулна
        'existing_fields_json': _json.dumps(t.required_fields or [], ensure_ascii=False),
    })


@login_required
@sysadmin_required
def app_type_delete_view(request, pk):
    """
    Өргөдлийн төрлийг устгана.
    PROTECT тул тухайн төрлийг ашигласан өргөдөл байвал устгахгүй — алдаа харуулна.
    """
    t = get_object_or_404(ApplicationType, pk=pk)

    if request.method == 'POST':
        from django.db.models import ProtectedError
        try:
            name = t.name
            t.delete()
            log_action(request.user, 'TYPE_DELETE', f'Өргөдлийн төрөл устгасан: {name}')
            messages.success(request, f'"{name}" төрөл устгагдлаа.')
        except ProtectedError:
            count = t.application_set.count()
            messages.error(
                request,
                f'"{t.name}" төрлийг {count} өргөдөл ашиглаж байгаа тул устгах боломжгүй. '
                f'Эхлээд тухайн өргөдлүүдийг шийдвэрлэж эсвэл идэвхгүй болгоно уу.'
            )
        return redirect('app_type_list')

    app_count = t.application_set.count()
    return render(request, 'admin_panel/app_type_confirm_delete.html', {
        'type':      t,
        'app_count': app_count,
    })
