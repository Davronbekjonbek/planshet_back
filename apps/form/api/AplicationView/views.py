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
from ...models import Application, Product, TochkaProductHistory
from apps.home.models import NTochka, PeriodDate, Employee
from apps.form.api.utils import get_period_by_today, get_period_by_type_today

from .serializers import (
    ApplicationListSerializer,
    ApplicationCreateSerializer,
    ApplicationUpdateSerializer,
    ApplicationDetailSerializer
)

User = get_user_model()

class ApplicationCreateView(CreateAPIView):
    """
    Application (ariza) yaratish uchun view
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

        mutable_data = request.data.copy()
        mutable_data['employee'] = employee.id
        mutable_data['period'] = period.id

        if application_type == 'for_open':
            rasta_name = request.data.get('rasta_name')
            tochka_id = request.data.get('tochka_id')
            print(tochka_id)
            ntochka = NTochka.objects.create(in_proccess=True, name=rasta_name, hudud_id=tochka_id)
            mutable_data['ntochka'] = ntochka.id

        elif application_type == 'for_close':
            mutable_data['ntochkas'] = request.data.get('ntochkas', [])
        print(mutable_data)
        serializer = self.get_serializer(data=mutable_data)

        if not serializer.is_valid():
            import logging
            logger = logging.getLogger(__name__)
            logger.error(serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.is_valid(raise_exception=True)
        application = serializer.save()
        detail_serializer = ApplicationDetailSerializer(application)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)


class ApplicationListView(ListAPIView):
    serializer_class = ApplicationListSerializer

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
        # Xodim UUIDni headerdan olish
        uuid = self.request.META.get('HTTP_X_USER_UUID')
        employee = get_employee_by_uuid(uuid)
        if not employee:
            return Application.objects.none()

        return (
            Application.objects
            .filter(employee=employee)
            .select_related(
                'employee',
                'checked_by',
                'ntochka',
                'period',
                'period__period'
            )
            .prefetch_related('ntochkas')
            .order_by('-created_at')
        )

