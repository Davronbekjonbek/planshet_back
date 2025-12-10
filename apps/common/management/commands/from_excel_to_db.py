import time
from apps.common.models import *
from apps.form.models import *
from apps.home.models import *

from django.core.management.base import BaseCommand, CommandError

import pandas as pd
import os

file_path = "datas/plantochtovar_oxirgi.xlsx"
# file_path = "datas/plantochtovar_oxirgi_has_product_mhik.xlsx"
# file_path = "datas/planshet_data.xlsx"

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
            full_name = str(row.get('fish', '')).strip()
            soato = str(row.get('tuman_soato', None))
            is_active = row.get('is_active', 'yes').strip().lower() == 'yes'
            pinfl = str(row.get('pinfl', None))
            phone1 = str(row.get('phone1', None))
            phone2 = str(row.get('phone2', None))
            password = str(row.get('parol', None))
            login = str(row.get('tuman_soato', None)) or pinfl  # Agar login bo'sh bo'lsa, pinfl ishlatiladi

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
            name = str(row.get('nomi', '')).strip()
            lon = row.get('lon', 0.0) or 0.0
            lat = row.get('lat', 0.0) or 0.0
            is_active = row.get('faol', True)
            code = row.get('kod', None)
            unique_code = row.get('obyekt_code', None)
            inn = row.get('inn', 0)
            is_weekly = row.get('haftalik', False)

            # ForeignKey lar uchun (masalan: soato orqali District, pinfl orqali Employee qidirish mumkin)
            soato = str(row.get('tuman', None))
            pinfl = row.get('pinfl', None)
            adress = row.get('manzil', '').strip()
            raw_value = row.get('mahsulot_turi', '')
            mahsulot_turi = [x.strip() for x in raw_value.strip("()").split(",")]
            print(mahsulot_turi, name)
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
                    weekly_type=int(is_weekly),
                    product_type=mahsulot_turi,
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
            obyekt_unique = str(int(row.get('obyekt', None)))
            code = str(row.get('rasta_kodi', None))
            is_weekly = bool(row.get('is_weekly', False))
            weekly_type = int(row.get('haftalik_turi', 1))
            print(obyekt_unique, type(obyekt_unique))
            # Kod bo'yicha obyektni (Tochka) topish
            raw_value = row.get('mahsulot_turi', '')
            mahsulot_turi = [x.strip() for x in raw_value.strip("()").split(",")]

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
                    code=code,
                    weekly_type=weekly_type,
                    product_type=mahsulot_turi,
                )
                imported_count += 1
            except Exception as e:
                time.sleep(5)
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
            name = str(row.get('nomi') or '').strip()
            code3 = row.get('kod3', None)
            code8 = row.get('kod8', None)
            code = code8
            # birlik_nomi = (row.get('birligi') or '').strip()
            birlik_code = int(row.get('birlik_kodi', 1) or 1)
            
            rasfas = row.get('rasfas', 1)
            number = code3


            try:
                birligi = Birlik.objects.get(code=birlik_code)
            except Birlik.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Birlik topilmadi: {birlik_code} {row}"))
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
                    number=int(number),
                )
                print(name, code, birligi, rasfas, number)
                imported_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Xato: {name} - {str(e)}"))
                errors_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Yangi kategoriyalar: {imported_count}, mavjudlari: {existing_count}, xatoliklar: {errors_count}"
        ))


    def update_ntochka_product_type(self, df):
        updated_count = 0
        errors_count = 0

        for _, row in df.iterrows():
            rasta_kodi = str(int(row.get('rasta_kodi', ''))).strip()
            raw_value = row.get('mahsulot_turi', '')
            mahsulot_turi = [x.strip() for x in raw_value.strip("()").split(",")]
            try:
                ntochka = NTochka.objects.get(code=rasta_kodi)
                ntochka.product_type = mahsulot_turi
                ntochka.save()
                updated_count += 1
                print(rasta_kodi, mahsulot_turi, ntochka.product_type)
            except NTochka.DoesNotExist:
                errors_count += 1
                self.stdout.write(
                    self.style.WARNING(f"NTochka topilmadi: {rasta_kodi}")
                )
                continue

        self.stdout.write(self.style.SUCCESS(
            f"Yangilangan NTochka mahsulot turlari: {updated_count}, xatoliklar: {errors_count}"
        ))

    def import_products(self, df):

        imported_count = 0
        existing_count = 0
        errors_count = 0

        for _, row in df.iterrows():
            name = (row.get('nomi') or '').strip()
            code = str(row.get('kategoriya_kodi') or '').strip()
            category_code = code  # product category code ham bo‘lishi mumkin, kerak bo‘lsa moslashtiring
            # hbhd = int(row.get('HBHD', 1) or 1)
            is_import = bool(row.get('is_import', False))
            is_weekly = int(row.get('haftalik', 1) or 1)
            # narxi = float(row.get('narxi', 0) or 0)
            narxi = float(row.get('narxi', 0) or 0)
            is_special = bool(row.get('is_special', False))
            is_index = bool(row.get('is_index', False))
            unique_code = str(row.get('mahsulot_mhik_kodi') or '').strip()
            barcode_val = row.get('barcode')
            _bottom = row.get('bottom', 20) * narxi / 100 
            _top = row.get('top', 300) * narxi / 100
            try:
                if barcode_val is None or str(barcode_val).strip() == '' or pd.isna(barcode_val):
                    barcode = ''
                else:
                    barcode = str(int(float(barcode_val))).strip()
            except Exception as e:
                barcode = ''
            print(name)
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
                    barcode=barcode,
                    category=category,
                    price=narxi,
                    top=_top,
                    bottom=_bottom,
                    weekly_type=int(is_weekly),
                    weekly = True,
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

    def relate_rasta_product(self, rasta_product):
        imported_count = 0
        existing_count = 0
        errors_count = 0
        error_messages = []

        for _, row in rasta_product.iterrows():
            try:
                rasta_kodi = str(int(row.get('rasta_kodi', ''))).strip()
                mahsulot_kodi = str(int(row.get('mahsulot_kodi', ''))).strip()
                print(mahsulot_kodi)
                if not rasta_kodi or not mahsulot_kodi:
                    errors_count += 1
                    error_messages.append(f"Row {_ + 1}: rasta_kodi yoki mahsulot_kodi bo'sh")
                    continue

                try:
                    ntochka = NTochka.objects.get(code=rasta_kodi)
                except NTochka.DoesNotExist:
                    errors_count += 1
                    error_messages.append(f"Row {_ + 1}: NTochka topilmadi rasta_kodi={rasta_kodi}")
                    continue

                try:
                    product = Product.objects.get(code=mahsulot_kodi)
                except Product.DoesNotExist:
                    errors_count += 1
                    error_messages.append(f"Row {_ + 1}: Product topilmadi mahsulot_kodi={mahsulot_kodi}")
                    continue

                haftalik = row.get('haftalik', True)
                weekly = True if haftalik in [1, '1', True, 'True', 'true', 'Haftalik'] else False
                tochka_product = TochkaProduct.objects.create(
                    hudud = ntochka.hudud,
                    product=product,
                    ntochka=ntochka,
                    last_price = 0.0,
                    previous_price = 0.0,
                    miqdor = 0.0,
                    is_active = True,
                    is_udalen = False,
                    is_weekly = weekly
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
            union = row.get('birligi', None)
            number  = row.get('kod{3}', 1)

            cat = ProductCategory.objects.get(code=code)
            cat.rasfas = rasfas
            cat.union = union
            cat.number = number
            cat.save()

    def update_products(self, df):
        updated_count = 0
        errors_count = 0

        for _, row in df.iterrows():
            product_kodi = str(row.get('mahsulot_kodi') or '').strip()
            product = Product.objects.filter(code=product_kodi).first()
            if not product:
                errors_count += 1
                self.stdout.write(
                    self.style.WARNING(f"Mahsulot topilmadi: {product_kodi}")
                )
                continue

            kategory = str(row.get('kategoriya_kodi') or '').strip()
            category = ProductCategory.objects.filter(code=kategory).first()
            if not category:
                errors_count += 1
                self.stdout.write(
                    self.style.WARNING(f"Kategoriya topilmadi: {kategory} for product {product_kodi}")
                )
                continue
            product.category = category
            product.save()
            updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Yangilangan mahsulotlar: {updated_count}, xatoliklar: {errors_count}"
        ))

    def set_mhik_to_exists_products(self, df):
        updated_count = 0
        errors_count = 0

        for _, row in df.iterrows():
            product_kodi = str(row.get('mahsulot_kodi') or '').strip()
            product = Product.objects.filter(code=product_kodi).first()
            if not product:
                errors_count += 1
                self.stdout.write(
                    self.style.WARNING(f"Mahsulot topilmadi: {product_kodi}")
                )
                continue

            mahsulot_mhik_kodi = str(row.get('mahsulot_mhik_kodi') or '').strip()
            product.code = mahsulot_mhik_kodi
            product.save()
            updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Yangilangan mahsulotlar: {updated_count}, xatoliklar: {errors_count}"
        ))
    
    def update_rasta_product(self, df):
        """Rasta mahsulotlarini birliklarini yangliash"""
        updated_count = 0
        errors_count = 0

        rasta_product_count = {

        } 

        for _, row in df.iterrows():
            mahsulot_kodi = int(row.get('mahsulot_kodi') or '')
            rasta_kodi = int(row.get('rasta_kodi') or '')
            obyekt_kodi = int(row.get('obyekt_kodi') or '')
            miqdor = float(row.get('birlik') or 0.0)
            rasta_products = TochkaProduct.objects.filter(
                ntochka__code=rasta_kodi,
                product__code=mahsulot_kodi,
            )
            print(rasta_products, mahsulot_kodi, rasta_kodi, rasta_products.count(), "print")
            count_ = rasta_products.count()
            rasta_product_count[count_] = rasta_product_count.get(count_, 0) + 1
            rasta_products.update(miqdor=miqdor)
            updated_count += rasta_products.count()
        print(rasta_product_count)

    def add_price_for_last_period(self, df):
        updated_count = 0
        errors_count = 0

        for _, row in df.iterrows():
            mahsulot_kodi = int(row.get('mahsulot_kodi') or '')
            rasta_kodi = int(row.get('rasta_kodi') or '')
            obyekt_kodi = int(row.get('obyekt_kodi') or '')
            narxi = float(row.get('price') or 0.0)
            rasta_products = TochkaProduct.objects.filter(
                ntochka__code=rasta_kodi,
                product__code=mahsulot_kodi,
            )
            for rp in rasta_products:
                rp.last_price = narxi
                rp.save()
            print(rasta_products, narxi, mahsulot_kodi, rasta_kodi, rasta_products.count(), "print")
            updated_count += rasta_products.count()

        self.stdout.write(self.style.SUCCESS(
            f"Yangilangan rasta mahsulotlar: {updated_count}, xatoliklar: {errors_count}"
        ))

    def handle(self, *args, **options):
        self.stdout.write("Excel fayl topilgan ma'lumotlarni bazaga yuklash boshlandi...")

        # employee_data = self.read_sheet('xodim')
        # self.import_employee(employee_data)

        # obyekt_data = self.read_sheet('obyekt')
        # self.import_obyekt(obyekt_data)
        # #
        # rasta_data = self.read_sheet('rasta')
        # self.update_ntochka_product_type(rasta_data)
        # self.import_ntochka(rasta_data)
        # #
        # category_data = self.read_sheet('category')
        # self.update_category(category_data)
        # self.import_category(category_data)
        # #
        # product_data = self.read_sheet('mahsulot')
        # # self.update_products(product_data)
        # self.import_products(product_data)
        # #
        # rasta_hafta_product_data = self.read_sheet('rasta_mahsulotlari')
        # self.relate_rasta_product(rasta_hafta_product_data)
        #
        # rasta_oy_product_data = self.read_sheet('rasta_oy')
        # self.relate_rasta_hafta_product(rasta_oy_product_data)

        # rasta_product_data = self.read_sheet('rasta_mahsulotlari')
        # self.update_rasta_product(rasta_product_data)

        # exists_products_data = self.read_sheet('exists_mahsulot_mhik')
        # self.set_mhik_to_exists_products(exists_products_data)

        rasta_hafta_product_data = self.read_sheet('rasta_mahsulotlari')
        self.add_price_for_last_period(rasta_hafta_product_data)


        self.stdout.write(self.style.SUCCESS("Import jarayoni muvaffaqiyatli yakunlandi!"))

