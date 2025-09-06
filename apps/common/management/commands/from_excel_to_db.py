from apps.common.models import *
from apps.form.models import *
from apps.home.models import *

from django.core.management.base import BaseCommand, CommandError

import pandas as pd
import os

file_path = "datas/planshet_data.xlsx"

class Command(BaseCommand):
    help = "Excel fayl topilgan ma'lumotlarni bazaga yuklaydi"

    def read_sheet(self, sheet_name):
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        return df

    def import_employee(self, df):
        imported_count = 0
        existing_count = 0
        errors_count = 0

        for _, row in df.iterrows():
            full_name = str(row.get('fio', '')).strip()
            soato = str(row.get('soato', None))
            is_active = row.get('is_active', 'yes').strip().lower() == 'yes'
            pinfl = str(row.get('pinfl', None))
            phone1 = str(row.get('phone1', None))
            phone2 = str(row.get('phone2', None))
            password = str(row.get('password', None))
            login = str(row.get('soato', None)) or pinfl  # Agar login bo'sh bo'lsa, pinfl ishlatiladi

            # Districtni soato orqali topish
            try:
                district = District.objects.get(code=(soato[4:]), region__code=soato[:4])
            except District.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f"Tuman topilmadi: {soato} - {full_name}")
                )
                errors_count += 1
                continue

            # login unique bo‘lgani uchun mavjudligini tekshirish
            if Employee.objects.filter(login=soato).exists():
                existing_count += 1
                continue

            try:
                Employee.objects.create(
                    full_name=full_name,
                    login=login,
                    password=password,
                    district=district,
                    pinfl=pinfl,
                    phone1=phone1,
                    phone2=phone2,
                    permission_plov=False,
                    status=1.0 if is_active else 0.0,
                    permission1=True,
                    permission2=True,
                    permission3=True,
                    permission4=False,
                    permission5=False,
                    gps_permission=True,
                    lang='uz'
                )
                imported_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Xato: {full_name} - {str(e)}")
                )
                errors_count += 1
        print(Employee.objects.all())
        self.stdout.write(self.style.SUCCESS(
            f"Yangi xodimlar: {imported_count}, mavjud xodimlar: {existing_count}, xatoliklar: {errors_count}"
        ))

    def import_obyekt(self, df):
        imported_count = 0
        existing_count = 0
        errors_count = 0

        for _, row in df.iterrows():
            name = row.get('nomi', '').strip()
            lon = row.get('lon', 0.0) or 0.0
            lat = row.get('lat', 0.0) or 0.0
            is_active = row.get('is_active', True)
            code = row.get('kod', None)
            unique_code = row.get('unique_kod', None)
            inn = row.get('INN', 0)
            is_weekly = row.get('is_weekly', False)

            # ForeignKey lar uchun (masalan: soato orqali District, pinfl orqali Employee qidirish mumkin)
            soato = str(row.get('soato', None))
            pinfl = row.get('pinfl', None)
            try:
                district = District.objects.get(code=(soato[4:]), region__code=soato[:4])
            except District.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f"Tuman topilmadi: {soato} - {name}")
                )
                continue

            try:
                employee = Employee.objects.get(district=district) if district else None
            except Employee.DoesNotExist:
                employee = None

            if not all([district, employee]):
                errors_count += 1
                continue

            # code unique bo‘lsa, mavjudligini tekshiramiz
            if Tochka.objects.filter(code=unique_code).exists():
                existing_count += 1
                continue

            try:
                Tochka.objects.create(
                    name=name,
                    icon='nutrition',          # yoki kerakli qiymat tanlang, default='nutrition'
                    district=district,
                    code=unique_code,
                    inn=inn,
                    pinfl=pinfl,
                    lat=lat,
                    lon=lon,
                    employee=employee,
                    is_active=bool(is_active),
                    weekly_type=int(is_weekly)
                )
                imported_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Xato: {name} - {str(e)}")
                )
                errors_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Yangi obyektlar: {imported_count}, mavjud obyektlar: {existing_count}, xatoliklar: {errors_count}"
        ))

    def import_ntochka(self, df):
        imported_count = 0
        existing_count = 0
        errors_count = 0

        for _, row in df.iterrows():
            name = row.get('nomi', '').strip()
            obyekt_unique = str(row.get('kod_obyekt_unique', None))
            code = str(row.get('kod_unique', None))
            is_weekly = bool(row.get('is_weekly', False))
            print(obyekt_unique, type(obyekt_unique))
            # Kod bo'yicha obyektni (Tochka) topish
            hudud = Tochka.objects.get(code=obyekt_unique)


            # code unique bo‘lgani uchun mavjudligiga tekshiruv
            if NTochka.objects.filter(code=code).exists():
                existing_count += 1
                continue

            try:
                NTochka.objects.create(
                    name=name,
                    hudud=hudud,
                    is_active=True,
                    is_weekly=is_weekly,
                    in_proccess=False,
                    code=code
                )
                imported_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Xato: {name} - {str(e)}")
                )
                errors_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Yangi NTochka: {imported_count}, mavjudlari: {existing_count}, xatoliklar: {errors_count}"
        ))

    def import_category(self, df):
        imported_count = 0
        existing_count = 0
        errors_count = 0

        for _, row in df.iterrows():
            name = (row.get('nomi') or '').strip()
            code3 = row.get('kod{3}', None)
            code8 = row.get('kod{8}', None)
            code = code8
            birlik_nomi = (row.get('birligi') or '').strip()
            rasfas = row.get('rasfas', 1)
            number = code3


            try:
                birligi = Birlik.objects.get(name=birlik_nomi)
            except Birlik.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Birlik topilmadi: {birlik_nomi} {row}"))
                errors_count += 1
                continue

            if ProductCategory.objects.filter(code=code).exists():
                existing_count += 1
                continue

            try:
                ProductCategory.objects.create(
                    name=name,
                    code=code,
                    union=birligi,
                    rasfas=rasfas,
                    number=number,
                )
                imported_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Xato: {name} - {str(e)}"))
                errors_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Yangi kategoriyalar: {imported_count}, mavjudlari: {existing_count}, xatoliklar: {errors_count}"
        ))




    def import_products(self, df):

        imported_count = 0
        existing_count = 0
        errors_count = 0

        for _, row in df.iterrows():
            name = (row.get('nomi') or '').strip()
            code = str(row.get('kod{8}.cat') or '').strip()
            category_code = code  # product category code ham bo‘lishi mumkin, kerak bo‘lsa moslashtiring
            # hbhd = int(row.get('HBHD', 1) or 1)
            is_import = bool(row.get('is_import', False))
            is_weekly = int(row.get('is_weekly', 1) or 1)
            narxi = float(row.get('Narxi', 0) or 0)
            is_special = bool(is_weekly == 3)
            is_index = bool(row.get('is_index', False))
            unique_code = str(row.get('kod_unique') or '').strip()

            try:
                category = ProductCategory.objects.get(code=category_code)
            except ProductCategory.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Kategoriya topilmadi: {category_code}"))
                errors_count += 1
                continue

            # code unique bo‘lsa tekshiramiz
            if Product.objects.filter(code=unique_code).exists():
                existing_count += 1
                continue

            try:
                Product.objects.create(
                    name=name,
                    code=unique_code,
                    category=category,
                    price=narxi,
                    bottom=narxi * 0.8,
                    top=narxi * 1.2,
                    weekly=int(is_weekly),
                    unit=category.union ,
                    hbhd=3,
                    is_import=bool(int(is_import)==1),
                    is_special=is_special,
                    is_index=bool(int(is_weekly)==3),
                )
                imported_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Xato: {name} - {str(e)}"))
                errors_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Yangi mahsulotlar: {imported_count}, mavjudlari: {existing_count}, xatoliklar: {errors_count}"
        ))

    def relate_rasta_hafta_product(self, rasta_hafta):
        imported_count = 0
        existing_count = 0
        errors_count = 0
        error_messages = []

        for _, row in rasta_hafta.iterrows():
            try:
                kod_unique = str(int(row.get('kod_unique', ''))).strip()
                kod_product_unique = str(int(row.get('kod_product_unique', ''))).strip()
                print(kod_product_unique)
                if not kod_unique or not kod_product_unique:
                    errors_count += 1
                    error_messages.append(f"Row {_ + 1}: kod_unique yoki kod_product_unique bo'sh")
                    continue

                try:
                    ntochka = NTochka.objects.get(code=kod_unique)
                except NTochka.DoesNotExist:
                    errors_count += 1
                    error_messages.append(f"Row {_ + 1}: NTochka topilmadi kod_unique={kod_unique}")
                    continue

                try:
                    product = Product.objects.get(code=kod_product_unique)
                except Product.DoesNotExist:
                    errors_count += 1
                    error_messages.append(f"Row {_ + 1}: Product topilmadi kod_product_unique={kod_product_unique}")
                    continue

                tochka_product = TochkaProduct.objects.create(
                    hudud = ntochka.hudud,
                    product=product,
                    ntochka=ntochka,
                    last_price = 0.0,
                    previous_price = 0.0,
                    miqdor = 0.0,
                    is_active = True,
                    is_udalen = False,
                    is_weekly = True
                )



            except Exception as e:
                errors_count += 1
                error_messages.append(f"Row {_ + 1}: Xatolik - {str(e)}")
                continue

        # Natijalarni qaytarish
        result = {
            'imported_count': imported_count,
            'existing_count': existing_count,
            'errors_count': errors_count,
            'error_messages': error_messages,
            'total_processed': imported_count + existing_count + errors_count
        }

        print(f"Import yakunlandi:")
        print(f"- Yangi yaratildi: {imported_count}")
        print(f"- Mavjud edi: {existing_count}")
        print(f"- Xatoliklar: {errors_count}")

        if error_messages:
            print("Xatolik xabarlari:")
            for msg in error_messages:  # Faqat birinchi 10 ta xatolikni ko'rsatish
                print(f"  - {msg}")
            # if len(error_messages) > 10:
            #     print(f"  ... va yana {len(error_messages) - 10} ta xatolik")

        return result

    def update_category(self, df):
        imported_count = 0
        existing_count = 0
        errors_count = 0

        for _, row in df.iterrows():
            code8 = row.get('kod{8}', None)
            code = code8
            rasfas = row.get('rasfas', 1)
            cat = ProductCategory.objects.get(code=code)
            cat.rasfas = rasfas
            cat.save()


    def handle(self, *args, **options):
        self.stdout.write("Excel fayl topilgan ma'lumotlarni bazaga yuklash boshlandi...")

        employee_data = self.read_sheet('users')
        self.import_employee(employee_data)

        obyekt_data = self.read_sheet('obyekt')
        self.import_obyekt(obyekt_data)
        #
        # rasta_data = self.read_sheet('rasta')
        # self.import_ntochka(rasta_data)
        #
        category_data = self.read_sheet('category')
        # self.update_category(category_data)
        self.import_category(category_data)
        #
        product_data = self.read_sheet('product')
        self.import_products(product_data)
        #
        # rasta_hafta_product_data = self.read_sheet('rasta_hafta')
        # self.relate_rasta_hafta_product(rasta_hafta_product_data)
        #
        # rasta_oy_product_data = self.read_sheet('rasta_oy')
        # self.relate_rasta_hafta_product(rasta_oy_product_data)

        self.stdout.write(self.style.SUCCESS("Import jarayoni muvaffaqiyatli yakunlandi!"))

