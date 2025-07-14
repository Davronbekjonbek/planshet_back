from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.response import Response
from rest_framework import status

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from ..utils import get_product_by_uuid, get_period_by_type_today
from ...models import TochkaProduct

from .serializers import TochkaProductSerializer, TochkaProductHistorySerializer

from apps.home.api.utils import get_employee_by_uuid, get_ntochka_by_uuid


class TochkaProductListView(ListAPIView):
    """
    ListAPIView View for listing Tochka Products.
    """
    serializer_class = TochkaProductSerializer
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
                'X-Rasta-UUID',
                openapi.IN_HEADER,
                description="Rasta UUID (query parameter)",
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
        rasta_uuid = req.META.get('HTTP_X_RASTA_UUID')
        print(uuid, rasta_uuid)
        employee = get_employee_by_uuid(uuid)
        ntochka = get_ntochka_by_uuid(rasta_uuid)
        if employee and ntochka:
            return TochkaProduct.objects.filter(ntochka=ntochka)
        return TochkaProduct.objects.none()


class TochkaProductHistoryCreateView(CreateAPIView):
    """
    CreateAPIView View for creating Tochka Product History.
    """
    serializer_class = TochkaProductHistorySerializer

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
                'X-Product-UUID',
                openapi.IN_HEADER,
                description="Product UUID (query parameter)",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'X-Rasta-UUID',
                openapi.IN_HEADER,
                description="Rasta UUID (query parameter)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ]
    )
    def post(self, request, *args, **kwargs):
        uuid = request.META.get('HTTP_X_USER_UUID')
        product_uuid = request.META.get('HTTP_X_PRODUCT_UUID')
        rasta_uuid = request.META.get('HTTP_X_RASTA_UUID')

        employee = get_employee_by_uuid(uuid)
        ntochka = get_ntochka_by_uuid(rasta_uuid)
        product = get_product_by_uuid(product_uuid)
        period_type = request.data.get('period_type')
        period = get_period_by_type_today(period_type)
        if not employee or not ntochka or not product:
            return Response({"detail": "Xodim, NTochka yoki Mahsulot topilmadi."}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data.copy()
        data['employee'] = employee.id
        data['ntochka'] = ntochka.id
        data['hudud'] = ntochka.hudud.id
        data['product'] = product.id
        data['period'] = period.id
        ntochka_product = TochkaProduct.objects.filter(ntochka=ntochka, product=product).first()
        print(data)

        serializer = self.get_serializer(data=data)
        print(serializer.is_valid())
        if serializer.is_valid():
            serializer.save()
            data = serializer.data
            ntochka_product.previous_price = ntochka_product.last_price
            ntochka_product.last_price = data['price']
            ntochka_product.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)