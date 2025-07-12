from rest_framework import serializers

from apps.form.models import ProductCategory, Product, TochkaProduct, TochkaProductHistory


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_code = serializers.CharField(source='category.code', read_only=True)
    unit_name = serializers.CharField(source='unit.name', read_only=True)
    unit_miqdor = serializers.FloatField(source='unit.miqdor', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'category', 'code', 'price','unit_id', 'unit_name', 'unit_miqdor', 'top', 'bottom',
            'is_import', 'created_at', 'updated_at'
        ]


class TochkaProductSerializer(serializers.ModelSerializer):
    """
    Serializer for TochkaProduct model.
    """
    product = ProductSerializer(read_only=True)
    class Meta:
        model = TochkaProduct
        fields = [
            'id', 'product', 'ntochka', 'last_price',  'is_active', 'is_udalen'
        ]

class TochkaProductHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TochkaProductHistory
        fields = [
            'id', 'product', 'hudud', 'price', 'unit_miqdor', 'unit_price', 'employee', 'period', 'is_checked', 'is_active'
        ]
