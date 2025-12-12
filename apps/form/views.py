from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
import json

from .models import Application, TochkaProductHistory, TochkaProduct
from apps.home.models import Employee, PeriodDate, Tochka, NTochka


class ApplicationListView(LoginRequiredMixin, ListView):
    model = Application
    template_name = 'applications/application_list.html'
    context_object_name = 'applications'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Application.objects.select_related(
            'employee', 'checked_by', 'period', 'tochka', 'ntochka'
        ).prefetch_related('tochkas', 'ntochkas')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status == 'pending':
            queryset = queryset.filter(is_checked=False)
        elif status == 'approved':
            queryset = queryset.filter(is_checked=True, is_active=True)
        elif status == 'rejected':
            queryset = queryset.filter(is_checked=True, is_active=False)
        
        # Filter by type
        app_type = self.request.GET.get('type')
        if app_type:
            queryset = queryset.filter(application_type=app_type)
        
        # Filter by period
        period_id = self.request.GET.get('period')
        if period_id:
            queryset = queryset.filter(period_id=period_id)
        
        # Filter by employee
        employee_id = self.request.GET.get('employee')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(employee__full_name__icontains=search) |
                Q(tochka__name__icontains=search) |
                Q(ntochka__name__icontains=search) |
                Q(comment__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistics
        context['total_applications'] = Application.objects.count()
        context['pending_applications'] = Application.objects.filter(is_checked=False).count()
        context['approved_applications'] = Application.objects.filter(is_checked=True, is_active=True).count()
        context['rejected_applications'] = Application.objects.filter(is_checked=True, is_active=False).count()
        
        # Filters data
        context['periods'] = PeriodDate.objects.all().order_by('-id')
        context['employees'] = Employee.objects.all().order_by('full_name')
        
        # Current filters
        context['current_status'] = self.request.GET.get('status', '')
        context['current_type'] = self.request.GET.get('type', '')
        context['current_period'] = self.request.GET.get('period', '')
        context['current_employee'] = self.request.GET.get('employee', '')
        context['search_query'] = self.request.GET.get('search', '')
        
        return context


class ApplicationDetailView(LoginRequiredMixin, DetailView):
    model = Application
    template_name = 'applications/application_detail.html'
    context_object_name = 'application'
    
    def get_object(self):
        return get_object_or_404(
            Application.objects.select_related(
                'employee', 'checked_by', 'period', 'tochka', 'ntochka'
            ).prefetch_related('tochkas', 'ntochkas'),
            pk=self.kwargs['pk']
        )


@login_required
@require_POST
def approve_application(request, pk):
    """Arizani tasdiqlash"""
    application = get_object_or_404(Application, pk=pk)
    
    if application.is_checked:
        messages.warning(request, 'Bu ariza allaqachon tekshirilgan!')
        return redirect('form:application_list')
    
    try:
        # Mark as checked and approved
        application.is_checked = True
        application.is_active = True
        application.checked_by = request.user
        application.checked_at = timezone.now()
        
        # Process based on application type
        if application.application_type == 'for_close_rasta':
            # Close rastas
            for ntochka in application.ntochkas.all():
                ntochka.is_active = False
                ntochka.save()
                
                # Deactivate all products in this rasta
                TochkaProduct.objects.filter(ntochka=ntochka).update(is_active=False)
                NTochka.objects.filter(ntochka=ntochka).update(is_active=False)
        
        elif application.application_type == 'for_open_rasta':
            # Open rastas
            for ntochka in application.ntochkas.all():
                ntochka.is_active = False
                ntochka.save()
                
                # Process products if any
                if application.products:
                    for product_data in application.products:
                        product_id = product_data.get('product_id')
                        if product_id:
                            TochkaProduct.objects.update_or_create(
                                product_id=product_id,
                                ntochka=ntochka,
                                hudud=application.tochka,
                                defaults={
                                    'is_active': False,
                                    'last_price': product_data.get('price', 0),
                                    'miqdor': product_data.get('miqdor', 0)
                                }
                            )
        
        elif application.application_type == 'for_close_obyekt':
            # Close obyekt
            if application.tochka:
                application.tochka.is_active = False
                application.tochka.save()
                
                # Deactivate all products and rastas in this obyekt
                NTochka.objects.filter(tochka=application.tochka).update(is_active=False)
                TochkaProduct.objects.filter(hudud=application.tochka).update(is_active=False)
        
        elif application.application_type == 'for_open_obyekt':
            # Open obyekt
            if application.tochka:
                application.tochka.is_active = False
                application.tochka.save()
        
        application.save()
        
        messages.success(request, 'Ariza muvaffaqiyatli tasdiqlandi!')
        
        # Return JSON response for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'Ariza tasdiqlandi'
            })
        
    except Exception as e:
        messages.error(request, f'Xatolik yuz berdi: {str(e)}')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return redirect('form:application_list')


