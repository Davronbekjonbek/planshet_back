from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView

from apps.home.models import Employee

from .serializers import EmployeeSerializer, LoginSerializer

class LoginView(CreateAPIView):
    """
    CreateAPIView View for user login.
    """
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            employee = serializer.validated_data['employee']
            employee_serializer = EmployeeSerializer(employee)
            return Response(employee_serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
