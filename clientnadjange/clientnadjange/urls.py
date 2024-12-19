

from django.contrib import admin
from django.urls import path, include  # Импортируем include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('mainheader.urls')),  # Подключаем URL-адреса приложения
]
