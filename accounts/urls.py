from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('', RedirectView.as_view(pattern_name='login', permanent=False), name='home'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/change-password/', views.change_password_view, name='change_password'),
    path('directory/', views.employee_directory_view, name='employee_directory'),
    path('admin-panel/users/', views.user_list_view, name='user_list'),
    path('admin-panel/users/create/', views.user_create_view, name='user_create'),
    path('admin-panel/users/<int:pk>/edit/', views.user_edit_view, name='user_edit'),
    path('admin-panel/users/<int:pk>/reset-password/', views.user_reset_password_view, name='user_reset_password'),
    path('admin-panel/users/bulk/', views.user_bulk_action_view, name='user_bulk_action'),
]
