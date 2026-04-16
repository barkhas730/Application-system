from django.urls import path
from . import views

urlpatterns = [
    path('applications/', views.application_list_view, name='application_list'),
    path('applications/new/', views.application_new_view, name='application_new'),
    # Ноорогийн жагсаалт болон шууд устгах
    path('applications/drafts/', views.draft_list_view, name='draft_list'),
    path('applications/drafts/<int:pk>/delete/', views.draft_delete_view, name='draft_delete'),
    path('applications/<int:pk>/', views.application_detail_view, name='application_detail'),
    path('applications/<int:pk>/edit/', views.application_edit_view, name='application_edit'),
    path('applications/<int:pk>/cancel/', views.application_cancel_view, name='application_cancel'),
    path('applications/<int:pk>/forward/', views.application_forward_view, name='application_forward'),
    path('applications/<int:pk>/return/', views.application_return_view, name='application_return'),
    path('applications/<int:pk>/decide/', views.application_decide_view, name='application_decide'),
    path('applications/<int:pk>/pdf/', views.application_pdf_view, name='application_pdf'),
    # Хавсралт устгах — зөвхөн өргөдлийн эзэн, can_edit горимд
    path('attachments/<int:pk>/delete/', views.attachment_delete_view, name='attachment_delete'),
    path('admin-panel/types/', views.app_type_list_view, name='app_type_list'),
    path('admin-panel/types/create/', views.app_type_create_view, name='app_type_create'),
    path('admin-panel/types/<int:pk>/edit/', views.app_type_edit_view, name='app_type_edit'),
    # Өргөдлийн төрлийг устгах — PROTECT тул өргөдөл байвал алдаа гарна
    path('admin-panel/types/<int:pk>/delete/', views.app_type_delete_view, name='app_type_delete'),
]
