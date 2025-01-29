from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('messages_app.urls')),  # Include app URLs under /api/
]

