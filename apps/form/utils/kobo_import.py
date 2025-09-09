import requests
import json
import logging
import os

from typing import Dict, List, Optional
from datetime import datetime
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.home.models import Employee, Tochka, PeriodDate
from apps.form.models import TochkaProductHistory, Product

logger = logging.getLogger("kobo_import")


class KoBoDataImporter:
    """KoBoToolbox dan ma'lumotlarni import qilish uchun utility class"""

    def __init__(self):
        self.api_token = getattr(settings, 'KOBO_API_TOKEN', '28f417fc72d201c2cdfb3b6d65c4830c176e3675')
        self.form_id = getattr(settings, 'KOBO_FORM_ID', 'abuTTZJpsJ9ED9FW45ccy3')
        self.base_url = "https://kf.kobotoolbox.org/api/v2/assets"
        self.headers = {
            "Authorization": f"Token {self.api_token}",
            "Content-Type": "application/json"
        }

    def fetch_kobo_data(self) -> Optional[Dict]:
        """KoBoToolbox dan ma'lumotlarni olish"""
        try:
            url = f"{self.base_url}/{self.form_id}/data.json"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            if data:
                file_path = os.path.join(settings.BASE_DIR, "datas", "form_datas.json")
                # Papka mavjud emasligini tekshirish
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
            logger.info(f"KoBoToolbox dan {data.get('count', 0)} ta yozuv olindi")
            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"KoBoToolbox dan ma'lumot olishda xatolik: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse qilishda xatolik: {e}")
            return None

    def parse_submission_date(self, date_str: str) -> datetime:
        """Submission date ni parse qilish"""
        try:
            # 2025-07-07T11:46:36 formatini parse qilish
            if 'T' in date_str and not date_str.endswith('Z') and '+' not in date_str:
                date_str = date_str + '+00:00'
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            logger.warning(f"Date parse qilib bo'lmadi: {date_str}")
            return timezone.now()

    def get_or_create_employee(self, login: str, user_id: str) -> Optional[Employee]:
        """Employee ni topish yoki xatolik qaytarish"""
        try:
            # Login bo'yicha topishga harakat qilish
            employee = Employee.objects.get(login=login)
            return employee
        except Employee.DoesNotExist:
            logger.warning(f"Employee topilmadi: login={login}, user_id={user_id}")
            return None

    def get_or_create_period(self, period_id: str) -> Optional[PeriodDate]:
        """PeriodDate ni topish"""
        try:
            period = PeriodDate.objects.get(id=period_id)
            return period
        except PeriodDate.DoesNotExist:
            logger.warning(f"Period topilmadi: {period_id}")
            return None

    def get_tochka(self, tochka_id: str) -> Optional[Tochka]:
        """Tochka ni topish"""
        try:
            tochka = Tochka.objects.get(id=tochka_id, is_active=True)
            return tochka
        except Tochka.DoesNotExist:
            logger.warning(f"Tochka topilmadi: {tochka_id}")
            return None

    def get_product(self, product_id: str) -> Optional[Product]:
        """Product ni topish"""
        try:
            product = Product.objects.get(id=product_id)
            return product
        except Product.DoesNotExist:
            logger.warning(f"Product topilmadi: {product_id}")
            return None

    def parse_products_data(self, products_data: List[Dict], submission: Dict) -> List[Dict]:
        """Mahsulot ma'lumotlarini parse qilish"""
        parsed_products = []

        # Login ma'lumotlarini olish
        login = submission.get('login_page/login', '')
        user_id = submission.get('login_page/user_id', '')
        period_id = submission.get('login_page/period_ok', '')
        tochka_id = submission.get('tochka_page/selected_tochka', '')

        # Submission date
        submission_date = self.parse_submission_date(
            submission.get('_submission_time', '')
        )

        for product_data in products_data:
            # Yangi format (tochka_products) - sizning JSON formatiga mos
            product_info = {
                'product_id': product_data.get('tochka_products/product_id'),
                'product_name': product_data.get('tochka_products/products_for_tochka/product_name'),
                'miqdor': product_data.get('tochka_products/products_for_tochka/miqdor'),
                'narx': product_data.get('tochka_products/products_for_tochka/narx'),
                'birlik_narx': product_data.get('tochka_products/products_for_tochka/birlik_narx'),
                'jami_narx': product_data.get('tochka_products/products_for_tochka/jami_narx'),
                'product_price': product_data.get('tochka_products/products_for_tochka/product_price'),
                'product_rasfasovka': product_data.get('tochka_products/products_for_tochka/product_rasfasovka'),
                'product_birlik': product_data.get('tochka_products/products_for_tochka/product_birlik'),
                'login': login,
                'user_id': user_id,
                'period_id': period_id,
                'tochka_id': tochka_id,
                'submission_date': submission_date,
                'kobo_submission_id': submission.get('_id')
            }

            # Bo'sh product_id larni o'tkazib yuborish
            if not product_info.get('product_id'):
                logger.warning(f"Product ID topilmadi: {product_data}")
                continue

            parsed_products.append(product_info)

        return parsed_products

    @transaction.atomic
    def save_product_history(self, product_info: Dict) -> bool:
        """TochkaProductHistory ga ma'lumot saqlash"""
        try:
            # Employee ni topish
            employee = self.get_or_create_employee(
                product_info['login'],
                product_info['user_id']
            )
            if not employee:
                return False

            # Period ni topish
            period = self.get_or_create_period(product_info['period_id'])
            if not period:
                return False

            # Tochka ni topish
            tochka = self.get_tochka(product_info['tochka_id'])
            if not tochka:
                return False

            # Product ni topish
            product = self.get_product(product_info['product_id'])
            if not product:
                return False

            # Narx va miqdor ma'lumotlarini olish
            price = float(product_info.get('narx', 0) or 0)
            unit_miqdor = float(product_info.get('miqdor', 0) or 0)
            unit_price = float(product_info.get('birlik_narx', 0) or 0)
            jami_narx = float(product_info.get('jami_narx', 0) or 0)

            # # Duplicate check - bir xil submission ID va product ID
            # existing = TochkaProductHistory.objects.filter(
            #     product=product,
            #     hudud=tochka,
            #     employee=employee,
            #     period=period,
            #     created_at__date=product_info['submission_date'].date()
            # ).first()
            #
            # if existing:
            #     logger.info(f"Duplicate record topildi: {existing.id}")
            #     return False

            # Yangi yozuv yaratish
            history = TochkaProductHistory.objects.create(
                product=product,
                hudud=tochka,
                price=price,
                unit_miqdor=unit_miqdor,
                unit_price=unit_price,
                employee=employee,
                period=period,
                is_checked=False,
                is_active=True
            )

            # Created_at ni submission date ga o'zgartirish
            history.created_at = product_info['submission_date']
            history.save(update_fields=['created_at'])

            logger.info(
                f"Yangi yozuv saqlandi: {history.id} - Product: {product.id}, Miqdor: {unit_miqdor}, Narx: {price}")
            return True

        except Exception as e:
            logger.error(f"Ma'lumot saqlashda xatolik: {e}")
            return False

    def process_submissions(self, data: Dict) -> Dict:
        """Barcha submissionlarni qayta ishlash"""
        results = {
            'total_submissions': 0,
            'processed_products': 0,
            'saved_products': 0,
            'errors': 0
        }

        submissions = data.get('results', [])
        results['total_submissions'] = len(submissions)

        for submission in submissions:
            try:
                # Products ma'lumotlarini olish
                products_data = submission.get('tochka_products', [])

                if not products_data:
                    logger.warning(f"Submission {submission.get('_id')} da mahsulot ma'lumotlari topilmadi")
                    continue

                # Mahsulotlarni parse qilish
                parsed_products = self.parse_products_data(products_data, submission)
                results['processed_products'] += len(parsed_products)

                # Har bir mahsulotni saqlash
                for product_info in parsed_products:
                    if self.save_product_history(product_info):
                        results['saved_products'] += 1
                    else:
                        results['errors'] += 1

            except Exception as e:
                logger.error(f"Submission qayta ishlashda xatolik: {e}")
                results['errors'] += 1

        return results

    def import_data(self) -> Dict:
        """Asosiy import funksiyasi"""
        logger.info("KoBoToolbox ma'lumotlarini import qilish boshlandi")

        # Ma'lumotlarni olish
        data = self.fetch_kobo_data()
        if not data:
            return {'success': False, 'error': 'Ma\'lumot olinmadi'}

        # Ma'lumotlarni qayta ishlash
        results = self.process_submissions(data)

        logger.info(f"Import yakunlandi: {results}")
        return {
            'success': True,
            'results': results
        }


