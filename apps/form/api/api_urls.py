from django.urls import path

from .ProductView import TochkaProductListView, TochkaProductHistoryCreateView

app_name = 'home'

urlpatterns = [
    path('tochka-products/', TochkaProductListView.as_view(), name='tochka_product_list'),
    path('tochka-product-history/', TochkaProductHistoryCreateView.as_view(), name='tochka_product_history_create'),
]