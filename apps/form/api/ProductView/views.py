from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.response import Response
from rest_framework import status

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from ..utils import get_product_by_uuid, get_period_by_type_today
from ...models import TochkaProduct, Product

from .serializers import TochkaProductSerializer, TochkaProductHistorySerializer, ProductSerializer

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

        # Get product status
        product_status = data.get('status')
        print(data)
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

            # Create alternative product history
            alternative_data = {
                'employee': employee.id,
                'ntochka': ntochka.id,
                'hudud': ntochka.hudud.id,
                'product': alternative_product.id,
                'period': period.id,
                'period_type':'weekly',
                'price': float(alternative_product_price),
                'unit_miqdor': float(alternative_product_quantity),
                'unit_price': float(alternative_product_price) / float(
                    alternative_product_quantity) * alternative_product.unit.miqdor,
                'status': 'mavjud',  # Alternative product is available
                'is_alternative': True,
                'alternative_for': product,
                'is_checked': True,
            }

            # Save alternative product history
            alt_serializer = self.get_serializer(data=alternative_data)
            if alt_serializer.is_valid():
                alt_serializer.save()

                # Update or create TochkaProduct for alternative product
                alt_ntochka_product, created = TochkaProduct.objects.get_or_create(
                    ntochka=ntochka,
                    product=alternative_product,
                    defaults={
                        'hudud': ntochka.hudud,
                        'last_price': float(alternative_product_price),
                        'previous_price': 0
                    }
                )

                if not created:
                    alt_ntochka_product.previous_price = alt_ntochka_product.last_price
                    alt_ntochka_product.last_price = float(alternative_product_price)
                    alt_ntochka_product.save()
            else:
                print(alt_serializer.errors, 333)
                return Response(alt_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # For the main product, set price to 0 since it's not available
            data['price'] = 0
            data['unit_miqdor'] = 0
            data['unit_price'] = 0

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
        print(4444444)
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
        category_products = Product.objects.filter(category=category)

        # Ushbu rasta (ntochka)da mavjud bo‘lgan productlar ID ro‘yxati
        existing_product_ids = ntochka.products.filter(
            is_udalen=False
        ).values_list('product_id', flat=True)

        # Faqat mavjud bo‘lmagan productlar
        missing_products = category_products.exclude(id__in=existing_product_ids)

        serializer = ProductSerializer(missing_products, many=True)
        print(serializer.data)
        return Response(serializer.data, status=200)