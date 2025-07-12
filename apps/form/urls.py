from django.urls import path, include
from .api import api_urls

app_name = 'home'

urlpatterns = [
    path('', include(api_urls), name='api'),
]