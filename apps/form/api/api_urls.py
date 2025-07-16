from django.urls import path

from .ProductView import TochkaProductListView, TochkaProductHistoryCreateView, AlternativeProductListView

app_name = 'home'

urlpatterns = [
    path('tochka-products/', TochkaProductListView.as_view(), name='tochka_product_list'),
    path('tochka-product-history/', TochkaProductHistoryCreateView.as_view(), name='tochka_product_history_create'),
    path('get-alternative-products/', AlternativeProductListView.as_view(), name='alternative_product_list')
]