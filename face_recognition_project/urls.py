from django.contrib import admin
from django.urls import path, include  # Add 'include' import
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('face_recognition/', include('face_recognition_app.urls')),  # Include app URLs
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)