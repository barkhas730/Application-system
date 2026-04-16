from django.urls import path
from . import views

urlpatterns = [
    path('reports/', views.reports_view, name='reports'),
    path('reports/export/', views.reports_export_view, name='reports_export'),
]
