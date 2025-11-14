from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.db.models import Prefetch, Q

from ..utils import get_product_by_uuid, get_period_by_type_today, get_tochka_product_by_id
from ...models import Application, TochkaProduct, Product, TochkaProductHistory

from .serializers import TochkaProductSerializer, TochkaProductHistorySerializer, ProductSerializer, \
    ProductListSerializer

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
            ),
            openapi.Parameter(
                'weekly_type',
                openapi.IN_QUERY,
                description="Weekly type (1: weekly, 2: monthly, 3: all)",
                type=openapi.TYPE_BOOLEAN,
                required=True
            ),
            openapi.Parameter(
                'obyekt_type',
                openapi.IN_QUERY,
                description="Product type (1: food, 2: non-food, 3: service)",
                type=openapi.TYPE_STRING,
                required=True
            ),
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
        print(f"UUID: {uuid}, Rasta UUID: {rasta_uuid}")
        in_process = req.query_params.get('in_proccess', 'false').lower() == 'true'
        period_type = req.GET.get('period_type', 'weekly')
        is_weekly = period_type == 'weekly'
        _product_type = req.GET.get('obyekt_type', None)
        product_type = {'food': '1', 'nofood': '2', 'services': '3'}.get(_product_type, '1')

        employee = get_employee_by_uuid(uuid)
        ntochka = get_ntochka_by_uuid(rasta_uuid)
        qs = None
        query = Q(
            ntochka=ntochka,
            is_active=True,
            is_weekly=is_weekly,
        )
        if not is_weekly:
            query &= Q(product__category__product_type=product_type)
        print(f"Employee: {employee}, NTochka: {ntochka}, In process: {in_process}, Period type: {period_type}, Obyekt type: {product_type}",f"Query: {query}")
        if employee and ntochka:
            current_period = get_period_by_type_today(period_type=period_type)
            print(f"Current Period: {current_period}", period_type)
            history_prefetch = Prefetch(
                'history', 
                queryset=TochkaProductHistory.objects.filter(
                    period__period=current_period,
                    is_active=True
                ).select_related('tochka_product', 'period', 'employee'),
                to_attr='current_history'
            )

            qs = TochkaProduct.objects.filter(
                query
            ).select_related(
                'product',
                'ntochka',
                'hudud',
                'product__category',
                'product__unit'
            ).prefetch_related(
                history_prefetch
            )
        
        print(f"Query count: {len(connection.queries)}")
        return qs


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
                'X-Tochka-Product-ID',
                openapi.IN_HEADER,
                description="Tochka Product ID (header orqali)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ]
    )
    def post(self, request, *args, **kwargs):
        uuid = request.META.get('HTTP_X_USER_UUID')
        tochka_product_id = request.META.get('HTTP_X_TOCHKA_PRODUCT_ID')
        print(f"UUID: {uuid}, Tochka Product ID: {tochka_product_id}")
        employee = get_employee_by_uuid(uuid)
        tochka_product = get_tochka_product_by_id(tochka_product_id)
        period_type = request.data.get('period_type')
        print(f"Employee: {employee}, Tochka Product: {tochka_product}, Period Type: {period_type}")
        period = get_period_by_type_today(period_type)
        
        data = request.data.copy()
        data['employee'] = employee.id
        data['ntochka'] = tochka_product.ntochka.id
        data['hudud'] = tochka_product.hudud.id
        data['product'] = tochka_product.product.id
        data['tochka_product'] = tochka_product.id
        data['period'] = period.id
        print(f"Data: {data}")
        # Get product status
        product_status = data.get('status')
        # Handle alternative product if status is 'sotilmayapti'
        if product_status == 'sotilmayapti':
            alternative_data = data.get('alternative_product')
            print(alternative_data)
            alternative_product_uuid = alternative_data.get('uuid')
            alternative_product_price = alternative_data.get('price')
            alternative_product_quantity = alternative_data.get('quantity')

            if not alternative_product_uuid or not alternative_product_price or not alternative_product_quantity:
                print(alternative_product_uuid, alternative_product_price, alternative_product_quantity,1111)
                return Response(
                    {"detail": "Alternativ mahsulot ma'lumotlari to'liq emas."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get alternative product
            alternative_product = get_product_by_uuid(alternative_product_uuid)
            if not alternative_product:
                print(alternative_product,222222)
                return Response(
                    {"detail": "Alternativ mahsulot topilmadi."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update or create TochkaProduct for alternative product
            alt_ntochka_product, created = TochkaProduct.objects.get_or_create(
                ntochka=tochka_product.ntochka,
                product=alternative_product,
                defaults={
                    'hudud': tochka_product.hudud,
                }
            )

            alt_ntochka_product.previous_price = alt_ntochka_product.last_price
            alt_ntochka_product.last_price = float(alternative_product_price)
            alt_ntochka_product.is_weekly = True
            alt_ntochka_product.save()
            alternative_data = {
                'employee': employee.id,
                'ntochka': tochka_product.ntochka.id,
                'hudud': tochka_product.hudud.id,
                'product': alternative_product.id,
                'tochka_product': alt_ntochka_product.id,
                'period': period.id,
                'period_type':'weekly',
                'price': float(alternative_product_price),
                'unit_miqdor': float(alternative_product_quantity),
                'unit_price': float(alternative_product_price) / float(
                    alternative_product_quantity) * alternative_product.unit.miqdor,
                'status': 'mavjud',  # Alternative product is available
                'is_alternative': True,
                'is_checked': True,
            }
            print(alternative_data)
            # Save alternative product history
            alt_serializer = self.get_serializer(data=alternative_data)
            if alt_serializer.is_valid():
                alt_serializer.save()

            else:
                print(alt_serializer.errors, 333)
                return Response(alt_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # For the main product, set price to 0 since it's not available
            data['price'] = 0
            data['unit_miqdor'] = 0
            data['unit_price'] = 0


        serializer = self.get_serializer(data=data)

        if serializer.is_valid():
            serializer.save()
            data = serializer.data
            tochka_product.previous_price = tochka_product.last_price
            tochka_product.last_price = data['price']
            tochka_product.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(serializer.errors, 444)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AlternativeProductListView(ListAPIView):
    pagination_class = None
    serializer_class = ProductSerializer

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
    def get(self, request, *args, **kwargs):
        req = self.request
        user_uuid = req.META.get('HTTP_X_USER_UUID')
        product_uuid = req.META.get('HTTP_X_PRODUCT_UUID')
        rasta_uuid = req.META.get('HTTP_X_RASTA_UUID')

        employee = get_employee_by_uuid(user_uuid)
        ntochka = get_ntochka_by_uuid(rasta_uuid)
        product = get_product_by_uuid(product_uuid)

        if not all([employee, ntochka, product]):
            return Response({"detail": "Invalid headers or not found"}, status=400)

        category = product.category
        category_products = Product.objects.filter(category=category).select_related(
            'category',
            'unit'
        )



        # Ushbu rasta (ntochka)da mavjud bo‘lgan productlar ID ro‘yxati
        existing_product_ids = ntochka.products.filter(
            is_udalen=False
        ).values_list('product_id', flat=True)

        # Faqat mavjud bo‘lmagan productlar
        missing_products = category_products.exclude(id__in=existing_product_ids)

        serializer = ProductSerializer(missing_products, many=True)
        return Response(serializer.data, status=200)


class ProductListView(ListAPIView):
    serializer_class = ProductListSerializer
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
        user_uuid = request.META.get('HTTP_X_USER_UUID')
        employee = get_employee_by_uuid(user_uuid)
        if not employee:
            return Response({"detail": "Xodim yoki period topilmadi."}, status=status.HTTP_400_BAD_REQUEST)
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_queryset(self):
        return Product.objects.filter(
            is_special=True
        ).select_related(
            'category'
        ).only(
            'id',
            'name',
            'category'
        ).order_by('name')
