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
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.generic import ListView, DetailView, TemplateView
from django.db.models import Avg, Min, Max, Count, Q, F, Sum, Value, CharField, Case, When, IntegerField, Prefetch
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, Concat
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
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
        
        selected_period = None
        per_page = 50

        # Base queryset with optimized prefetch/select
        history_qs = TochkaProductHistory.objects.select_related(
            'product', 'ntochka', 'hudud', 'employee', 'period',
            'hudud__district', 'hudud__district__region',
            'product__category', 'product__unit'
        ).prefetch_related(
            'tochka_product',
        ).filter(is_active=True)
        
        # Apply filters
        filters = {}
        
        if region_id:
            filters['hudud__district__region_id'] = region_id
            context['selected_region'] = Region.objects.get(id=region_id)
        
        if district_id:
            filters['hudud__district_id'] = district_id
            context['selected_district'] = District.objects.get(id=district_id)
        
        if period_id:
            try:
                selected_period = Period.objects.get(id=period_id)
                filters['period__period_id'] = period_id
            except Period.DoesNotExist:
                selected_period = None
        
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
                
        # Limit to latest period if nothing specified to keep view fast
        if not filters.get('period__period_id') and not (date_from and date_to):
            latest_period = PeriodDate.objects.select_related('period').order_by('-date').first()
            if latest_period:
                filters['period__period_id'] = latest_period.period_id
                selected_period = latest_period.period
        
        # Apply all filters
        history_qs = history_qs.filter(**filters).order_by('-period__date', '-id')
        context['selected_period'] = selected_period

        total_count = history_qs.count()
        # Add to context
        paginator = Paginator(history_qs, per_page)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        query_params = self.request.GET.copy()
        if 'page' in query_params:
            query_params.pop('page')
        context['query_string'] = query_params.urlencode()

        context['history_records'] = page_obj.object_list
        context['page_obj'] = page_obj
        context['paginator'] = paginator
        context['total_count'] = total_count
        context['per_page'] = per_page
        
        # Dropdown data for filters
        context['regions'] = Region.objects.all().order_by('name')
        
        if region_id:
            context['districts'] = District.objects.filter(region_id=region_id).order_by('name')
        else:
            context['districts'] = District.objects.all().order_by('name')
            
        context['periods'] = Period.objects.filter(is_active=True).order_by('-id')
        context['categories'] = ProductCategory.objects.all().order_by('name')
        
        if category_id:
            context['products'] = Product.objects.filter(category_id=category_id).order_by('name')
        else:
            context['products'] = Product.objects.all().order_by('name')[:100]
            
        context['employees'] = Employee.objects.all().order_by('full_name')
        context['status_choices'] = dict(TochkaProductHistory.PRODUCT_STATUS_CHOICES)
        
        # Statistics
        aggregates = history_qs.aggregate(
            avg_price=Avg('price'),
            max_price=Max('price'),
            min_price=Min('price')
        )
        context['stats'] = {
            'avg_price': aggregates['avg_price'],
            'max_price': aggregates['max_price'],
            'min_price': aggregates['min_price'],
            'total_records': total_count,
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
                region_monitoring = self._get_region_monitoring(
                    product_id,
                    selected_period.id if selected_period else None
                )
                context['region_monitoring'] = json.dumps(region_monitoring)
        
        # Top 10 most expensive products
        top_products = history_qs.values(
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
    
    def _get_region_monitoring(self, product_id, period_id=None):
        """Compare product prices across regions"""
        comparison = TochkaProductHistory.objects.filter(
            product_id=product_id, 
            is_active=True
        )

        if period_id:
            comparison = comparison.filter(period__period_id=period_id)

        comparison = comparison.select_related(
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


class RegionMonitoringView(LoginRequiredMixin, TemplateView):
    template_name = 'monitoring/region_monitoring.html'

    def get(self, request, *args, **kwargs):
        if request.GET.get('export') == 'excel':
            return self.export_excel()
        return super().get(request, *args, **kwargs)

    def export_excel(self):
        context = self.get_context_data(**self.kwargs)
        data = context['data']
        
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet("Monitoring")
        
        # Headers
        headers = ['Nomi', 'SOATO', 'Jami obyektlar', 'Kiritilgan', 'Foiz', "Mas'ul xodimlar"]
        header_format = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1})
        
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
            worksheet.set_column(col, col, 20)
            
        # Data
        for row, item in enumerate(data, start=1):
            worksheet.write(row, 0, item['name'])
            worksheet.write(row, 1, item.get('soato', ''))
            worksheet.write(row, 2, item['total'])
            worksheet.write(row, 3, item['entered'])
            worksheet.write(row, 4, f"{item['percent']}%")
            employees = ", ".join([e.full_name for e in item['employees']])
            worksheet.write(row, 5, employees)
            
        # Total Row
        if 'total_data' in context:
            total = context['total_data']
            row += 1
            worksheet.write(row, 0, "Jami", header_format)
            worksheet.write(row, 1, "", header_format)
            worksheet.write(row, 2, total['total'], header_format)
            worksheet.write(row, 3, total['entered'], header_format)
            worksheet.write(row, 4, f"{total['percent']}%", header_format)
            worksheet.write(row, 5, "", header_format)
            
        workbook.close()
        output.seek(0)
        
        filename = f"monitoring_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 1. Filters - Safe Integer Conversion
        try:
            period_id = int(self.request.GET.get('period', ''))
        except (ValueError, TypeError):
            period_id = None
            
        try:
            date_id = int(self.request.GET.get('date', ''))
        except (ValueError, TypeError):
            date_id = None
            
        try:
            region_id = int(self.request.GET.get('region', ''))
        except (ValueError, TypeError):
            region_id = None
            
        try:
            district_id = int(self.request.GET.get('district', ''))
        except (ValueError, TypeError):
            district_id = None

        try:
            tochka_id = int(self.request.GET.get('tochka', ''))
        except (ValueError, TypeError):
            tochka_id = None
            
        status_filter = self.request.GET.get('status')

        # Context for filters
        context['periods'] = Period.objects.filter(is_active=True).order_by('-id')
        context['regions'] = Region.objects.all().order_by('name')
        
        # Determine target dates
        target_dates = []
        selected_period = None
        selected_date = None

        if period_id:
            selected_period = Period.objects.filter(id=period_id).first()
            context['selected_period'] = selected_period
            # Filter dates by period
            period_dates = PeriodDate.objects.filter(period_id=period_id).order_by('-date')
            context['period_dates'] = period_dates
        
        if date_id:
            selected_date = PeriodDate.objects.filter(id=date_id).first()
            if selected_date:
                target_dates = [selected_date]
                if not selected_period:
                    selected_period = selected_date.period
                    context['selected_period'] = selected_period
                    context['period_dates'] = PeriodDate.objects.filter(period=selected_period).order_by('-date')
        elif selected_period:
            # If period selected but no date, use all dates in period
            target_dates = list(PeriodDate.objects.filter(period=selected_period))
        else:
            # Default to very latest date if nothing selected
            latest_date = PeriodDate.objects.order_by('-date').first()
            if latest_date:
                target_dates = [latest_date]
                selected_date = latest_date
                selected_period = latest_date.period
                context['selected_period'] = selected_period
                context['period_dates'] = PeriodDate.objects.filter(period=selected_period).order_by('-date')

        context['selected_date'] = selected_date

        # 2. Region & District Filters
        if region_id:
            context['districts'] = District.objects.filter(region_id=region_id).order_by('name')
            context['selected_region'] = region_id
        
        if district_id:
            context['selected_district'] = district_id
        
        context['selected_status'] = status_filter

        # 3. Data Aggregation
        data = []
        mode = 'region' # region, district, tochka

        if not target_dates:
             context['data'] = []
             context['mode'] = mode
             return context

        def get_status_class(percent):
            if percent >= 100: return 'bg-success', 'To\'liq'
            elif percent >= 70: return 'bg-warning', 'Yaxshi'
            return 'bg-danger', 'Qoniqarsiz'

        if tochka_id:
            mode = 'product'
            context['selected_tochka'] = Tochka.objects.get(id=tochka_id)
            
            queryset = TochkaProduct.objects.filter(hudud_id=tochka_id, is_active=True).select_related('product', 'product__unit')
            
            # Optimization: Fetch latest history for each product in bulk
            histories = TochkaProductHistory.objects.filter(
                tochka_product__in=queryset,
                period__in=target_dates
            ).select_related('employee').order_by('tochka_product_id', '-period__date')
            
            # Create a map of tochka_product_id -> latest history
            history_map = {}
            for h in histories:
                if h.tochka_product_id not in history_map:
                    history_map[h.tochka_product_id] = h
            
            for obj in queryset:
                history = history_map.get(obj.id)
                
                entered = 1 if history else 0
                percent = 100 if entered else 0
                status_cls, status_text = get_status_class(percent)
                
                data.append({
                    'id': obj.id,
                    'name': obj.product.name,
                    'soato': obj.product.code,
                    'total': 1,
                    'entered': entered,
                    'percent': percent,
                    'employees': [history.employee] if history else [],
                    'status_class': status_cls,
                    'status_text': history.get_status_display() if history else 'Kiritilmagan',
                    'price': history.price if history else 0,
                    'unit': obj.product.unit.name
                })

        elif district_id:
            mode = 'tochka'
            # Show Tochkas in the district
            queryset = Tochka.objects.filter(district_id=district_id, is_active=True).select_related('employee')
            
            # Annotate with entered status
            queryset = queryset.annotate(
                total_products=Count('products', filter=Q(products__is_active=True)),
                entered_products=Count('products', filter=Q(products__is_active=True, products__history__period__in=target_dates), distinct=True)
            )
            
            for obj in queryset:
                total = obj.total_products
                entered = obj.entered_products
                percent = (entered / total * 100) if total > 0 else 0
                status_cls, status_text = get_status_class(percent)
                
                data.append({
                    'id': obj.id,
                    'name': obj.name,
                    'soato': obj.code,
                    'total': total,
                    'entered': entered,
                    'percent': round(percent, 1),
                    'employees': [obj.employee] if obj.employee else [],
                    'status_class': status_cls,
                    'status_text': status_text
                })

        elif region_id:
            mode = 'district'
            # Show Districts in the region
            queryset = District.objects.filter(region_id=region_id, employees__isnull=False).distinct().prefetch_related(
                Prefetch('employees', queryset=Employee.objects.all())
            )
            
            # Annotate total active tochkas
            queryset = queryset.annotate(
                total_tochkas=Count('tochkas', filter=Q(tochkas__is_active=True)),
                entered_tochkas=Count('tochkas', filter=Q(tochkas__is_active=True, tochkas__product_history__period__in=target_dates), distinct=True)
            )

            for obj in queryset:
                total = obj.total_tochkas
                entered = obj.entered_tochkas
                percent = (entered / total * 100) if total > 0 else 0
                status_cls, status_text = get_status_class(percent)
                
                data.append({
                    'id': obj.id,
                    'name': obj.name,
                    'soato': f"{obj.region.code}{obj.code}",
                    'total': total,
                    'entered': entered,
                    'percent': round(percent, 1),
                    'employees': list(obj.employees.all()),
                    'status_class': status_cls,
                    'status_text': status_text
                })

        else:
            mode = 'region'
            # Show All Regions
            # Instead of complex annotation on Region, we aggregate from Districts
            
            # 1. Get all districts that have employees
            districts_qs = District.objects.filter(employees__isnull=False).distinct().annotate(
                total_tochkas=Count('tochkas', filter=Q(tochkas__is_active=True)),
                entered_tochkas=Count('tochkas', filter=Q(tochkas__is_active=True, tochkas__product_history__period__in=target_dates), distinct=True)
            ).select_related('region').prefetch_related('employees')

            # 2. Initialize Region Data
            region_map = {}
            all_regions = Region.objects.all().order_by('name')
            
            for r in all_regions:
                region_map[r.id] = {
                    'obj': r,
                    'total': 0,
                    'entered': 0,
                    'employees': set()
                }
            
            # 3. Aggregate District Data into Regions
            for d in districts_qs:
                if d.region_id in region_map:
                    r_data = region_map[d.region_id]
                    r_data['total'] += d.total_tochkas
                    r_data['entered'] += d.entered_tochkas
                    for emp in d.employees.all():
                        r_data['employees'].add(emp)
            
            # 4. Build final data list
            for r in all_regions:
                r_data = region_map[r.id]
                total = r_data['total']
                entered = r_data['entered']
                percent = (entered / total * 100) if total > 0 else 0
                status_cls, status_text = get_status_class(percent)
                
                data.append({
                    'id': r.id,
                    'name': r.name,
                    'soato': r.code,
                    'total': total,
                    'entered': entered,
                    'percent': round(percent, 1),
                    'employees': list(r_data['employees']),
                    'status_class': status_cls,
                    'status_text': status_text
                })

        # Apply Status Filter
        if status_filter:
            data = [d for d in data if status_filter in d['status_class']]

        context['data'] = data
        context['mode'] = mode
        
        # Calculate Totals
        total_obj = sum(d['total'] for d in data)
        total_ent = sum(d['entered'] for d in data)
        total_percent = (total_ent / total_obj * 100) if total_obj else 0
        status_cls, status_text = get_status_class(total_percent)
        
        context['total_data'] = {
            'total': total_obj,
            'entered': total_ent,
            'percent': round(total_percent, 1),
            'status_class': status_cls,
            'status_text': status_text
        }
        
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
        filters['period__period_id'] = period_id
    
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
        filters['period__period_id'] = period_id
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