@login_required
@require_POST
def reject_application(request, pk):
    """Arizani rad etish"""
    application = get_object_or_404(Application, pk=pk)
    
    if application.is_checked:
        messages.warning(request, 'Bu ariza allaqachon tekshirilgan!')
        return redirect('form:application_list')
    
    try:
        # Mark as checked but not active (rejected)
        application.is_checked = True
        application.is_active = False
        application.checked_by = request.user
        application.checked_at = timezone.now()
        
        # Add rejection comment if provided
        comment = request.POST.get('rejection_comment')
        if comment:
            application.comment = f"Rad etish sababi: {comment}"
        
        application.save()
        
        messages.success(request, 'Ariza rad etildi!')
        
        # Return JSON response for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'Ariza rad etildi'
            })
        
    except Exception as e:
        messages.error(request, f'Xatolik yuz berdi: {str(e)}')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return redirect('form:application_list')


@login_required
def application_detail_ajax(request, pk):
    """AJAX orqali ariza tafsilotlarini olish"""
    application = get_object_or_404(
        Application.objects.select_related(
            'employee', 'checked_by', 'period', 'tochka', 'ntochka'
        ).prefetch_related('tochkas', 'ntochkas'),
        pk=pk
    )
    
    data = {
        'id': application.id,
        'application_type': application.get_application_type_display(),
        'employee': application.employee.full_name,
        'period': str(application.period),
        'created_at': application.created_at.strftime('%d.%m.%Y %H:%M'),
        'is_checked': application.is_checked,
        'is_active': application.is_active,
        'comment': application.comment or '',
        'products': application.products or [],
        'detail': application.detail or [],
    }
    
    # Add location info
    if application.tochka:
        data['tochka'] = {
            'id': application.tochka.id,
            'name': application.tochka.name,
            'address': application.tochka.address or '',
            'is_inDSQ': getattr(application.tochka, 'is_inDSQ', None)
        }
    
    if application.ntochka:
        data['ntochka'] = {
            'id': application.ntochka.id,
            'name': application.ntochka.name,
            'is_inDSQ': getattr(application.ntochka, 'is_inDSQ', None)
        }
    
    # Add multiple locations
    if application.tochkas.exists():
        data['tochkas'] = [
            {'id': t.id, 'name': t.name, 'address': t.address or '', 'is_inDSQ': getattr(t, 'is_inDSQ', None)}
            for t in application.tochkas.all()
        ]
    
    if application.ntochkas.exists():
        data['ntochkas'] = [
            {'id': n.id, 'name': n.name, 'is_inDSQ': getattr(n, 'is_inDSQ', None)}
            for n in application.ntochkas.all()
        ]
    
    # Add checker info if checked
    if application.is_checked and application.checked_by:
        data['checked_by'] = application.checked_by.get_full_name()
        data['checked_at'] = application.checked_at.strftime('%d.%m.%Y %H:%M') if application.checked_at else ''
    
    return JsonResponse(data)


@login_required
def get_application_statistics(request):
    """Ariza statistikalarini olish"""
    period_id = request.GET.get('period')
    
    queryset = Application.objects.all()
    if period_id:
        queryset = queryset.filter(period_id=period_id)
    
    stats = {
        'total': queryset.count(),
        'pending': queryset.filter(is_checked=False).count(),
        'approved': queryset.filter(is_checked=True, is_active=True).count(),
        'rejected': queryset.filter(is_checked=True, is_active=False).count(),
        'by_type': {}
    }
    
    # Statistics by type
    for app_type, display in Application.APPLICATION_TYPE_CHOICES:
        count = queryset.filter(application_type=app_type).count()
        stats['by_type'][app_type] = {
            'display': display,
            'count': count
        }
    
    return JsonResponse(stats)