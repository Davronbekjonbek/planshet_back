from rest_framework import serializers

from django.contrib.auth import get_user_model
from django.utils import timezone

from ...models import Application, Product, TochkaProductHistory
from apps.home.models import NTochka, PeriodDate, Employee
from apps.form.api.utils import get_period_by_today, get_period_by_type_today

User = get_user_model()


class ApplicationCreateSerializer(serializers.ModelSerializer):
    """
    Ariza yaratish uchun serializer
    """
    # Obyekt yaratish uchun ma'lumotlar (for_open_obyekt uchun)
    obyekt_data = serializers.JSONField(required=False, write_only=True)

    # Rasta nomi (for_open_rasta uchun)
    rasta_name = serializers.CharField(required=False, write_only=True)

    # Obyekt ID (for_open_rasta uchun)
    tochka_id = serializers.IntegerField(required=False, write_only=True)

    class Meta:
        model = Application
        fields = [
            'id',
            'application_type',
            'employee',
            'tochka',
            'tochkas',
            'ntochka',
            'ntochkas',
            'products',
            'period',
            'comment',
            'detail',
            'obyekt_data',
            'rasta_name',
            'tochka_id',
        ]
        read_only_fields = ['id', 'checked_by', 'checked_at', 'is_checked']

    def validate_application_type(self, value):
        valid_types = ['for_close_rasta', 'for_open_rasta', 'for_close_obyekt', 'for_open_obyekt']
        if value not in valid_types:
            raise serializers.ValidationError(
                f"Ariza turi quyidagilardan biri bo'lishi kerak: {', '.join(valid_types)}")
        return value

    def validate(self, attrs):
        application_type = attrs.get('application_type')

        # FOR_CLOSE_RASTA validatsiya
        if application_type == 'for_close_rasta':
            if not attrs.get('ntochkas'):
                raise serializers.ValidationError({
                    'ntochkas': 'Yopish uchun kamida bitta rasta tanlang.'
                })

        # FOR_OPEN_RASTA validatsiya
        elif application_type == 'for_open_rasta':
            if not attrs.get('products'):
                raise serializers.ValidationError({
                    'products': 'Kamida bitta mahsulot tanlang.'
                })

        # FOR_CLOSE_OBYEKT validatsiya
        elif application_type == 'for_close_obyekt':
            if not attrs.get('tochkas'):
                raise serializers.ValidationError({
                    'tochkas': 'Yopish uchun kamida bitta obyekt tanlang.'
                })

        # FOR_OPEN_OBYEKT validatsiya
        elif application_type == 'for_open_obyekt':
            pass

        return attrs

    def create(self, validated_data):
        # Pop qo'shimcha maydonlar
        validated_data.pop('obyekt_data', None)
        validated_data.pop('rasta_name', None)
        validated_data.pop('tochka_id', None)

        # ManyToMany maydonlarni alohida saqlash
        tochkas = validated_data.pop('tochkas', [])
        ntochkas = validated_data.pop('ntochkas', [])

        # Application yaratish
        application = Application.objects.create(**validated_data)

        # ManyToMany bog'lanishlarni o'rnatish
        if tochkas:
            application.tochkas.set(tochkas)
        if ntochkas:
            application.ntochkas.set(ntochkas)

        return application


class ApplicationListSerializer(serializers.ModelSerializer):
    """
    Arizalar ro'yxati uchun optimizatsiya qilingan serializer
    """
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    checked_by_name = serializers.CharField(source='checked_by.get_full_name', read_only=True, allow_null=True)
    application_type_display = serializers.CharField(source='get_application_type_display', read_only=True)

    # Related obyektlar - SerializerMethodField ishlatish
    tochka_detail = serializers.SerializerMethodField()
    tochkas_detail = serializers.SerializerMethodField()
    ntochka_detail = serializers.SerializerMethodField()
    ntochkas_detail = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = [
            'id',
            'application_type',
            'application_type_display',
            'employee',
            'employee_name',
            'checked_by',
            'checked_by_name',
            'tochka',
            'tochka_detail',
            'tochkas',
            'tochkas_detail',
            'ntochka',
            'ntochka_detail',
            'ntochkas',
            'ntochkas_detail',
            'products',
            'period',
            'checked_at',
            'comment',
            'detail',
            'is_active',
            'is_checked',
            'created_at',
            'updated_at',
        ]

    def get_tochka_detail(self, obj):
        # select_related bilan allaqachon yuklangan
        if obj.tochka:
            return {
                'id': obj.tochka.id,
                'name': obj.tochka.name,
                'code': obj.tochka.code,
                'address': obj.tochka.address,
                'icon': obj.tochka.icon,
                'icon_display': obj.tochka.icon_display,
                'icon_color': obj.tochka.icon_color,
                'district_name': obj.tochka.district.name if obj.tochka.district else None,
            }
        return None

    def get_tochkas_detail(self, obj):
        # prefetch_related bilan allaqachon yuklangan
        return [
            {
                'id': t.id,
                'name': t.name,
                'code': t.code,
                'address': t.address,
                'icon': t.icon,
                'icon_display': t.icon_display,
                'icon_color': t.icon_color,
                'district_name': t.district.name if t.district else None,
            }
            for t in obj.tochkas.all()
        ]

    def get_ntochka_detail(self, obj):
        # select_related bilan allaqachon yuklangan
        if obj.ntochka:
            return {
                'id': obj.ntochka.id,
                'name': obj.ntochka.name,
                'code': obj.ntochka.code,
                'hudud_name': obj.ntochka.hudud.name if obj.ntochka.hudud else None,
                'hudud_id': obj.ntochka.hudud.id if obj.ntochka.hudud else None,
            }
        return None

    def get_ntochkas_detail(self, obj):
        # prefetch_related bilan allaqachon yuklangan
        return [
            {
                'id': n.id,
                'name': n.name,
                'code': n.code,
                'hudud_name': n.hudud.name if n.hudud else None,
                'hudud_id': n.hudud.id if n.hudud else None,
            }
            for n in obj.ntochkas.all()
        ]

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