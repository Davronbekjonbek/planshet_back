from django.urls import path, include
from .api import api_urls
from . import views

app_name = 'home'

urlpatterns = [
    path('', include(api_urls), name='api'),
    path('applications/', views.ApplicationListView.as_view(), name='application_list'),

    # Detail views
    path('<int:pk>/', views.ApplicationDetailView.as_view(), name='application_detail'),
    path('<int:pk>/detail-ajax/', views.application_detail_ajax, name='application_detail_ajax'),
    
    # Actions
    path('<int:pk>/approve/', views.approve_application, name='approve_application'),
    path('<int:pk>/reject/', views.reject_application, name='reject_application'),
    
    # Statistics
    path('statistics/', views.get_application_statistics, name='application_statistics'),
]