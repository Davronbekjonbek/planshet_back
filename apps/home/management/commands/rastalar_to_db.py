import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings

from apps.home.models import Tochka, NTochka
from apps.form.models import Product, TochkaProduct


class Command(BaseCommand):
    help = "Excel faylidan rastalar va rasta-mahsulot bog'lanishlarini yuklaydi"

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
            self.import_rastalar(excel_path)

            # 2. Keyin rasta-mahsulot bog'lanishlarini yuklash
            self.import_rasta_products(excel_path)

            self.stdout.write(
                self.style.SUCCESS("Import jarayoni muvaffaqiyatli yakunlandi!")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Xatolik yuz berdi: {str(e)}")
            )

    def import_rastalar(self, excel_path):
        """Rastalarni Excel fayldan bazaga yuklash"""
        self.stdout.write("Rastalarni yuklash boshlandi...")

        # Excel faylni o'qish - rasta varaqasi
        df_rasta = pd.read_excel(excel_path, sheet_name='rasta')

        # Unikal rastalarni olish (nomi va kod.obyekt bo'yicha)
        unique_rastas = df_rasta[['nomi', 'kod.obyekt']].drop_duplicates()

        imported_count = 0
        existing_count = 0

        for _, row in unique_rastas.iterrows():
            try:
                obyekt_name = row['nomi']
                obyekt_code = int(row['kod.obyekt'])

                # Tochka (Obyekt) ni olish
                tochka = Tochka.objects.filter(code=obyekt_code).first()

                if not tochka:
                    self.stdout.write(
                        self.style.WARNING(f"Tochka topilmadi (code={obyekt_code}). Rasta: {obyekt_name}")
                    )
                    continue

                # NTochka (Rasta) ni yaratish
                ntochka, n_created = NTochka.objects.get_or_create(
                    name=obyekt_name,
                    hudud=tochka
                )

                if n_created:
                    imported_count += 1
                else:
                    existing_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Rasta yuklashda xato: {obyekt_name} - {str(e)}")
                )

        self.stdout.write(
            self.style.SUCCESS(f"Rastalar yuklandi: {imported_count} ta yangi, {existing_count} ta mavjud")
        )

    def import_rasta_products(self, excel_path):
        """Rasta-mahsulot bog'lanishlarini Excel fayldan bazaga yuklash"""
        self.stdout.write("Rasta-mahsulot bog'lanishlarini yuklash boshlandi...")

        # Excel faylni o'qish - rasta varaqasi
        df_rasta = pd.read_excel(excel_path, sheet_name='rasta')

        imported_count = 0
        existing_count = 0
        errors_count = 0

        for _, row in df_rasta.iterrows():
            try:
                product_code = str(row['kod_product'])
                rasta_name = row['nomi']

                # Mahsulotni topish
                try:
                    product = Product.objects.get(code=product_code)
                except Product.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f"Mahsulot topilmadi: {product_code}")
                    )
                    errors_count += 1
                    continue

                # Rastani (NTochka) topish - nomi bo'yicha
                try:
                    ntochka = NTochka.objects.get(name=rasta_name)
                except NTochka.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f"Rasta topilmadi: {rasta_name}")
                    )
                    errors_count += 1
                    continue

                # Hudud (Tochka)
                hudud = ntochka.hudud

                # TochkaProduct yaratish yoki yangilash
                tp, created = TochkaProduct.objects.get_or_create(
                    product=product,
                    ntochka=ntochka,
                    defaults={
                        'hudud': hudud,
                        'last_price': product.price,
                        'previous_price': product.price,
                        'is_active': True
                    }
                )

                if created:
                    imported_count += 1
                else:
                    existing_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Rasta-mahsulot bog'lanishini yuklashda xato: {str(e)}")
                )
                errors_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Rasta-mahsulot bog'lanishlari yuklandi: "
                f"{imported_count} ta yangi, {existing_count} ta mavjud, {errors_count} ta xatolik"
            )
        )