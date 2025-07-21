from django.urls import path

from .ProductView import TochkaProductListView, TochkaProductHistoryCreateView, AlternativeProductListView
from .AplicationView import  ApplicationCreateView, ApplicationListView
app_name = 'home'

urlpatterns = [
    path('tochka-products/', TochkaProductListView.as_view(), name='tochka_product_list'),
    path('tochka-product-history/', TochkaProductHistoryCreateView.as_view(), name='tochka_product_history_create'),
    path('get-alternative-products/', AlternativeProductListView.as_view(), name='alternative_product_list'),
    path('create-application/', ApplicationCreateView.as_view(), name='create_application'),
    path('application-list/', ApplicationListView.as_view(), name='application_list')

]