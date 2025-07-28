from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated

from django.contrib.auth import get_user_model
from django.db.models import Q, Prefetch
from django.utils import timezone

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from apps.home.api.utils import get_employee_by_uuid
from ...models import Application, Product, TochkaProduct, TochkaProductHistory
from apps.home.models import NTochka, PeriodDate, Employee, Tochka
from apps.form.api.utils import get_period_by_today, get_period_by_type_today

from .serializers import (
    ApplicationListSerializer,
    ApplicationCreateSerializer,
    ApplicationUpdateSerializer,
    ApplicationDetailSerializer
)

User = get_user_model()

import logging

logger = logging.getLogger(__name__)


class ApplicationListView(ListAPIView):
    """
    Arizalar ro'yxatini olish uchun optimizatsiya qilingan view
    """
    serializer_class = ApplicationListSerializer

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'X-User-UUID',
                openapi.IN_HEADER,
                description="Xodim UUID raqami (header orqali)",
                type=openapi.TYPE_STRING,
                required=True
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        return Response(
            self.get_serializer(self.get_queryset(), many=True).data,
            status=status.HTTP_200_OK
        )

    def get_queryset(self):
        user_uuid = self.request.META.get('HTTP_X_USER_UUID')
        employee = get_employee_by_uuid(user_uuid)

        if not employee:
            return Application.objects.none()

        # Optimizatsiya: select_related va prefetch_related ishlatish
        queryset = Application.objects.filter(
            employee=employee
        ).select_related(
            'employee',
            'checked_by',
            'period',
            'tochka',  # ForeignKey
            'tochka__district',  # Nested ForeignKey
            'ntochka',  # ForeignKey
            'ntochka__hudud',  # Nested ForeignKey
        ).prefetch_related(
            'tochkas',  # ManyToMany
            'tochkas__district',  # Nested relation
            'ntochkas',  # ManyToMany
            'ntochkas__hudud',  # Nested relation
        ).order_by('-created_at')

        # Filter by application_type if provided
        application_type = self.request.query_params.get('application_type')
        if application_type:
            queryset = queryset.filter(application_type=application_type)

        # Filter by is_checked status
        is_checked = self.request.query_params.get('is_checked')
        if is_checked is not None:
            queryset = queryset.filter(is_checked=is_checked.lower() == 'true')

        return queryset


class ApplicationCreateView(CreateAPIView):
    """
    Application (ariza) yaratish uchun asosiy view
    """
    serializer_class = ApplicationCreateSerializer
    queryset = Application.objects.all()

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'X-User-UUID',
                openapi.IN_HEADER,
                description="Xodim UUID raqami (header orqali)",
                type=openapi.TYPE_STRING,
                required=True
            ),
        ]
    )
    def post(self, request, *args, **kwargs):
        user_uuid = request.META.get('HTTP_X_USER_UUID')
        employee = get_employee_by_uuid(user_uuid)
        application_type = request.data.get('application_type')
        period = get_period_by_type_today('weekly')

        if not employee or not period:
            return Response(
                {"detail": "Xodim yoki period topilmadi."},
                status=status.HTTP_400_BAD_REQUEST
            )
        district = employee.district
        mutable_data = request.data.copy()
        mutable_data['employee'] = employee.id
        mutable_data['period'] = period.id
        print(request.data)
        try:
            # FOR_CLOSE_RASTA - Rastalarni yopish
            if application_type == 'for_close_rasta':
                ntochka_ids = request.data.get('ntochkas', [])
                if not ntochka_ids:
                    return Response(
                        {"detail": "Yopish uchun kamida bitta rasta tanlang."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                mutable_data['ntochkas'] = ntochka_ids

            # FOR_OPEN_RASTA - Yangi rasta yaratish
            elif application_type == 'for_open_rasta':
                rasta_name = request.data.get('rasta_name')
                tochka_id = request.data.get('tochka_id')

                if not rasta_name or not tochka_id:
                    return Response(
                        {"detail": "Rasta nomi va obyekt ID si majburiy."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                try:
                    tochka = Tochka.objects.select_related('district').get(id=tochka_id)
                    ntochka = NTochka.objects.create(
                        name=rasta_name,
                        hudud=tochka,
                        in_proccess=True,
                    )
                    ntochka.code=f"{tochka.code}-{ntochka.id}"
                    ntochka.save()
                    products = request.data.get('products', [])
                    if products:
                        tochka_products = [
                            TochkaProduct(
                                product_id=product.get('product_id'),
                                ntochka=ntochka,
                                hudud=tochka,
                                is_active=True
                            )
                            for product in products if product.get('product_id')
                        ]
                        TochkaProduct.objects.bulk_create(tochka_products)
                    mutable_data['ntochka'] = ntochka.id
                except Tochka.DoesNotExist:
                    return Response(
                        {"detail": "Obyekt topilmadi."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # FOR_CLOSE_OBYEKT - Obyektlarni yopish
            elif application_type == 'for_close_obyekt':
                tochka_ids = request.data.get('tochkas', [])
                if not tochka_ids:
                    return Response(
                        {"detail": "Yopish uchun kamida bitta obyekt tanlang."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                mutable_data['tochkas'] = tochka_ids

            elif application_type == 'for_open_obyekt':
                obyekt_data = request.data.get('obyekt_data', {})
                required_fields = ['name', 'lat', 'lon', 'address']
                missing_fields = [field for field in required_fields if not obyekt_data.get(field)]

                if missing_fields:
                    return Response(
                        {"detail": f"Quyidagi maydonlar majburiy: {', '.join(missing_fields)}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                try:
                    tochka = Tochka.objects.create(
                        name=obyekt_data['name'],
                        district=district,
                        address=obyekt_data['address'],
                        lat=obyekt_data['lat'],
                        lon=obyekt_data['lon'],
                        icon=obyekt_data.get('icon', 'nutrition'),
                        inn=obyekt_data.get('inn', ''),
                        plan=obyekt_data.get('plan', 0),
                        pinfl= obyekt_data.get('pinfl', ''),
                        employee=employee,
                        in_proccess=True
                    )
                    tochka.code=f"{district.region.code}{district.code}{tochka.id}"
                    tochka.save()
                    mutable_data['tochka'] = tochka.id
                except Exception as e:
                    logger.error(f"Tochka creation error: {str(e)}")
                    return Response(
                        {"detail": f"Xatolik yuz berdi: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            else:
                return Response(
                    {"detail": "Noto'g'ri ariza turi."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Ariza yaratish
            serializer = self.get_serializer(data=mutable_data)

            if not serializer.is_valid():
                logger.error(f"Serializer errors: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            application = serializer.save()

            # # Response data - optimizatsiya bilan
            # response_data = {
            #     'id': application.id,
            #     'message': 'Ariza muvaffaqiyatli yaratildi',
            #     'application_type': application.application_type,
            # }
            #
            res_data = {}
            if application_type == 'for_open_rasta' and application.ntochka:
                res_data = {
                    'id': application.ntochka.id,
                    'uuid': application.ntochka.uuid,
                }
            elif application_type == 'for_open_obyekt' and application.tochka:
                res_data = {
                    'id': application.tochka.id,
                    'uuid': application.tochka.uuid,
                }

            return Response({'message':'success', 'application_type':application_type, 'data':res_data}, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Application creation error: {str(e)}")
            return Response(
                {"detail": f"Xatolik yuz berdi: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )