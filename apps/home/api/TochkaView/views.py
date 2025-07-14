from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.generics import ListAPIView

from ...models import Tochka

from .serializers import TochkaSerializer

from ..utils import get_employee_by_uuid


class TochkaListView(ListAPIView):
    """
    ListAPIView View for listing Tochkas.
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
        if employee:
            return Tochka.objects.filter(employee=employee, is_active=True)
        return Tochka.objects.none()