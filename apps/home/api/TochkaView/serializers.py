from rest_framework import serializers

from ...models import Tochka, Employee, NTochka

class RastaSerializer(serializers.ModelSerializer):
    is_checked = serializers.SerializerMethodField()
    all_count = serializers.SerializerMethodField()
    finished = serializers.SerializerMethodField()

    class Meta:
        model = NTochka
        fields = ['id','uuid', 'name', 'hudud', 'is_active', 'is_checked', 'all_count', 'finished']

    def get_is_checked(self, obj):
        return False

    def get_all_count(self, obj):
        return 10

    def get_finished(self, obj):
        return 9

class TochkaSerializer(serializers.ModelSerializer):
    """
    Serializer for Tochka model.
    """
    icon_display = serializers.ReadOnlyField()
    icon_color = serializers.ReadOnlyField()
    is_checked = serializers.SerializerMethodField()
    all_count = serializers.SerializerMethodField()
    finished = serializers.SerializerMethodField()
    ntochkas = RastaSerializer(many=True, read_only=True)

    class Meta:
        model = Tochka
        fields = [
            'id', 'uuid', 'name', 'icon', 'icon_display', 'icon_color', 'address', 'district',
            'inn', 'plan', 'lat', 'lon', 'employee', 'is_active', 'is_checked', 'all_count', 'finished', 'ntochkas'
        ]

    def get_is_checked(self, obj):
        return False

    def get_all_count(self, obj):
        return 10

    def get_finished(self, obj):
        return 0

