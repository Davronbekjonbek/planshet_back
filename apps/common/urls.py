from django.urls import path
from . import views

app_name = 'monitoring'

urlpatterns = [
    # Main dashboard view
    path('', views.MonitoringDashboardView.as_view(), name='dashboard'),
    
    # Product detail view
    path('product/<int:pk>/', views.ProductHistoryDetailView.as_view(), name='product_detail'),
    
    # Region comparison view
    path('regions/', views.RegionMonitoringView.as_view(), name='region_monitoring'),

    
    # Export data
    path('export/excel/', views.export_to_excel, name='export_excel'),
    path('export/csv/', views.export_to_csv, name='export_csv'),
]