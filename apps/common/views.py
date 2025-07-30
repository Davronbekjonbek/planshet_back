import csv
import zipfile
import io
from datetime import datetime
from django.contrib import admin
from django.urls import path
from django.http import HttpResponse
from django.utils.safestring import mark_safe

from apps.form.models import *
from apps.home.models import *
from apps.common.models import  *


def export_all_csv_zip(request):
    """Namuna formatida CSV fayllarni ZIP da export qilish"""

    # ZIP fayl yaratish
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:

        # 1. period.csv - PeriodDate dan
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(['id', 'day'])
        for period_date in PeriodDate.objects.all():
            writer.writerow([
                period_date.id,
                period_date.date.strftime('%d.%m.%Y')
            ])
        zip_file.writestr('period.csv', csv_buffer.getvalue())

        # 2. products.csv - TochkaProduct dan
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(['name', 'label', 'tochka_rasta_id', 'price', 'group', 'rasfasovka', 'upakofka', 'birlik'])
        for tochka_product in TochkaProduct.objects.select_related('product', 'ntochka', 'product__unit',
                                                                   'product__category'):
            writer.writerow([
                tochka_product.product.id,
                tochka_product.product.name,
                tochka_product.ntochka.id,
                tochka_product.last_price,
                tochka_product.product.category.name if tochka_product.product.category else '',
                1000,  # default rasfasovka
                1000,  # default upakofka
                tochka_product.product.unit.name
            ])
        zip_file.writestr('products.csv', csv_buffer.getvalue())

        # 3. tochka.csv - Tochka dan
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(['name', 'label', 'tochka_id', 'lat', 'lon', 'user_id'])
        for tochka in Tochka.objects.all():
            writer.writerow([
                tochka.id,
                tochka.name,
                tochka.id,
                tochka.lat,
                tochka.lon,
                tochka.employee.id
            ])
        zip_file.writestr('tochka.csv', csv_buffer.getvalue())

        # 4. users.csv - Employee dan
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(['id', 'login', 'parol'])
        for employee in Employee.objects.all():
            writer.writerow([
                employee.id,
                employee.login,
                employee.password
            ])
        zip_file.writestr('users.csv', csv_buffer.getvalue())

    zip_buffer.seek(0)

    # ZIP faylni qaytarish
    response = HttpResponse(zip_buffer.read(), content_type='application/zip')
    response[
        'Content-Disposition'] = f'attachment; filename="export_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip"'

    return response

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.generic import ListView, DetailView, TemplateView
from django.db.models import Avg, Min, Max, Count, Q, F, Sum, Value, CharField
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, Concat
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
import pandas as pd
from datetime import datetime, timedelta
import json
from io import BytesIO
import xlsxwriter
import csv

from apps.home.models import (
    Tochka, NTochka, Region, District, 
    Employee, Period, PeriodDate
)
from apps.form.models import (
    TochkaProductHistory, TochkaProduct, 
    Product, ProductCategory, Birlik, Application
)

class MonitoringDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'monitoring/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get filter parameters
        region_id = self.request.GET.get('region')
        district_id = self.request.GET.get('district')
        period_id = self.request.GET.get('period')
        category_id = self.request.GET.get('category')
        product_id = self.request.GET.get('product')
        status = self.request.GET.get('status')
        employee_id = self.request.GET.get('employee')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        # Base queryset with optimized prefetch/select
        history_qs = TochkaProductHistory.objects.select_related(
            'product', 'ntochka', 'hudud', 'employee', 'period',
            'hudud__district', 'hudud__district__region',
            'product__category', 'product__unit'
        ).prefetch_related(
            'tochka_product',
            'product__category__union'
        ).all()
        
        # Apply filters
        filters = {}
        
        if region_id:
            filters['hudud__district__region_id'] = region_id
            context['selected_region'] = Region.objects.get(id=region_id)
        
        if district_id:
            filters['hudud__district_id'] = district_id
            context['selected_district'] = District.objects.get(id=district_id)
        
        if period_id:
            filters['period_id'] = period_id
            context['selected_period'] = PeriodDate.objects.get(id=period_id)
        
        if category_id:
            filters['product__category_id'] = category_id
            context['selected_category'] = ProductCategory.objects.get(id=category_id)
        
        if product_id:
            filters['product_id'] = product_id
            context['selected_product'] = Product.objects.get(id=product_id)
        
        if status:
            filters['status'] = status
            context['selected_status'] = status
            
        if employee_id:
            filters['employee_id'] = employee_id
            context['selected_employee'] = Employee.objects.get(id=employee_id)
        
        # Date range filtering
        if date_from and date_to:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                filters['period__date__range'] = [date_from_obj, date_to_obj]
                context['date_from'] = date_from
                context['date_to'] = date_to
            except ValueError:
                pass
                
        # Limit to recent data if no period or date range specified
        if not period_id and not (date_from and date_to):
            latest_period = PeriodDate.objects.order_by('-date').first()
            if latest_period:
                filters['period'] = latest_period
                context['selected_period'] = latest_period
        
        # Apply all filters
        history_qs = history_qs
        print
        # Add to context
        context['history_records'] = history_qs
        context['total_count'] = history_qs.count()
        
        # Dropdown data for filters
        context['regions'] = Region.objects.all().order_by('name')
        
        if region_id:
            context['districts'] = District.objects.filter(region_id=region_id).order_by('name')
        else:
            context['districts'] = District.objects.all().order_by('name')
            
        context['periods'] = PeriodDate.objects.select_related('period').order_by('-date')[:50]
        context['categories'] = ProductCategory.objects.all().order_by('name')
        
        if category_id:
            context['products'] = Product.objects.filter(category_id=category_id).order_by('name')
        else:
            context['products'] = Product.objects.all().order_by('name')[:100]
            
        context['employees'] = Employee.objects.all().order_by('full_name')
        context['status_choices'] = dict(TochkaProductHistory.PRODUCT_STATUS_CHOICES)
        
        # Statistics
        context['stats'] = {
            'avg_price': history_qs.aggregate(Avg('price'))['price__avg'],
            'max_price': history_qs.aggregate(Max('price'))['price__max'],
            'min_price': history_qs.aggregate(Min('price'))['price__min'],
            'total_records': history_qs.count(),
            'unique_products': history_qs.values('product_id').distinct().count(),
            'unique_tochkas': history_qs.values('hudud_id').distinct().count()
        }
        
        # Price trend data (for charts)
        if product_id or category_id:
            # Get trend data for specific product or category
            trend_data = self._get_price_trend_data(history_qs)
            context['trend_data'] = json.dumps(trend_data)
            
            # Product price comparison across regions
            if product_id:
                region_comparison = self._get_region_comparison(product_id)
                context['region_comparison'] = json.dumps(region_comparison)
        
        # Top 10 most expensive products
        top_products = TochkaProductHistory.objects.filter(
            is_active=True, 
            period=context.get('selected_period')
        ).select_related(
            'product', 'product__category'
        ).values(
            'product__name', 'product__category__name'
        ).annotate(
            avg_price=Avg('price')
        ).order_by('-avg_price')[:10]
        
        context['top_products'] = list(top_products)
        
        return context
    
    def _get_price_trend_data(self, queryset):
        """Generate price trend data for charts"""
        trends = queryset.values('period__date').annotate(
            avg_price=Avg('price'),
            date_str=Concat(
                F('period__date__year'), Value('-'), 
                F('period__date__month'), Value('-'),
                F('period__date__day'), 
                output_field=CharField()
            )
        ).order_by('period__date')
        
        return {
            'labels': [t['date_str'] for t in trends],
            'data': [float(t['avg_price']) if t['avg_price'] else 0 for t in trends]
        }
    
    def _get_region_comparison(self, product_id):
        """Compare product prices across regions"""
        comparison = TochkaProductHistory.objects.filter(
            product_id=product_id, 
            is_active=True
        ).select_related(
            'hudud__district__region'
        ).values(
            'hudud__district__region__name'
        ).annotate(
            avg_price=Avg('price')
        ).order_by('hudud__district__region__name')
        
        return {
            'labels': [c['hudud__district__region__name'] for c in comparison],
            'data': [float(c['avg_price']) if c['avg_price'] else 0 for c in comparison]
        }


class ProductHistoryDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'monitoring/product_detail.html'
    context_object_name = 'product'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        product = self.get_object()
        
        # Get history for this product
        history = TochkaProductHistory.objects.filter(
            product=product, 
            is_active=True
        ).select_related(
            'hudud', 'hudud__district', 'hudud__district__region',
            'ntochka', 'employee', 'period'
        ).order_by('-period__date', 'hudud__district__region__name')
        
        # Filter by region if specified
        region_id = self.request.GET.get('region')
        if region_id:
            history = history.filter(hudud__district__region_id=region_id)
            context['selected_region'] = Region.objects.get(id=region_id)
            
        # Filter by district if specified
        district_id = self.request.GET.get('district')
        if district_id:
            history = history.filter(hudud__district_id=district_id)
            context['selected_district'] = District.objects.get(id=district_id)
            
        # Price trends over time
        price_trends = history.values('period__date').annotate(
            avg_price=Avg('price'),
            min_price=Min('price'),
            max_price=Max('price')
        ).order_by('period__date')
        
        # Convert to chart-friendly format
        trend_data = {
            'labels': [t['period__date'].strftime('%Y-%m-%d') for t in price_trends],
            'avg': [float(t['avg_price']) if t['avg_price'] else 0 for t in price_trends],
            'min': [float(t['min_price']) if t['min_price'] else 0 for t in price_trends],
            'max': [float(t['max_price']) if t['max_price'] else 0 for t in price_trends]
        }
        
        context['history'] = history[:500]  # Limit for performance
        context['trend_data'] = json.dumps(trend_data)
        context['regions'] = Region.objects.all()
        context['districts'] = District.objects.all() if not region_id else District.objects.filter(region_id=region_id)
        
        return context


class RegionComparisonView(LoginRequiredMixin, TemplateView):
    template_name = 'monitoring/region_comparison.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get selected period
        period_id = self.request.GET.get('period')
        if period_id:
            period = PeriodDate.objects.get(id=period_id)
        else:
            period = PeriodDate.objects.order_by('-date').first()
            
        context['selected_period'] = period
        context['periods'] = PeriodDate.objects.select_related('period').order_by('-date')[:30]
        
        # Get selected category
        category_id = self.request.GET.get('category')
        if category_id:
            category = ProductCategory.objects.get(id=category_id)
            context['selected_category'] = category
            
            # Get average prices by region for this category
            region_data = TochkaProductHistory.objects.filter(
                period=period,
                product__category=category,
                is_active=True
            ).select_related(
                'hudud__district__region'
            ).values(
                'hudud__district__region__name'
            ).annotate(
                avg_price=Avg('price')
            ).order_by('hudud__district__region__name')
            
            comparison_data = {
                'labels': [r['hudud__district__region__name'] for r in region_data],
                'data': [float(r['avg_price']) if r['avg_price'] else 0 for r in region_data]
            }
            
            context['comparison_data'] = json.dumps(comparison_data)
            
        context['categories'] = ProductCategory.objects.all().order_by('name')
        
        return context


