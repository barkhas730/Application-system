from django.urls import path
from . import views

urlpatterns = [
    path('admin-panel/logs/', views.log_list_view, name='log_list'),
]
