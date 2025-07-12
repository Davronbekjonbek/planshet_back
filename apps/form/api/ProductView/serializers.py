from rest_framework import serializers

from apps.form.models import ProductCategory, Product, TochkaProduct, TochkaProductHistory


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category__name', read_only=True)
    category_code = serializers.CharField(source='category__code', read_only=True)
    unit_name = serializers.CharField(source='unit__name', read_only=True)
    unit_miqdor = serializers.FloatField(source='unit__miqdor', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'category', 'category_name','category_code', 'code', 'price','unit_id', 'unit_name', 'unit_miqdor', 'top', 'bottom',
            'created_at', 'updated_at'
        ]


class TochkaProductSerializer(serializers.ModelSerializer):
    """
    Serializer for TochkaProduct model.
    """
    product = ProductSerializer(read_only=True)
    class Meta:
        model = TochkaProduct
        fields = [
            'id', 'product', 'ntochka', 'last_price', 'is_active', 'is_udalen'
        ]

class TochkaProductHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for TochkaProductHistory model.
    """
    class Meta:
        model = TochkaProductHistory
        fields = [
            'id', 'product', 'ntochka', 'hudud', 'price', 'unit_miqdor', 'unit_price', 'is_checked', 'is_active'
        ]
