from django.db.models import Prefetch
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


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

        if not employee:
            return Tochka.objects.none()

        period_date = get_period_by_type_today()
        if not period_date:
            return Tochka.objects.none()

        ntochka_prefetch = Prefetch(
            'ntochkas',
            queryset=NTochka.objects.filter(
                is_active=True
            ).prefetch_related(
                Prefetch(
                    'products',
                    queryset=TochkaProduct.objects.filter(is_udalen=False),
                    to_attr='active_products'
                ),
                Prefetch(
                    'product_history',
                    queryset=TochkaProductHistory.objects.filter(
                        period__period=period_date.period
                    ).exclude(
                        status__in=['sotilmayapti', 'vaqtinchalik', 'obyekt_yopilgan', 'mavsumiy', 'chegirma']
                    ),
                    to_attr='completed_history'
                )
            ),
            to_attr='active_ntochkas'
        )

        return Tochka.objects.filter(
            employee=employee,
            is_active=True
        ).select_related(
            'employee',
            'district'
        ).prefetch_related(
            ntochka_prefetch
        )