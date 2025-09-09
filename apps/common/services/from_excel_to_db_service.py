# apps/importer/services.py
from django.db import transaction
from apps.form.models import Birlik, ProductCategory, Product
from apps.common.models import KoboForm
from apps.home.models import Employee, District, Tochka
import pandas as pd


# Shu yerga sening helperlaringni qo'yamiz (s, s_or_none, b, i, f)
def s(v, default=""):
    import pandas as pd
    if v is None: return default
    try:
        if pd.isna(v): return default
    except Exception:
        pass
    return str(v).strip()

def s_or_none(v):
    x = s(v, "")
    return x if x else None

def b(v, default=False):
    if v is None: return default
    val = str(v).strip().lower()
    return val in {"1","true","t","yes","ha","y","on","active"}

def i(v, default=0):
    x = s_or_none(v)
    if x is None: return default
    try:
        return int(float(x))
    except Exception:
        return default

def f(v, default=0.0):
    x = s_or_none(v)
    if x is None: return default
    try:
        return float(x)
    except Exception:
        return default

class PlanshetExcelImporter:
    """
    Shu klass ichida xuddi management command’dagi metodlarni ishlatamiz.
    Farqi: fayl path emas, uploaded file (InMemoryUploadedFile/TemporaryUploadedFile) bilan ishlaymiz.
    """

    def __init__(self, file_obj):
        self.file_obj = file_obj
        self.results = {}

    def read_sheet(self, sheet_name):
        # Uploaded file bilan bevosita ishlash
        self.file_obj.seek(0)
        return pd.read_excel(
            self.file_obj,
            sheet_name=sheet_name,
            dtype=str,
            keep_default_na=False,
            engine="openpyxl",
        )

    @transaction.atomic
    def import_employee(self, df):
        # from apps.home.models import District  # mos joyingga qarab import qil
        # from apps.form.models import Employee

        imported = existing = errors = 0
        existing_logins = set(Employee.objects.values_list("login", flat=True))
        district_cache = {}

        for _, row in df.iterrows():
            full_name = s(row.get('fio'))
            soato = s_or_none(row.get('soato'))
            is_active = b(row.get('is_active', 'yes'), True)
            pinfl = s_or_none(row.get('pinfl'))
            phone1 = s_or_none(row.get('phone1'))
            phone2 = s_or_none(row.get('phone2'))
            password = s_or_none(row.get('password'))
            login = s_or_none(row.get('soato')) or pinfl

            if not login:
                errors += 1
                continue

            if login in existing_logins:
                existing += 1
                continue

            if not soato or len(soato) < 6:
                errors += 1
                continue

            region_code = soato[:4]
            district_code = soato[4:]
            key = (region_code, district_code)

            if key in district_cache:
                district = district_cache[key]
            else:
                try:
                    district = District.objects.get(code=district_code, region__code=region_code)
                    district_cache[key] = district
                except District.DoesNotExist:
                    errors += 1
                    continue
                except District.MultipleObjectsReturned:
                    errors += 1
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
                    permission1=True, permission2=True, permission3=True,
                    permission4=False, permission5=False,
                    gps_permission=True,
                    lang='uz'
                )
                existing_logins.add(login)
                imported += 1
            except Exception:
                errors += 1

        self.results['employees'] = dict(imported=imported, existing=existing, errors=errors)

    @transaction.atomic
    def import_obyekt(self, df):


        imported = existing = errors = 0
        existing_codes = set(Tochka.objects.values_list("code", flat=True))
        district_cache = {}
        employees_by_district = {}

        for _, row in df.iterrows():
            name = s(row.get('nomi'))
            lon = f(row.get('lon'))
            lat = f(row.get('lat'))
            is_active = b(row.get('is_active'), True)
            unique_code = s_or_none(row.get('unique_kod')) or s_or_none(row.get('kod'))
            inn = s_or_none(row.get('INN'))
            is_weekly = i(row.get('is_weekly'), 0)
            soato = s_or_none(row.get('soato'))
            pinfl = s_or_none(row.get('pinfl'))

            if not unique_code:
                errors += 1
                continue

            if unique_code in existing_codes:
                existing += 1
                continue

            if not soato or len(soato) < 6:
                errors += 1
                continue

            region_code = soato[:4]
            district_code = soato[4:]
            key = (region_code, district_code)

            if key in district_cache:
                district = district_cache[key]
            else:
                try:
                    district = District.objects.get(code=district_code, region__code=region_code)
                    district_cache[key] = district
                except District.DoesNotExist:
                    errors += 1
                    continue
                except District.MultipleObjectsReturned:
                    errors += 1
                    continue

            employee = None
            if pinfl:
                employee = Employee.objects.filter(pinfl=pinfl, district=district).order_by('id').first()
            if not employee:
                if key in employees_by_district:
                    employee = employees_by_district[key]
                else:
                    employee = Employee.objects.filter(district=district).order_by('id').first()
                    employees_by_district[key] = employee

            if not employee:
                errors += 1
                continue

            try:
                Tochka.objects.create(
                    name=name,
                    icon='nutrition',
                    district=district,
                    code=unique_code,
                    inn=inn,
                    pinfl=pinfl,
                    lat=lat,
                    lon=lon,
                    employee=employee,
                    is_active=is_active,
                    weekly_type=is_weekly
                )
                existing_codes.add(unique_code)
                imported += 1
            except Exception:
                errors += 1

        self.results['tochka'] = dict(imported=imported, existing=existing, errors=errors)

    @transaction.atomic
    def import_category(self, df):

        imported = existing = errors = 0
        existing_codes = set(ProductCategory.objects.values_list("code", flat=True))

        for _, row in df.iterrows():
            name = s(row.get('nomi'))
            code3 = s_or_none(row.get('kod{3}'))
            code8 = s_or_none(row.get('kod{8}'))
            code = code8 or code3
            birlik_nomi = s(row.get('birligi'))
            rasfas = i(row.get('rasfas'), 1)
            number = code3

            if not code:
                errors += 1
                continue

            if code in existing_codes:
                existing += 1
                continue

            try:
                birligi = Birlik.objects.get(name=birlik_nomi)
            except Birlik.DoesNotExist:
                errors += 1
                continue

            try:
                ProductCategory.objects.create(
                    name=name,
                    code=code,
                    union=birligi,
                    rasfas=rasfas,
                    number=number,
                )
                existing_codes.add(code)
                imported += 1
            except Exception:
                errors += 1

        self.results['category'] = dict(imported=imported, existing=existing, errors=errors)

    @transaction.atomic
    def import_products(self, df):

        imported = existing = errors = 0
        existing_codes = set(Product.objects.values_list("code", flat=True))
        cat_by_code = ProductCategory.objects.in_bulk(field_name='code')

        for _, row in df.iterrows():
            name = s(row.get('nomi'))
            category_code = s_or_none(row.get('kod{8}.cat'))
            weekly_val = i(row.get('is_weekly'), 1)
            narxi = f(row.get('Narxi'), 0.0)
            unique_code = s_or_none(row.get('kod_unique'))
            barcode = s(row.get('barcode'))
            is_import_val = s(row.get('is_import'))

            if not unique_code:
                errors += 1
                continue

            if unique_code in existing_codes:
                existing += 1
                continue

            if not category_code or category_code not in cat_by_code:
                errors += 1
                continue

            category = cat_by_code[category_code]
            try:
                Product.objects.create(
                    name=name,
                    code=unique_code,
                    barcode=barcode,
                    category=category,
                    price=narxi,
                    bottom=narxi * 0.8,
                    top=narxi * 1.2,
                    weekly=int(weekly_val),
                    unit=category.union,
                    hbhd=3,
                    is_import=b(is_import_val, False),
                    is_special=(int(weekly_val) == 3),
                    is_index=(int(weekly_val) == 3),
                )
                existing_codes.add(unique_code)
                imported += 1
            except Exception:
                errors += 1

        self.results['products'] = dict(imported=imported, existing=existing, errors=errors)

    def run(self, sheets=("users","obyekt","category","product")):
        """
        Admin formdan checkboxlar bilan qaysi listlarni ishlatishni tanlaymiz.
        """
        if "users" in sheets:
            self.import_employee(self.read_sheet("users"))
        if "obyekt" in sheets:
            self.import_obyekt(self.read_sheet("obyekt"))
        if "category" in sheets:
            self.import_category(self.read_sheet("category"))
        if "product" in sheets:
            self.import_products(self.read_sheet("product"))
        return self.results
