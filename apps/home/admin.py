from django.contrib import admin
from django.contrib.admin.widgets import AdminDateWidget
from django.forms import ModelForm
from django.urls import path
from django.utils.html import format_html
from django.db import models
from .models import Region, District, Period, PeriodDate, Tochka, Employee, NTochka
from ..common.admin import BaseAdmin
from apps.common.views import export_all_csv_zip


class CSVExportMixin:
    """Admin panelga export button qo'shish uchun mixin"""

    def get_urls(self):
        urls = super().get_urls()
        info = self.model._meta.app_label, self.model._meta.model_name
        custom_urls = [
            path('export-all-csv/', export_all_csv_zip, name='export_all_csv'),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        """Admin changelist view ga export button qo'shish"""
        extra_context = extra_context or {}
        extra_context['show_export_button'] = True
        return super().changelist_view(request, extra_context)

@admin.register(Region)
class RegionAdmin(BaseAdmin):
    list_display = ('name', 'code', 'districts_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'code')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_districts_count=models.Count('districts'))

    def districts_count(self, obj):
        return obj._districts_count

    districts_count.short_description = 'Tumanlar soni'
    districts_count.admin_order_field = '_districts_count'


@admin.register(District)
class DistrictAdmin(BaseAdmin):
    list_display = ('name', 'region', 'code', 'employees_count', 'created_at')
    list_filter = ('region', 'created_at')
    search_fields = ('name', 'code', 'region__name')
    ordering = ('region__name', 'name')
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('region',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_employees_count=models.Count('employees'))

    def employees_count(self, obj):
        return obj._employees_count

    employees_count.short_description = 'Xodimlar soni'
    employees_count.admin_order_field = '_employees_count'


class PeriodDateForm(ModelForm):
    class Meta:
        model = PeriodDate
        fields = '__all__'


class PeriodDateInline(admin.TabularInline):
    model = PeriodDate
    # form = PeriodDateForm
    extra = 1
    fields = ['date']


@admin.register(Period)
class PeriodAdmin(CSVExportMixin, admin.ModelAdmin):
    list_display = ['name', 'period_type', 'is_active']
    list_filter = ['period_type', 'is_active']
    search_fields = ['name']
    inlines = [PeriodDateInline]


@admin.register(PeriodDate)
class PeriodDateAdmin(admin.ModelAdmin):
    form = PeriodDateForm
    list_display = ['period', 'date']
    list_filter = ['period', 'date']
    date_hierarchy = 'date'



@admin.register(Tochka)
class TochkaAdmin(BaseAdmin):
    list_display = ('id', 'name', 'district', 'inn', 'address', 'plan', 'location', 'created_at')
    list_filter = ('district__region', 'district', 'is_active')
    search_fields = ('name', 'inn', 'address', 'code')
    ordering = ('-id',)
    readonly_fields = ('uuid', 'created_at', 'updated_at')
    exclude = ('uuid',)
    list_select_related = ('district', 'district__region', 'employee')
    list_per_page = 50
    raw_id_fields = ('employee', 'district')

    def location(self, obj):
        if obj.lat and obj.lon:
            return format_html(
                '<a href="https://maps.google.com/?q={},{}" target="_blank">Xaritada</a>',
                obj.lat, obj.lon
            )
        return '-'

    location.short_description = 'Joylashuv'



@admin.register(NTochka)
class NTochkaAdmin(BaseAdmin):
    
    list_display = ('id', 'name', 'hudud', 'code', 'is_active')
    list_filter = ('is_active', 'weekly_type', 'product_type')
    readonly_fields = ('uuid',)
    search_fields = ('name', 'code')
    list_select_related = ('hudud', 'hudud__district', 'hudud__employee')
    list_per_page = 50
    raw_id_fields = ('hudud',)
    autocomplete_fields = []


@admin.register(Employee)
class EmployeeAdmin(BaseAdmin):
    list_display = ('id','full_name', 'login', 'district', 'status', 'lang', 'permissions_summary', 'created_at')
    list_filter = ('district__region', 'district', 'status', 'lang', 'created_at')
    list_display_links = ('id', 'full_name')
    search_fields = ('full_name', 'login', 'district__name')
    ordering = ('full_name',)
    readonly_fields = ('uuid', 'created_at', 'updated_at')
    list_select_related = ("district","district__region") 

    # fieldsets = (
    #     ('Shaxsiy ma\'lumotlar', {
    #         'fields': ('full_name', 'login', 'password', 'district', 'status', 'lang')
    #     }),
    #     ('Ruxsatlar', {
    #         'fields': ('permission1', 'permission2', 'permission3', 'permission4', 'permission5', 'permission_plov',
    #                    'gps_permission'),
    #         'classes': ('collapse',)
    #     }),
    #     ('Vaqt ma\'lumotlari', {
    #         'fields': ('created_at', 'updated_at'),
    #         'classes': ('collapse',)
    #     })
    # )

    def permissions_summary(self, obj):
        permissions = []
        if obj.permission1: permissions.append('1')
        if obj.permission2: permissions.append('2')
        if obj.permission3: permissions.append('3')
        if obj.permission4: permissions.append('4')
        if obj.permission5: permissions.append('5')
        if obj.permission_plov: permissions.append('Plov')
        if obj.gps_permission: permissions.append('GPS')
        return ', '.join(permissions) if permissions else 'Ruxsat yo\'q'

    permissions_summary.short_description = 'Ruxsatlar'


