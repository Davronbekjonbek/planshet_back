import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings

from apps.form.models import Product, ProductCategory


class Command(BaseCommand):
    help = "Excel faylidan mahsulotlarni bazaga yuklaydi (datas papkadan)"

    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str, help='Excel fayl nomi (datas papkasida)')

    def handle(self, *args, **options):
        base_dir = settings.BASE_DIR
        excel_file = options['excel_file']
        excel_path = os.path.join(base_dir, 'datas', excel_file)

        if not os.path.exists(excel_path):
            self.stdout.write(
                self.style.ERROR(f"Excel fayl topilmadi: {excel_path}")
            )
            return

        try:
            self.import_products(excel_path)

            self.stdout.write(
                self.style.SUCCESS("Mahsulotlar muvaffaqiyatli yuklandi!")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Import jarayonida xatolik: {str(e)}")
            )

    def import_products(self, excel_path):
        """Mahsulotlarni Excel fayldan bazaga yuklash"""
        self.stdout.write("Mahsulotlarni yuklash boshlandi...")

        df = pd.read_excel(excel_path, sheet_name='product')

        imported_count = 0
        existing_count = 0
        errors_count = 0

        for _, row in df.iterrows():
            try:
                category_code = row['kod{8}.cat']
                product_code = str(row['kod_product'])
                product_name = row['nomi']
                product_price = float(row['Narxi'])
                is_import = bool(row['is_import'])
                is_weekly = bool(row['is_weekly'])

                # Kategoriya topish
                category = ProductCategory.objects.filter(code=category_code).first()
                if not category:
                    self.stdout.write(
                        self.style.WARNING(f"Kategoriya topilmadi: {category_code} - {product_name}")
                    )
                    continue

                birlik = category.union  # O'lchov birligi

                top = product_price * 1.2
                bottom = product_price * 0.8

                product, created = Product.objects.get_or_create(
                    code=product_code,
                    defaults={
                        'name': product_name,
                        'category': category,
                        'price': product_price,
                        'top': top,
                        'bottom': bottom,
                        'is_import': is_import,
                        'is_weekly': is_weekly,
                        'unit': birlik
                    }
                )

                if created:
                    imported_count += 1
                else:
                    existing_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Xato: {row.get('nomi', 'Noma\'lum')} - {str(e)}")
                )
                errors_count += 1
                continue

        self.stdout.write(
            self.style.SUCCESS(
                f"Mahsulotlar yuklandi: {imported_count} ta yangi, "
                f"{existing_count} ta mavjud, {errors_count} ta xatolik"
            )
        )
