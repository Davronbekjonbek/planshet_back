import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings

from apps.form.models import Product, ProductCategory, Birlik


class Command(BaseCommand):
    help = "datas/products.json faylidan mahsulotlarni bazaga yuklaydi"

    def handle(self, *args, **options):
        base_dir = settings.BASE_DIR
        file_path = os.path.join(base_dir, 'datas', 'products.json')

        with open(file_path, encoding='utf-8') as f:
            data = json.load(f)

        for _data in data:
            try:
                # Kategoriya bo'yicha topish
                try:
                    category = ProductCategory.objects.get(code=_data['category_code'])
                except ProductCategory.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f"Kategoriya topilmadi: {_data['category_code']} - {_data['name']}")
                    )
                    continue

                # O'lchov birligini kategoriya orqali olish
                birlik = category.union

                top = float(_data['price']) * 1.2
                bottom = float(_data['price']) * 0.8


                # Mahsulot yaratish yoki yangilash
                product, created = Product.objects.get_or_create(
                    code=_data['code'], 
                    defaults={
                        'name': _data['name'],
                        'category': category,
                        'price': float(_data['price']),
                        'top': top,
                        'bottom': bottom,
                        'is_import': bool(_data['is_import']),
                        'is_weekly': bool(_data['is_weekly']),
                        'unit': birlik
                    }
                )

                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f"Mahsulot yaratildi: {product.name}")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f"Mahsulot allaqachon mavjud: {product.name}")
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Xato: {_data['name']} - {str(e)}")
                )
                continue

        self.stdout.write(
            self.style.SUCCESS('Mahsulotlar muvaffaqiyatli yuklandi!')
        )
