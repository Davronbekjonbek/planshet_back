import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings

from apps.form.models import ProductCategory, Birlik


class Command(BaseCommand):
    help = "datas/tovarlar_category.json faylidan tovar kategoriyalarini bazaga yuklaydi"

    def handle(self, *args, **options):
        base_dir = settings.BASE_DIR
        file_path = os.path.join(base_dir, 'datas', 'tovarlar_category.json')

        with open(file_path, encoding='utf-8') as f:
            data = json.load(f)

        for _data in data:
            try:
                # Birlikni topish yoki yaratish (edizm bo'yicha)
                birlik, birlik_created = Birlik.objects.get_or_create(
                    name=_data.get('edizm', 'дона'),
                    defaults={
                        'code': _data.get('edizm', 'дона')[:10]  # Birlik uchun kod
                    }
                )

                # ProductCategory yaratish
                category, created = ProductCategory.objects.get_or_create(
                    code=_data['kod'],
                    defaults={
                        'name': _data['nomuz'],
                        'name_ru': _data.get('nomrus', ''),
                        'number': int(_data.get('nt', 0)),
                        'union': birlik,
                        'top': int(_data.get('yuqori', 0)),
                        'bottom': int(_data.get('quyi', 0)),
                        'rasfas': _data.get('rasfas') == '1000',  # '1000' bo'lsa True
                        'is_weekly': _data.get('haftalik') == '1',  # '1' bo'lsa True
                    }
                )

                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f"Kategoriya yaratildi: {category.name}")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f"Kategoriya allaqachon mavjud: {category.name}")
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Xatolik yuz berdi: {_data.get('nomuz', 'Noma\'lum')} - {str(e)}")
                )
                continue

        self.stdout.write(
            self.style.SUCCESS('Tovar kategoriyalari muvaffaqiyatli yuklandi!')
        )