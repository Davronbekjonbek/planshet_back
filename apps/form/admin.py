from django.contrib import admin
from django.forms import ValidationError
from django.utils.html import format_html

from apps.home.models import Employee, PeriodDate, Tochka, NTochka, Period
from .models import Birlik, ProductCategory, Product, TochkaProduct, TochkaProductHistory, Application
from apps.common.admin import BaseAdmin


@admin.register(Birlik)
class BirlikAdmin(BaseAdmin):
    list_display = ('name', 'code', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'code')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')

    


@admin.register(ProductCategory)
class ProductCategoryAdmin(BaseAdmin):
    list_display = ('id', 'name', 'code', 'union', 'number', 'rasfas', 'created_at')
    list_filter = ('union', 'rasfas', 'created_at')
    search_fields = ('name', 'code')
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

    


@admin.register(Product)
class ProductAdmin(BaseAdmin):
    list_display = ('id', 'name', 'category_name', 'code', 'price', 'unit', 'price_display',  'top', 'bottom')
    list_filter = ('category__union', 'category', 'unit')
    search_fields = ('name', 'code')
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

    @admin.display(description='Category')
    def category_name(self, obj):
        return obj.category.name if obj.category else '-'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('category', 'unit')


@admin.register(TochkaProduct)
class TochkaProductAdmin(BaseAdmin):
    list_display = ('id', 'product_name', 'ntochka_name', 'last_price', 'is_udalen', 'created_at')
    list_filter = ('is_udalen', 'is_active', 'ntochka')
    search_fields = ('product__name', 'id')
    ordering = ('-id',)
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 50
    raw_id_fields = ('product', 'ntochka', 'hudud')
    show_full_result_count = False

    @admin.display(description='Product')
    def product_name(self, obj):
        return f"{obj.product.name}" if obj.product else '-'

    @admin.display(description='NTochka')
    def ntochka_name(self, obj):
        return f"{obj.ntochka.name}" if obj.ntochka else '-'


    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('product', 'ntochka', 'hudud')


@admin.register(TochkaProductHistory)
class TochkaProductHistoryAdmin(BaseAdmin):
    list_display = ('id', 'price', 'employee', 'period', 'status_display', 'created_at')
    list_filter = (
        'status',
        'is_active',
        'is_checked',
        # 'product',
        # 'ntochka',
        # 'hudud',
    )
    search_fields = ('employee__full_name', 'id')
    ordering = ('-id',)
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    list_per_page = 30
    raw_id_fields = ('tochka_product', 'ntochka', 'hudud', 'product', 'employee', 'period', 'alternative_for')
    show_full_result_count = False  # Jami sonini hisoblashni o'chirish - juda tezlashtiradi!

    # N+1 query muammosini hal qilish
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'tochka_product',
            'employee',
            'period',
            'product',
        ).only(
            'id', 'price', 'status', 'is_active', 'is_checked', 'created_at',
            'employee__full_name', 'employee__id',
            'period__id', 'period__date',
            'tochka_product__id',
            'product__id', 'product__name',
        )
    
    # Form sahifasi uchun alohida optimizatsiya
    def get_object(self, request, object_id, from_field=None):
        """
        Form sahifasida obyektni olishda ham optimizatsiya qilish
        """
        queryset = self.get_queryset(request)
        model = queryset.model
        field = model._meta.pk if from_field is None else model._meta.get_field(from_field)
        
        try:
            object_id = field.to_python(object_id)
            return queryset.get(**{field.name: object_id})
        except (model.DoesNotExist, ValidationError, ValueError):
            return None
    
    def status_display(self, obj):
        status_colors = {
            'mavjud': '#28a745',
            'chegirma': '#ffc107', 
            'mavsumiy': '#6c757d',
            'vaqtinchalik': '#fd7e14',
            'sotilmayapti': '#dc3545',
            'obyekt_yopilgan': '#6f42c1'
        }
        color = status_colors.get(obj.status, '#6c757d')
        status_text = dict(obj.PRODUCT_STATUS_CHOICES).get(obj.status, obj.status)
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>', 
            color, 
            status_text
        )
    status_display.short_description = 'Status'
    status_display.admin_order_field = 'status'
    
    # Fieldsets - form sahifasi uchun
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': (
                'tochka_product',
                'employee', 
                'period',
                'hudud',
                'ntochka',
                'product',
            )
        }),
        ('Narx ma\'lumotlari', {
            'fields': (
                'price', 
                'unit_miqdor', 
                'unit_price'
            )
        }),
        ('Status va holatlar', {
            'fields': (
                'status',
                'is_checked',
                'is_active',
                'is_alternative',
                'is_from_application',
                'alternative_for'
            )
        }),
        ('Vaqt ma\'lumotlari', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    # ForeignKey dropdown optimizatsiyasi
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        
        if db_field.name == "employee":
            kwargs["queryset"] = Employee.objects.order_by('full_name')
        elif db_field.name == "period":
            kwargs["queryset"] = PeriodDate.objects.filter(period__is_active=True).order_by('-created_at')
        # elif db_field.name == "alternative_for":
        #     kwargs["queryset"] = TochkaProductHistory.objects.select_related(
        #         'product', 'hudud'
        #     ).order_by('-created_at')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    # Form classini custom qilish
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        # Agar obj mavjud bo'lsa, faqat kerakli querysetlarni yuklash
        # if obj:
        #     # Alternative_for uchun faqat bir xil product va hudud bo'yicha
        #     form.base_fields['alternative_for'].queryset = (
        #         TochkaProductHistory.objects
        #         .filter(product=obj.product, hudud=obj.hudud)
        #         .exclude(id=obj.id)
        #         .select_related('product', 'hudud')
        #         .order_by('-created_at')[:50]  # Faqat oxirgi 50 ta
        #     )
        
        return form
    
    # Bulk actions
    actions = ['make_active', 'make_inactive', 'mark_as_checked']
    
    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} ta yozuv faollashtirildi.')
    make_active.short_description = "Tanlangan yozuvlarni faollashtirish"
    
    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} ta yozuv nofaollashtirildi.')
    make_inactive.short_description = "Tanlangan yozuvlarni nofaollashtirish"
    
    def mark_as_checked(self, request, queryset):
        updated = queryset.update(is_checked=True)
        self.message_user(request, f'{updated} ta yozuv tekshirildi deb belgilandi.')
    mark_as_checked.short_description = "Tanlangan yozuvlarni tekshirildi deb belgilash"


@admin.register(Application)
class ApplicationAdmin(BaseAdmin):
    list_display = ('id','application_type', 'is_active_display')
    list_editable = ('is_active',)
    list_filter = ('application_type',)

    @admin.display(boolean=True, description='Faol')
    def is_active_display(self, obj):
        return obj.is_active