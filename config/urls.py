from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('', include('applications.urls')),
    path('', include('notifications.urls')),
    path('', include('reports.urls')),
    path('', include('logs.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
