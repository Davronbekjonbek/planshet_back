import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from django.test import TestCase
from django.db import IntegrityError
from django.db.utils import IntegrityError as UtilsIntegrityError
from io import BytesIO

from .from_excel_to_db_service import (
    PlanshetExcelImporter, 
    s, s_or_none, b, i, f
)


class TestHelperFunctions(TestCase):
    """Test helper functions s, s_or_none, b, i, f"""
    
    def test_s_function(self):
        # Test normal string
        self.assertEqual(s("test"), "test")
        # Test with whitespace
        self.assertEqual(s("  test  "), "test")
        # Test None
        self.assertEqual(s(None), "")
        self.assertEqual(s(None, "default"), "default")
        # Test pandas NaN
        self.assertEqual(s(pd.NA), "")
        # Test number
        self.assertEqual(s(123), "123")
    
    def test_s_or_none_function(self):
        self.assertEqual(s_or_none("test"), "test")
        self.assertEqual(s_or_none(""), None)
        self.assertEqual(s_or_none(None), None)
        self.assertEqual(s_or_none("  "), None)
    
    def test_b_function(self):
        # Test true values
        self.assertTrue(b("1"))
        self.assertTrue(b("true"))
        self.assertTrue(b("yes"))
        self.assertTrue(b("ha"))
        self.assertTrue(b("active"))
        # Test false values
        self.assertFalse(b("0"))
        self.assertFalse(b("false"))
        self.assertFalse(b("no"))
        self.assertFalse(b(None))
        self.assertFalse(b(""))
    
    def test_i_function(self):
        self.assertEqual(i("123"), 123)
        self.assertEqual(i("123.45"), 123)
        self.assertEqual(i("invalid"), 0)
        self.assertEqual(i(None), 0)
        self.assertEqual(i("", 5), 5)
    
    def test_f_function(self):
        self.assertEqual(f("123.45"), 123.45)
        self.assertEqual(f("123"), 123.0)
        self.assertEqual(f("invalid"), 0.0)
        self.assertEqual(f(None), 0.0)
        self.assertEqual(f("", 5.5), 5.5)