@login_required
def export_to_excel(request):
    """Export filtered data to Excel"""
    # Get filter parameters
    region_id = request.GET.get('region')
    district_id = request.GET.get('district')
    period_id = request.GET.get('period')
    category_id = request.GET.get('category')
    product_id = request.GET.get('product')
    status = request.GET.get('status')
    employee_id = request.GET.get('employee')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Base queryset with necessary joins
    queryset = TochkaProductHistory.objects.select_related(
        'product', 'ntochka', 'hudud', 'employee', 'period',
        'hudud__district', 'hudud__district__region',
        'product__category', 'product__unit'
    ).filter(is_active=True)
    
    # Apply filters
    filters = {}
    
    if region_id:
        filters['hudud__district__region_id'] = region_id
    
    if district_id:
        filters['hudud__district_id'] = district_id
    
    if period_id:
        filters['period_id'] = period_id
    
    if category_id:
        filters['product__category_id'] = category_id
    
    if product_id:
        filters['product_id'] = product_id
    
    if status:
        filters['status'] = status
        
    if employee_id:
        filters['employee_id'] = employee_id
    
    # Date range filtering
    if date_from and date_to:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            filters['period__date__range'] = [date_from_obj, date_to_obj]
        except ValueError:
            pass
    
    # Apply all filters
    queryset = queryset.filter(**filters)
    
    # Create DataFrame
    data = list(queryset.values(
        'product__name', 'product__category__name', 'hudud__name', 
        'ntochka__name', 'hudud__district__name', 'hudud__district__region__name',
        'price', 'unit_price', 'unit_miqdor', 'product__unit__name',
        'employee__full_name',  'status', 'product__is_index'
    ))
    
    if not data:
        # Return empty response or error
        return HttpResponse("No data to export")
    
    df = pd.DataFrame(data)
    
    # Rename columns for better readability
    column_mapping = {
        'product__name': 'Mahsulot',
        'product__category__name': 'Kategoriya',
        'hudud__name': 'Obyekt',
        'ntochka__name': 'Rasta',
        'hudud__district__name': 'Tuman',
        'hudud__district__region__name': 'Viloyat',
        'price': 'Narx',
        'unit_price': 'Birlik narxi',
        'unit_miqdor': 'Birlik miqdori',
        'product__unit__name': "O'lchov birligi",
        'employee__full_name': 'Xodim',
        'product__is_index': 'Indekslangan',
        # 'period__date': 'Sana',
        'status': 'Status',
        # 'created_at': 'Yaratilgan vaqt'
    }
    
    df.rename(columns=column_mapping, inplace=True)
    
    # Create Excel file
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Mahsulot narxlari', index=False)
        
        # Get workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets['Mahsulot narxlari']
        
        # Add formats
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        # Write the column headers with the defined format
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            worksheet.set_column(col_num, col_num, 15)  # Set column width
            
        # Add summary sheet
        summary_data = {
            'Metrics': [
                'Jami mahsulotlar soni',
                'O\'rtacha narx',
                'Eng yuqori narx',
                'Eng past narx',
                'Viloyatlar soni',
                'Tumanlar soni',
                'Obyektlar soni'
            ],
            'Values': [
                queryset.count(),
                queryset.aggregate(Avg('price'))['price__avg'],
                queryset.aggregate(Max('price'))['price__max'],
                queryset.aggregate(Min('price'))['price__min'],
                queryset.values('hudud__district__region_id').distinct().count(),
                queryset.values('hudud__district_id').distinct().count(),
                queryset.values('hudud_id').distinct().count()
            ]
        }
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Statistika', index=False)
        
        # Format summary sheet
        summary_sheet = writer.sheets['Statistika']
        for col_num, value in enumerate(summary_df.columns.values):
            summary_sheet.write(0, col_num, value, header_format)
            summary_sheet.set_column(col_num, col_num, 20)
    
    # Set up response
    output.seek(0)
    filename = f'mahsulot_narxlari_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


@login_required
def export_to_csv(request):
    """Export filtered data to CSV"""
    # Get filter parameters (same as Excel export)
    region_id = request.GET.get('region')
    district_id = request.GET.get('district')
    period_id = request.GET.get('period')
    category_id = request.GET.get('category')
    product_id = request.GET.get('product')
    status = request.GET.get('status')
    employee_id = request.GET.get('employee')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Apply filters (same logic as in Excel export)
    queryset = TochkaProductHistory.objects.select_related(
        'product', 'ntochka', 'hudud', 'employee', 'period',
        'hudud__district', 'hudud__district__region',
        'product__category', 'product__unit'
    ).filter(is_active=True)
    
    filters = {}
    
    if region_id:
        filters['hudud__district__region_id'] = region_id
    if district_id:
        filters['hudud__district_id'] = district_id
    if period_id:
        filters['period_id'] = period_id
    if category_id:
        filters['product__category_id'] = category_id
    if product_id:
        filters['product_id'] = product_id
    if status:
        filters['status'] = status
    if employee_id:
        filters['employee_id'] = employee_id
    if date_from and date_to:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            filters['period__date__range'] = [date_from_obj, date_to_obj]
        except ValueError:
            pass
    
    queryset = queryset.filter(**filters)
    
    # Set up response
    response = HttpResponse(content_type='text/csv')
    filename = f'mahsulot_narxlari_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Create CSV writer
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'Mahsulot', 'Kategoriya', 'Obyekt', 'Rasta', 'Tuman', 'Viloyat',
        'Narx', 'Birlik narxi', 'Birlik miqdori', "O'lchov birligi",
        'Xodim',  'Status'
    ])
    
    # Write data
    for item in queryset:
        writer.writerow([
            item.product.name, 
            item.product.category.name,
            item.hudud.name, 
            item.ntochka.name,
            item.hudud.district.name,
            item.hudud.district.region.name,
            item.price,
            item.unit_price,
            item.unit_miqdor,
            item.product.unit.name,
            item.employee.full_name,
            # item.period.date,
            item.get_status_display(),
            # item.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return response