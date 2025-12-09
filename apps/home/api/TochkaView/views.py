from django.db.models import Prefetch
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from django.db.models import Q

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.generics import ListAPIView

from apps.form.api.utils import get_period_by_type_today
from apps.form.models import TochkaProduct, TochkaProductHistory
from ...models import Tochka, NTochka

from .serializers import TochkaSerializer

from ..utils import get_employee_by_uuid


class TochkaListView(ListAPIView):
    """
    Optimized ListAPIView for Tochka objects.
    """
    serializer_class = TochkaSerializer
    pagination_class = None

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'X-User-UUID',
                openapi.IN_HEADER,
                description="Xodim UUID raqami (header orqali)",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'weekly_type',
                openapi.IN_QUERY,
                description="Davr turi (masalan: 'weekly', 'monthly')",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'product_type',
                openapi.IN_QUERY,
                description="Mahsulot turi (masalan: 'food', 'non-food', 'service')",
                type=openapi.TYPE_STRING,
                required=False
            )     
        ]   
    )
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_queryset(self):
        req = self.request
        uuid = req.META.get('HTTP_X_USER_UUID')
        employee = get_employee_by_uuid(uuid)
        _product_type = req.GET.get('obyekt_type', None)
        product_type = {'food': '1', 'nofood': '2', 'services': '3'}.get(_product_type, '1')
        _weekly_type = req.GET.get('weekly_type', 1)
        weekly_type = 1 if _weekly_type == 'weekly' else 2
        if not employee:
            return Tochka.objects.none()


        period_date = get_period_by_type_today(_weekly_type)
        if not period_date:
            return Tochka.objects.none()

        base_query = Q(
            Q(weekly_type=weekly_type) | Q(weekly_type=3),  # 3 is 'bari' type
            employee=employee,
            is_active=True
        )

        ntochka_query = Q(
            Q(weekly_type=weekly_type) | Q(weekly_type=3),
            is_active=True
        )

        tochka_product_query = Q(
            is_udalen=False,
            is_weekly=_weekly_type == 'weekly',
        )
        if product_type and weekly_type == 2:   # bu yerda faqat oylik bolgandagina filter qilinadi product type boyicha aks holda bolsa haftalikka tegishli bolga barcha rastalar korilishi kerak
            ntochka_query &= Q(product_type__contains=product_type)

        if weekly_type == 2 and product_type:
            base_query &= Q(product_type__contains=product_type)
            tochka_product_query &= Q(product__category__product_type=int(product_type))
        ntochka_prefetch = Prefetch(
            'ntochkas',
            queryset=NTochka.objects.filter(
                ntochka_query
            ).only(
                'id', 'uuid', 'name', 'hudud_id', 'is_active', 'in_proccess'
            ).prefetch_related(
                Prefetch(
                    'products',
                    queryset=TochkaProduct.objects.filter(
                        tochka_product_query
                    ).only(
                        'id', 'product_id', 'ntochka_id', 'last_price', 'miqdor', 'is_active'
                    ),
                    to_attr='active_products'
                ),
                Prefetch(
                    'product_history',
                    queryset=TochkaProductHistory.objects.filter(
                        period__period=period_date.period,
                        product__category__product_type=int(product_type)

                    ).exclude(
                        status__in=['sotilmayapti', 'vaqtinchalik', 'obyekt_yopilgan', 'mavsumiy', 'chegirma']
                    ).only('id', 'ntochka_id', 'status'),
                    to_attr='completed_history'
                )
            ),
            to_attr='active_ntochkas'
        )

        return Tochka.objects.filter(base_query).select_related(
            'employee',
            'district'
        ).only(
            'id', 'uuid', 'name', 'icon', 'address', 'in_proccess',
            'lat', 'lon', 'employee_id', 'district_id', 'is_active'
        ).prefetch_related(
            ntochka_prefetch
        )