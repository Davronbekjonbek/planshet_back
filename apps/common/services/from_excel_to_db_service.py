# apps/importer/services.py
from django.db import transaction
from apps.form.models import Birlik, ProductCategory, Product
from apps.common.models import KoboForm
from apps.home.models import Employee, District, Tochka
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# Helper functions
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
    Optimized Excel importer with better transaction management and bulk operations
    """

    def __init__(self, file_obj):
        self.file_obj = file_obj
        self.results = {}

    def read_sheet(self, sheet_name):
        try:
            self.file_obj.seek(0)
            return pd.read_excel(
                self.file_obj,
                sheet_name=sheet_name,
                dtype=str,
                keep_default_na=False,
                engine="openpyxl",
            )
        except Exception as e:
            logger.error(f"Error reading sheet {sheet_name}: {e}")
            return pd.DataFrame()

    def preload_data(self):
        """Preload all necessary data to reduce database queries"""
        self.existing_employee_logins = set(Employee.objects.values_list("login", flat=True))
        self.existing_tochka_codes = set(Tochka.objects.values_list("code", flat=True))
        self.existing_category_codes = set(ProductCategory.objects.values_list("code", flat=True))
        self.existing_product_codes = set(Product.objects.values_list("code", flat=True))
        
        # Cache districts and regions
        self.district_cache = {}
        districts = District.objects.select_related('region').all()
        for district in districts:
            key = (district.region.code, district.code)
            self.district_cache[key] = district
        
        # Cache employees by district
        self.employees_by_district = {}
        employees = Employee.objects.select_related('district').all()
        for emp in employees:
            district_id = emp.district_id
            if district_id not in self.employees_by_district:
                self.employees_by_district[district_id] = emp
        
        # Cache birlik objects
        self.birlik_cache = {birlik.name: birlik for birlik in Birlik.objects.all()}
        
        # Cache categories
        self.category_cache = {cat.code: cat for cat in ProductCategory.objects.select_related('union').all()}

    def import_employee(self, df):
        if df.empty:
            self.results['employees'] = dict(imported=0, existing=0, errors=0)
            return

        imported = existing = errors = 0
        employees_to_create = []
        batch_size = 500

        for _, row in df.iterrows():
            try:
                full_name = s(row.get('fio'))
                soato = s_or_none(row.get('soato'))
                is_active = b(row.get('is_active', 'yes'), True)
                pinfl = s_or_none(row.get('pinfl'))
                phone1 = s_or_none(row.get('phone1'))
                phone2 = s_or_none(row.get('phone2'))
                password = s_or_none(row.get('password'))
                login = s_or_none(row.get('soato')) or pinfl

                if not login or not soato or len(soato) < 6:
                    errors += 1
                    continue

                if login in self.existing_employee_logins:
                    existing += 1
                    continue

                region_code = soato[:4]
                district_code = soato[4:]
                key = (region_code, district_code)

                if key not in self.district_cache:
                    errors += 1
                    continue

                district = self.district_cache[key]

                employees_to_create.append(Employee(
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
                ))
                
                self.existing_employee_logins.add(login)
                imported += 1

                # Bulk create when batch size is reached
                if len(employees_to_create) >= batch_size:
                    try:
                        Employee.objects.bulk_create(employees_to_create, ignore_conflicts=True)
                        employees_to_create = []
                    except Exception as e:
                        logger.error(f"Error in bulk create employees: {e}")
                        errors += len(employees_to_create)
                        employees_to_create = []

            except Exception as e:
                logger.error(f"Error processing employee row: {e}")
                errors += 1

        # Create remaining employees
        if employees_to_create:
            try:
                Employee.objects.bulk_create(employees_to_create, ignore_conflicts=True)
            except Exception as e:
                logger.error(f"Error in final bulk create employees: {e}")
                errors += len(employees_to_create)

        self.results['employees'] = dict(imported=imported, existing=existing, errors=errors)

    def import_obyekt(self, df):
        if df.empty:
            self.results['tochka'] = dict(imported=0, existing=0, errors=0)
            return

        imported = existing = errors = 0
        tochkas_to_create = []
        batch_size = 500

        for _, row in df.iterrows():
            try:
                name = s(row.get('nomi'))
                lon = f(row.get('lon'))
                lat = f(row.get('lat'))
                is_active = b(row.get('is_active'), True)
                unique_code = s_or_none(row.get('unique_kod')) or s_or_none(row.get('kod'))
                inn = s_or_none(row.get('INN'))
                is_weekly = i(row.get('is_weekly'), 0)
                soato = s_or_none(row.get('soato'))
                pinfl = s_or_none(row.get('pinfl'))

                if not unique_code or not soato or len(soato) < 6:
                    errors += 1
                    continue

                if unique_code in self.existing_tochka_codes:
                    existing += 1
                    continue

                region_code = soato[:4]
                district_code = soato[4:]
                key = (region_code, district_code)

                if key not in self.district_cache:
                    errors += 1
                    continue

                district = self.district_cache[key]

                # Find employee more efficiently
                employee = None
                if pinfl:
                    # Try to find employee by pinfl and district from cached data
                    for emp_district_id, emp in self.employees_by_district.items():
                        if emp.district_id == district.id and emp.pinfl == pinfl:
                            employee = emp
                            break
                
                if not employee and district.id in self.employees_by_district:
                    employee = self.employees_by_district[district.id]

                if not employee:
                    errors += 1
                    continue

                tochkas_to_create.append(Tochka(
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
                ))
                
                self.existing_tochka_codes.add(unique_code)
                imported += 1

                # Bulk create when batch size is reached
                if len(tochkas_to_create) >= batch_size:
                    try:
                        Tochka.objects.bulk_create(tochkas_to_create, ignore_conflicts=True)
                        tochkas_to_create = []
                    except Exception as e:
                        logger.error(f"Error in bulk create tochkas: {e}")
                        errors += len(tochkas_to_create)
                        tochkas_to_create = []

            except Exception as e:
                logger.error(f"Error processing obyekt row: {e}")
                errors += 1

        # Create remaining tochkas
        if tochkas_to_create:
            try:
                Tochka.objects.bulk_create(tochkas_to_create, ignore_conflicts=True)
            except Exception as e:
                logger.error(f"Error in final bulk create tochkas: {e}")
                errors += len(tochkas_to_create)

        self.results['tochka'] = dict(imported=imported, existing=existing, errors=errors)

    def import_category(self, df):
        if df.empty:
            self.results['category'] = dict(imported=0, existing=0, errors=0)
            return

        imported = existing = errors = 0
        categories_to_create = []
        batch_size = 500

        for _, row in df.iterrows():
            try:
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

                if code in self.existing_category_codes:
                    existing += 1
                    continue

                if birlik_nomi not in self.birlik_cache:
                    errors += 1
                    continue

                birligi = self.birlik_cache[birlik_nomi]

                categories_to_create.append(ProductCategory(
                    name=name,
                    code=code,
                    union=birligi,
                    rasfas=rasfas,
                    number=number,
                ))
                
                self.existing_category_codes.add(code)
                # Update cache
                self.category_cache[code] = categories_to_create[-1]
                imported += 1

                # Bulk create when batch size is reached
                if len(categories_to_create) >= batch_size:
                    try:
                        ProductCategory.objects.bulk_create(categories_to_create, ignore_conflicts=True)
                        categories_to_create = []
                    except Exception as e:
                        logger.error(f"Error in bulk create categories: {e}")
                        errors += len(categories_to_create)
                        categories_to_create = []

            except Exception as e:
                logger.error(f"Error processing category row: {e}")
                errors += 1

        # Create remaining categories
        if categories_to_create:
            try:
                ProductCategory.objects.bulk_create(categories_to_create, ignore_conflicts=True)
            except Exception as e:
                logger.error(f"Error in final bulk create categories: {e}")
                errors += len(categories_to_create)

        self.results['category'] = dict(imported=imported, existing=existing, errors=errors)

    def import_products(self, df):
        if df.empty:
            self.results['products'] = dict(imported=0, existing=0, errors=0)
            return

        imported = existing = errors = 0
        products_to_create = []
        batch_size = 500

        for _, row in df.iterrows():
            try:
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

                if unique_code in self.existing_product_codes:
                    existing += 1
                    continue

                if not category_code or category_code not in self.category_cache:
                    errors += 1
                    continue

                category = self.category_cache[category_code]

                products_to_create.append(Product(
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
                ))
                
                self.existing_product_codes.add(unique_code)
                imported += 1

                # Bulk create when batch size is reached
                if len(products_to_create) >= batch_size:
                    try:
                        Product.objects.bulk_create(products_to_create, ignore_conflicts=True)
                        products_to_create = []
                    except Exception as e:
                        logger.error(f"Error in bulk create products: {e}")
                        errors += len(products_to_create)
                        products_to_create = []

            except Exception as e:
                logger.error(f"Error processing product row: {e}")
                errors += 1

        # Create remaining products
        if products_to_create:
            try:
                Product.objects.bulk_create(products_to_create, ignore_conflicts=True)
            except Exception as e:
                logger.error(f"Error in final bulk create products: {e}")
                errors += len(products_to_create)

        self.results['products'] = dict(imported=imported, existing=existing, errors=errors)

    @transaction.atomic
    def run(self, sheets=("users","obyekt","category","product")):
        """
        Import data from Excel sheets with optimized database operations
        """
        try:
            # Preload all data to minimize database queries
            self.preload_data()
            
            # Import in order to maintain dependencies
            if "users" in sheets:
                self.import_employee(self.read_sheet("users"))
            if "obyekt" in sheets:
                self.import_obyekt(self.read_sheet("obyekt"))
            if "category" in sheets:
                self.import_category(self.read_sheet("category"))
            if "product" in sheets:
                self.import_products(self.read_sheet("product"))
                
            return self.results
            
        except Exception as e:
            logger.error(f"Error in import process: {e}")
            # Re-raise to trigger transaction rollback
            raise
