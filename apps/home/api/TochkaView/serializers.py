from rest_framework import serializers

from apps.form.api.utils import get_period_by_type_today
from apps.form.models import TochkaProductHistory
from ...models import Tochka, Employee, NTochka

class RastaSerializer(serializers.ModelSerializer):
    is_checked = serializers.SerializerMethodField()
    all_count = serializers.SerializerMethodField()
    finished = serializers.SerializerMethodField()

    class Meta:
        model = NTochka
        fields = ['id','uuid', 'name', 'hudud', 'is_active', 'is_checked', 'all_count', 'finished']

    def get_all_count(self, obj):
        return obj.products.all().count()

    def get_finished(self, obj):
        period = get_period_by_type_today()
        if not period:
            return 0
        return TochkaProductHistory.objects.filter(ntochka=obj, period=period).count()

    def get_is_checked(self, obj):
        all_count = self.get_all_count(obj)
        finished = self.get_finished(obj)
        return all_count > 0 and all_count == finished

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
        all_count = self.get_all_count(obj)
        finished = self.get_finished(obj)
        return all_count > 0 and finished == all_count

    def get_all_count(self, obj):
        return obj.ntochkas.all().count()

    def get_finished(self, obj):
        finished = 0
        for rasta in obj.ntochkas.all():
            total = rasta.products.count()
            if total == 0:
                continue
            period = get_period_by_type_today()
            if not period:
                continue
            completed = TochkaProductHistory.objects.filter(ntochka=rasta, period=period).count()
            if completed == total:
                finished += 1
        return finished

