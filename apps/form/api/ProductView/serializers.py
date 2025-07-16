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
    unit_miqdor = serializers.FloatField(source='unit.miqdor', read_only=True)

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


class TochkaProductSerializer(serializers.ModelSerializer):
    """
    Serializer for TochkaProduct model.
    """
    product = ProductSerializer(read_only=True)
    status = serializers.SerializerMethodField(read_only=True)
    product_status = serializers.SerializerMethodField(read_only=True)

    def get_status(self, obj):
        product_history = get_tochka_product_history(
            ntochka=obj.ntochka,
            product=obj.product,
            period=get_period_by_type_today().period,
        )
        if product_history is None:
            return 'unknown'
        elif obj.last_price > obj.previous_price:
            return 'increased'
        elif obj.last_price < obj.previous_price:
            return 'decreased'
        else:
            return 'unchanged'

    def get_product_status(self, obj):
        product_history = get_tochka_product_history(
            ntochka=obj.ntochka,
            product=obj.product,
            period=get_period_by_type_today().period,
        )
        return product_history.status if product_history else None

    class Meta:
        model = TochkaProduct
        fields = [
            'id', 'product', 'ntochka', 'last_price', 'previous_price', 'status', 'product_status', 'is_active', 'is_udalen'
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
