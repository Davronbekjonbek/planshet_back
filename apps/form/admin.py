from django.contrib import admin
from django.utils.html import format_html
from .models import Birlik, ProductCategory, Product, TochkaProduct, TochkaProductHistory
from ..common.admin import BaseAdmin


@admin.register(Birlik)
class BirlikAdmin(BaseAdmin):
    list_display = ('name', 'code', 'categories_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'code')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')

    def categories_count(self, obj):
        return obj.categories.count()

    categories_count.short_description = 'Kategoriyalar soni'


@admin.register(ProductCategory)
class ProductCategoryAdmin(BaseAdmin):
    list_display = ('name', 'code', 'union', 'number', 'rasfas', 'is_weekly', 'products_count',
                    'created_at')
    list_filter = ('union', 'rasfas', 'is_weekly', 'created_at')
    search_fields = ('name', 'name_ru', 'code')
    ordering = ('number', 'name')
    readonly_fields = ('created_at', 'updated_at')

    # fieldsets = (
    #     ('Asosiy ma\'lumotlar', {
    #         'fields': ('name', 'name_ru', 'code', 'union', 'number')
    #     }),
    #     ('Sozlamalar', {
    #         'fields': ('top', 'bottom', 'rasfas', 'is_weekly')
    #     }),
    #     ('Vaqt ma\'lumotlari', {
    #         'fields': ('created_at', 'updated_at'),
    #         'classes': ('collapse',)
    #     })
    # )

    def products_count(self, obj):
        return obj.products.count()

    products_count.short_description = 'Mahsulotlar soni'


@admin.register(Product)
class ProductAdmin(BaseAdmin):
    list_display = ('name', 'category', 'code', 'price', 'unit', 'price_display',  'top', 'bottom', 'created_at')
    list_filter = ('category__union', 'category', 'unit', 'created_at')
    search_fields = ('name', 'name_ru', 'code')
    ordering = ('category__name', 'name')
    readonly_fields = ('uuid', 'created_at', 'updated_at')

    # fieldsets = (
    #     ('Asosiy ma\'lumotlar', {
    #         'fields': ('name', 'name_ru', 'category', 'code')
    #     }),
    #     ('Narx va o\'lchov', {
    #         'fields': ('price', 'unit')
    #     }),
    #     ('Vaqt ma\'lumotlari', {
    #         'fields': ('created_at', 'updated_at'),
    #         'classes': ('collapse',)
    #     })
    # )

    def price_display(self, obj):
        return format_html('<strong>{} {}</strong>', obj.price, obj.unit)

    price_display.short_description = 'Narx'


@admin.register(TochkaProduct)
class TochkaProductAdmin(BaseAdmin):
    list_display = ('product', 'ntochka', 'last_price', 'price_display', 'created_at')
    list_filter = ('product__category', 'created_at','ntochka__hudud')
    search_fields = ('product__name', 'hudud__name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    def price_display(self, obj):
        return format_html('<strong>{} {}</strong>', obj.last_price, obj.product.unit)

    price_display.short_description = 'Oxirgi narx'


@admin.register(TochkaProductHistory)
class TochkaProductHistoryAdmin(BaseAdmin):
    list_display = ('product', 'hudud', 'price', 'employee', 'period', 'price_display', 'created_at')
    list_filter = ('period', 'hudud__district__region', 'hudud__district', 'product__category', 'created_at')
    search_fields = ('product__name', 'hudud__name', 'employee__full_name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'

    # fieldsets = (
    #     ('Asosiy ma\'lumotlar', {
    #         'fields': ('product', 'hudud', 'price', 'employee', 'period')
    #     }),
    #     ('Vaqt ma\'lumotlari', {
    #         'fields': ('created_at', 'updated_at'),
    #         'classes': ('collapse',)
    #     })
    # )

    def price_display(self, obj):
        return format_html('<strong>{} {}</strong>', obj.price, obj.product.unit)

    price_display.short_description = 'Narx'




