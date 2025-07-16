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