class TestPlanshetExcelImporter(TestCase):
    """Test PlanshetExcelImporter class"""
    
    def setUp(self):
        self.mock_file = Mock()
        self.importer = PlanshetExcelImporter(self.mock_file)
    
    @patch('pandas.read_excel')
    def test_read_sheet(self, mock_read_excel):
        mock_df = pd.DataFrame({'test': [1, 2, 3]})
        mock_read_excel.return_value = mock_df
        
        result = self.importer.read_sheet("test_sheet")
        
        self.mock_file.seek.assert_called_once_with(0)
        mock_read_excel.assert_called_once_with(
            self.mock_file,
            sheet_name="test_sheet",
            dtype=str,
            keep_default_na=False,
            engine="openpyxl",
        )
        self.assertEqual(result.equals(mock_df), True)
    
    @patch('apps.home.models.Employee')
    @patch('apps.home.models.District')
    def test_import_employee_success(self, mock_district, mock_employee):
        # Setup mocks
        mock_employee.objects.values_list.return_value = []
        mock_district_instance = Mock()
        mock_district.objects.get.return_value = mock_district_instance
        mock_employee.objects.create.return_value = Mock()
        
        # Create test data
        df = pd.DataFrame({
            'fio': ['Test User'],
            'soato': ['123456'],
            'is_active': ['yes'],
            'pinfl': ['12345678901234'],
            'phone1': ['998901234567'],
            'phone2': ['998901234568'],
            'password': ['password123']
        })
        
        self.importer.import_employee(df)
        
        # Verify results
        self.assertEqual(self.importer.results['employees']['imported'], 1)
        self.assertEqual(self.importer.results['employees']['existing'], 0)
        self.assertEqual(self.importer.results['employees']['errors'], 0)
        
        mock_employee.objects.create.assert_called_once()
    
    @patch('apps.home.models.Employee')
    @patch('apps.home.models.District')
    def test_import_employee_existing(self, mock_district, mock_employee):
        # Setup mocks - existing login
        mock_employee.objects.values_list.return_value = ['123456']
        
        df = pd.DataFrame({
            'fio': ['Test User'],
            'soato': ['123456'],
            'is_active': ['yes'],
            'pinfl': ['12345678901234'],
            'phone1': ['998901234567'],
            'phone2': ['998901234568'],
            'password': ['password123']
        })
        
        self.importer.import_employee(df)
        
        self.assertEqual(self.importer.results['employees']['imported'], 0)
        self.assertEqual(self.importer.results['employees']['existing'], 1)
        self.assertEqual(self.importer.results['employees']['errors'], 0)
    
    @patch('apps.home.models.Tochka')
    @patch('apps.home.models.Employee')
    @patch('apps.home.models.District')
    def test_import_obyekt_success(self, mock_district, mock_employee, mock_tochka):
        # Setup mocks
        mock_tochka.objects.values_list.return_value = []
        mock_district_instance = Mock()
        mock_district.objects.get.return_value = mock_district_instance
        mock_employee_instance = Mock()
        mock_employee.objects.filter.return_value.order_by.return_value.first.return_value = mock_employee_instance
        mock_tochka.objects.create.return_value = Mock()
        
        df = pd.DataFrame({
            'nomi': ['Test Tochka'],
            'lon': ['69.123456'],
            'lat': ['41.123456'],
            'is_active': ['yes'],
            'unique_kod': ['TOCHKA001'],
            'INN': ['123456789'],
            'is_weekly': ['1'],
            'soato': ['123456'],
            'pinfl': ['12345678901234']
        })
        
        self.importer.import_obyekt(df)
        
        self.assertEqual(self.importer.results['tochka']['imported'], 1)
        self.assertEqual(self.importer.results['tochka']['existing'], 0)
        self.assertEqual(self.importer.results['tochka']['errors'], 0)
        
        mock_tochka.objects.create.assert_called_once()
    
    @patch('apps.home.models.Tochka')
    @patch('apps.home.models.Employee')
    @patch('apps.home.models.District')
    def test_import_obyekt_missing_inn_error(self, mock_district, mock_employee, mock_tochka):
        # Setup mocks
        mock_tochka.objects.values_list.return_value = []
        mock_district_instance = Mock()
        mock_district.objects.get.return_value = mock_district_instance
        mock_employee_instance = Mock()
        mock_employee.objects.filter.return_value.order_by.return_value.first.return_value = mock_employee_instance
        # Simulate IntegrityError for missing inn
        mock_tochka.objects.create.side_effect = IntegrityError("NOT NULL constraint failed: obyekt.inn")
        
        df = pd.DataFrame({
            'nomi': ['Test Tochka'],
            'lon': ['69.123456'],
            'lat': ['41.123456'],
            'is_active': ['yes'],
            'unique_kod': ['TOCHKA001'],
            'INN': [None],  # Missing INN
            'is_weekly': ['1'],
            'soato': ['123456'],
            'pinfl': ['12345678901234']
        })
        
        self.importer.import_obyekt(df)
        
        self.assertEqual(self.importer.results['tochka']['imported'], 0)
        self.assertEqual(self.importer.results['tochka']['existing'], 0)
        self.assertEqual(self.importer.results['tochka']['errors'], 1)
    
    @patch('apps.form.models.ProductCategory')
    @patch('apps.form.models.Birlik')
    def test_import_category_success(self, mock_birlik, mock_category):
        # Setup mocks
        mock_category.objects.values_list.return_value = []
        mock_birlik_instance = Mock()
        mock_birlik.objects.get.return_value = mock_birlik_instance
        mock_category.objects.create.return_value = Mock()
        
        df = pd.DataFrame({
            'nomi': ['Test Category'],
            'kod{3}': ['001'],
            'kod{8}': ['00100001'],
            'birligi': ['kg'],
            'rasfas': ['1']
        })
        
        self.importer.import_category(df)
        
        self.assertEqual(self.importer.results['category']['imported'], 1)
        self.assertEqual(self.importer.results['category']['existing'], 0)
        self.assertEqual(self.importer.results['category']['errors'], 0)
        
        mock_category.objects.create.assert_called_once()
    
    @patch('apps.form.models.Product')
    @patch('apps.form.models.ProductCategory')
    def test_import_products_success(self, mock_category, mock_product):
        # Setup mocks
        mock_product.objects.values_list.return_value = []
        mock_category_instance = Mock()
        mock_category_instance.union = Mock()
        mock_category.objects.in_bulk.return_value = {'00100001': mock_category_instance}
        mock_product.objects.create.return_value = Mock()
        
        df = pd.DataFrame({
            'nomi': ['Test Product'],
            'kod{8}.cat': ['00100001'],
            'is_weekly': ['1'],
            'Narxi': ['1000.0'],
            'kod_unique': ['PROD001'],
            'barcode': ['1234567890123'],
            'is_import': ['false']
        })
        
        self.importer.import_products(df)
        
        self.assertEqual(self.importer.results['products']['imported'], 1)
        self.assertEqual(self.importer.results['products']['existing'], 0)
        self.assertEqual(self.importer.results['products']['errors'], 0)
        
        mock_product.objects.create.assert_called_once()
    
    @patch.object(PlanshetExcelImporter, 'import_products')
    @patch.object(PlanshetExcelImporter, 'import_category')
    @patch.object(PlanshetExcelImporter, 'import_obyekt')
    @patch.object(PlanshetExcelImporter, 'import_employee')
    @patch.object(PlanshetExcelImporter, 'read_sheet')
    def test_run_method(self, mock_read_sheet, mock_import_employee, 
                       mock_import_obyekt, mock_import_category, mock_import_products):
        mock_df = pd.DataFrame({'test': [1]})
        mock_read_sheet.return_value = mock_df
        
        result = self.importer.run(sheets=("users", "obyekt", "category", "product"))
        
        # Verify all import methods were called
        mock_import_employee.assert_called_once_with(mock_df)
        mock_import_obyekt.assert_called_once_with(mock_df)
        mock_import_category.assert_called_once_with(mock_df)
        mock_import_products.assert_called_once_with(mock_df)
        
        # Verify read_sheet was called for each sheet
        self.assertEqual(mock_read_sheet.call_count, 4)
        
        self.assertEqual(result, self.importer.results)
    
    @patch.object(PlanshetExcelImporter, 'import_employee')
    @patch.object(PlanshetExcelImporter, 'read_sheet')
    def test_run_method_selective_sheets(self, mock_read_sheet, mock_import_employee):
        mock_df = pd.DataFrame({'test': [1]})
        mock_read_sheet.return_value = mock_df
        
        self.importer.run(sheets=("users",))
        
        # Only employee import should be called
        mock_import_employee.assert_called_once_with(mock_df)
        mock_read_sheet.assert_called_once_with("users")
    
    def test_run_method_empty_sheets(self):
        result = self.importer.run(sheets=())
        self.assertEqual(result, {})