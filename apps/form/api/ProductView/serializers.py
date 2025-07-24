from random import choices

from django.conf import settings
from rest_framework import serializers

from apps.form.api.utils import get_period_by_today, get_tochka_product_history, get_period_by_type_today
from apps.form.models import ProductCategory, Product, TochkaProduct, TochkaProductHistory


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_code = serializers.CharField(source='category.code', read_only=True)
    rasfas = serializers.CharField(source='category.rasfas', read_only=True)
    category_logo = serializers.SerializerMethodField(read_only=True)
    unit_name = serializers.CharField(source='unit.name', read_only=True)
    unit_miqdor = serializers.FloatField(source='category.rasfas', read_only=True)

    def get_category_logo(self, obj):
        if obj.category.logo:
            return f"{settings.IMAGE_URL}{obj.category.logo.url}"
        return None

    class Meta:
        model = Product
        fields = [
            'id', 'uuid', 'name', 'category', 'category_name','category_code', 'category_logo', 'rasfas', 'code', 'price',
            'unit_id', 'unit_name', 'unit_miqdor', 'top', 'bottom', 'is_import', 'created_at', 'updated_at',
        ]


class ProductListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_code = serializers.CharField(source='category.code', read_only=True)
    name = serializers.CharField(read_only=True)

class TochkaProductSerializer(serializers.ModelSerializer):
    """
    Optimized Serializer for TochkaProduct model.
    """
    product = ProductSerializer(read_only=True)
    status = serializers.SerializerMethodField(read_only=True)
    product_status = serializers.SerializerMethodField(read_only=True)

    def get_status(self, obj):
        # Prefetch qilingan ma'lumotlardan foydalanish
        history = getattr(obj.product, 'current_history', [])
        if not history:
            return 'unknown'

        if obj.last_price > obj.previous_price:
            return 'increased'
        elif obj.last_price < obj.previous_price:
            return 'decreased'
        else:
            return 'unchanged'

    def get_product_status(self, obj):
        # Prefetch qilingan ma'lumotlardan foydalanish
        history = getattr(obj.product, 'current_history', [])
        return history[0].status if history else None

    class Meta:
        model = TochkaProduct
        fields = [
            'id', 'product', 'ntochka', 'last_price',
            'previous_price', 'status', 'product_status',
            'is_active', 'is_udalen'
        ]

class TochkaProductHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for TochkaProductHistory model.
    """
    period_type = serializers.CharField(write_only=True, max_length=10)

    class Meta:
        model = TochkaProductHistory
        fields = [
            'id', 'product', 'status', 'period_type', 'ntochka', 'employee', 'period', 'hudud', 'price', 'unit_miqdor', 'unit_price', 'is_checked', 'is_active'
        ]
        read_only_fields = ['unit_miqdor', 'unit_price', 'is_checked', 'is_active']

    def create(self, validated_data):
        validated_data.pop('period_type', None)
        return super().create(validated_data)
