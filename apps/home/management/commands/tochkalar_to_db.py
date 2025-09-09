import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings

from apps.home.models import Employee, District, Tochka


class Command(BaseCommand):
    help = "datas/tochkalar.json faylidan xodimlarni bazaga yuklaydi"

    def handle(self, *args, **options):
        base_dir = settings.BASE_DIR
        file_path = os.path.join(base_dir, 'datas', 'tochkalar.json')

        with open(file_path, encoding='utf-8') as f:
            data = json.load(f)

        for _data in data:
            try:
                # Tumanni topish (hududid bo'yicha)
                try:
                    district = District.objects.get(code=_data['hududid'][4:], region__code=_data['hududid'][:4])
                except District.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f"Tuman topilmadi: {_data['hududid']} - {_data['nomi']}")
                    )
                    continue

                # Tochka yaratish yoki yangilash
                tochka, created = Tochka.objects.get_or_create(
                        name=_data['nomi'],
                        district=district,
                        inn=_data['inn'] if _data['inn'] else None,
                        address=_data['manzil'] if _data['manzil'] else None,
                        plan=_data['planid'] if _data['planid'] else None,
                        is_active=True,
                        lat=_data['lat'] if _data['lat'] else 0.0,
                        lon=_data['lon'] if _data['lon'] else 0.0,
                        employee=Employee.objects.get(pinfl=_data['pinfl']),
                        code = _data['code']
                    )
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f"Tochka yaratildi: {tochka.name}")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f"Tochka allaqachon mavjud: {tochka.name}")
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Xatolik yuz berdi: {_data['nomi']} - {str(e)}")
                )
                continue
        self.stdout.write(self.style.SUCCESS('Tochkalar muvaffaqiyatli yuklandi!'))


