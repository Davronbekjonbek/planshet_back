from rest_framework import serializers
from apps.home.models import Employee


class LoginSerializer(serializers.Serializer):
    login = serializers.CharField(max_length=100)
    password = serializers.CharField(max_length=100, write_only=True)

    def validate(self, attrs):
        login = attrs.get('login')
        password = attrs.get('password')

        if login and password:
            try:
                employee = Employee.objects.get(login=login)
                if employee.password == password:
                    attrs['employee'] = employee
                    return attrs
                else:
                    raise serializers.ValidationError("Noto'g'ri parol")
            except Employee.DoesNotExist:
                raise serializers.ValidationError("Bunday login mavjud emas")
        else:
            raise serializers.ValidationError("Login va parol kiritilishi shart")

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['id', 'uuid', 'full_name', 'login', 'district', 'status', 'permission1',
                 'permission2', 'permission3', 'permission4', 'permission5',
                 'phone1', 'phone2', 'permission_plov', 'gps_permission', 'lang']
