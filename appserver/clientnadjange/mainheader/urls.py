from django.urls import path
from mainheader.views import search_view

urlpatterns = [
    path('', search_view, name='search'),  # Теперь корневой путь будет вести к search_view
    path('search/', search_view, name='search'),  # Этот путь также остается
]
