from rest_framework import serializers

from django.contrib.auth import get_user_model
from django.utils import timezone

from ...models import Application, Product, TochkaProductHistory
from apps.home.models import NTochka, PeriodDate, Employee
from apps.form.api.utils import get_period_by_today, get_period_by_type_today

User = get_user_model()


class ApplicationListSerializer(serializers.ModelSerializer):
    """
    Application modelini ro'yxat ko'rish uchun serializer
    """
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    ntochka_name = serializers.CharField(source='ntochka.name', read_only=True)
    checked_by_name = serializers.CharField(source='checked_by.username', read_only=True)
    period_name = serializers.CharField(source='period.period.name', read_only=True)
    application_type_display = serializers.CharField(source='get_application_type_display', read_only=True)
    products_count = serializers.SerializerMethodField()
    ntochkas_names = serializers.SerializerMethodField()  # ManyToMany field uchun

    class Meta:
        model = Application
        fields = [
            'id', 'application_type', 'application_type_display',
            'employee', 'employee_name', 'checked_by', 'checked_by_name',
            'ntochka', 'ntochka_name', 'ntochkas', 'ntochkas_names',
            'products', 'products_count', 'period', 'period_name',
            'comment', 'checked_at', 'is_active', 'is_checked',
            'created_at', 'updated_at'
        ]

    def get_products_count(self, obj):
        """Mahsulotlar sonini qaytaradi"""
        return len(obj.products) if obj.products else 0

    def get_ntochkas_names(self, obj):
        """
        ManyToMany ntochkas fieldidagi barcha rastalar nomlarini
        vergul bilan ajratib qaytaradi
        """
        if obj.ntochkas.exists():
            # prefetch_related ishlatganimiz uchun bu yerda DB ga qo'shimcha query bo'lmaydi
            return ", ".join([ntochka.name for ntochka in obj.ntochkas.all()])
        return ""

class ProductItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()


class ApplicationCreateSerializer(serializers.ModelSerializer):
    """
    Application yaratish uchun serializer
    """
    products = ProductItemSerializer(many=True, required=False, allow_null=True, default=list)
    period_type = serializers.CharField(write_only=True, max_length=10, default='weekly')
    rasta_name = serializers.CharField(write_only=True, max_length=100, required=False)
    tochka_id = serializers.IntegerField(write_only=True, required=True)


    class Meta:
        model = Application
        fields = [
            'application_type', 'employee', 'ntochka', 'ntochkas', 'products', 'comment',
            'rasta_name', 'tochka_id', 'period_type', 'period', 'is_active'
        ]
        extra_kwargs = {
            'period': {'required': False}
        }

    # def validate_products(self, value):
    #     """Mahsulotlar JSON formatini tekshiradi"""
    #     if not isinstance(value, list):
    #         raise serializers.ValidationError("Mahsulotlar ro'yxat ko'rinishida bo'lishi kerak")
    #
    #     for product_data in value:
    #         if not isinstance(product_data, dict):
    #             raise serializers.ValidationError("Har bir mahsulot ob'ekt ko'rinishida bo'lishi kerak")
    #
    #         required_fields = ['product_id', 'status']
    #         for field in required_fields:
    #             if field not in product_data:
    #                 raise serializers.ValidationError(f"'{field}' maydoni majburiy")
    #
    #     return value
    #
    # def validate(self, attrs):
    #     """Umumiy validatsiya"""
    #     period_type = attrs.pop('period_type', 'weekly')
    #
    #     # Agar period berilmagan bo'lsa, avtomatik olish
    #     if 'period' not in attrs or not attrs['period']:
    #         if period_type == 'weekly':
    #             period = get_period_by_type_today('weekly')
    #         else:
    #             period = get_period_by_today()
    #
    #         if not period:
    #             raise serializers.ValidationError("Hozirgi davr topilmadi")
    #         attrs['period'] = period
    #
    #     return attrs

    def create(self, validated_data):
        """Application yaratish"""
        validated_data.pop('rasta_name', None)
        validated_data.pop('tochka_id', None)
        validated_data.pop('period_type', None)
        return super().create(validated_data)


class ApplicationUpdateSerializer(serializers.ModelSerializer):
    """
    Application yangilash uchun serializer
    """
    checked_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Application
        fields = [
            'checked_by', 'checked_at', 'is_checked', 'is_active'
        ]

    def update(self, instance, validated_data):
        """Application yangilash"""
        # Agar tekshirilgan deb belgilansa, vaqtni avtomatik qo'yish
        if validated_data.get('is_checked') and not instance.is_checked:
            validated_data['checked_at'] = timezone.now()

        return super().update(instance, validated_data)


class ApplicationDetailSerializer(serializers.ModelSerializer):
    """
    Application batafsil ko'rish uchun serializer
    """
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_login = serializers.CharField(source='employee.login', read_only=True)
    ntochka_name = serializers.CharField(source='ntochka.name', read_only=True)
    ntochka_hudud = serializers.CharField(source='ntochka.hudud', read_only=True)
    checked_by_name = serializers.CharField(source='checked_by.username', read_only=True)
    period_name = serializers.CharField(source='period.period.name', read_only=True)
    application_type_display = serializers.CharField(source='get_application_type_display', read_only=True)
    products_count = serializers.SerializerMethodField()
    products_detail = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = [
            'id', 'application_type', 'application_type_display',
            'employee', 'employee_name', 'employee_login',
            'checked_by', 'checked_by_name', 'ntochka', 'ntochka_name', 'ntochka_hudud',
            'products', 'products_count', 'products_detail',
            'period', 'period_name', 'checked_at', 'is_active',
            'is_checked', 'created_at', 'updated_at'
        ]

    def get_products_count(self, obj):
        """Mahsulotlar sonini qaytaradi"""
        return len(obj.products) if obj.products else 0

    def get_products_detail(self, obj):
        """Mahsulotlar batafsil ma'lumotlari"""
        if not obj.products:
            return []

        detailed_products = []
        for product_data in obj.products:
            try:
                product = Product.objects.get(id=product_data.get('product_id'))
                detailed_products.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'product_code': product.code,
                    'category_name': product.category.name if product.category else None,
                    'status': product_data.get('status'),
                    'price': product_data.get('price'),
                })
            except Product.DoesNotExist:
                detailed_products.append({
                    'product_id': product_data.get('product_id'),
                    'product_name': 'Mahsulot topilmadi',
                    'status': product_data.get('status'),
                    'error': 'Mahsulot bazada mavjud emas'
                })

        return detailed_products