from django.urls import path

from .LoginView import views as login_views
from .TochkaView import views as tochka_views

app_name = 'home'

urlpatterns = [
    path('login/', login_views.LoginView.as_view(), name='login'),
    path('tochka-list/', tochka_views.TochkaListView.as_view(), name='tochka-list'),
]