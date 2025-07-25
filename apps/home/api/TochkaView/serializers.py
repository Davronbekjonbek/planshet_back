from rest_framework import serializers

from django.db.models import  Q

from apps.form.api.utils import get_period_by_type_today
from apps.form.models import TochkaProductHistory

from ...models import Tochka, Employee, NTochka


class RastaSerializer(serializers.ModelSerializer):
    is_checked = serializers.SerializerMethodField()
    all_count = serializers.SerializerMethodField()
    finished = serializers.SerializerMethodField()

    class Meta:
        model = NTochka
        fields = ['id', 'uuid', 'name', 'hudud', 'is_active', 'is_checked', 'all_count', 'finished', 'in_proccess', 'products']

    def get_all_count(self, obj):
        # Use prefetched data instead of database query
        return len(getattr(obj, 'active_products', []))

    def get_finished(self, obj):
        # Use prefetched data instead of database query
        return len(getattr(obj, 'completed_history', []))

    def get_is_checked(self, obj):
        all_count = self.get_all_count(obj)
        finished = self.get_finished(obj)
        return all_count > 0 and all_count == finished


class TochkaSerializer(serializers.ModelSerializer):
    """
    Optimized Serializer for Tochka model.
    """
    icon_display = serializers.ReadOnlyField()
    icon_color = serializers.ReadOnlyField()
    is_checked = serializers.SerializerMethodField()
    all_count = serializers.SerializerMethodField()
    finished = serializers.SerializerMethodField()
    ntochkas = RastaSerializer(many=True, read_only=True, source='active_ntochkas')

    class Meta:
        model = Tochka
        fields = [
            'id', 'uuid', 'name', 'icon', 'icon_display', 'icon_color', 'address', 'in_proccess',
            'lat', 'lon', 'employee', 'is_active', 'is_checked', 'all_count', 'finished', 'ntochkas'
        ]

    def get_is_checked(self, obj):
        all_count = self.get_all_count(obj)
        finished = self.get_finished(obj)
        return all_count > 0 and finished == all_count

    def get_all_count(self, obj):
        # Use prefetched data instead of database query
        return len(getattr(obj, 'active_ntochkas', []))

    def get_finished(self, obj):
        # Use prefetched data and avoid nested loops
        finished = 0
        ntochkas = getattr(obj, 'active_ntochkas', [])

        for rasta in ntochkas:
            total = len(getattr(rasta, 'active_products', []))
            if total == 0:
                continue

            completed = len(getattr(rasta, 'completed_history', []))
            if completed == total:
                finished += 1

        return finished