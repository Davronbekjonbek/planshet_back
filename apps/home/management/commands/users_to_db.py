import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings

from apps.home.models import Employee, District


class Command(BaseCommand):
    help = "datas/users.json faylidan xodimlarni bazaga yuklaydi"

    def handle(self, *args, **options):
        base_dir = settings.BASE_DIR
        file_path = os.path.join(base_dir, 'datas', 'users.json')

        with open(file_path, encoding='utf-8') as f:
            data = json.load(f)

        for _data in data:
            try:
                # Tumanni topish (hududkod bo'yicha)
                try:
                    district = District.objects.get(code=_data['hududkod'][4:], region__code=_data['hududkod'][:4])
                except District.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f"Tuman topilmadi: {_data['hududkod']} - {_data['fio']}")
                    )
                    continue

                # Xodimni yaratish yoki yangilash
                employee, created = Employee.objects.get_or_create(
                    login=_data['login'],
                    defaults={
                        'full_name': _data['fio'],
                        'password': _data['password'],
                        'district': district,
                        'status': float(_data['status']),
                        'permission1': _data['permission1'],
                        'permission2': _data['permission2'],
                        'permission3': _data['permission3'],
                        'permission4': _data['permission4'] if _data['permission4'] else False,
                        'permission5': _data['permission5'] if _data['permission5'] else False,
                        'phone1': _data['phone1'] if _data['phone1'] else None,
                        'phone2': _data['phone2'] if _data['phone2'] else None,
                        'permission_plov': _data['permission_plov'] if _data['permission_plov'] else False,
                        'gps_permission': _data['gps_permission'],
                        'lang': _data['lang'],
                        'pinfl': _data.get('pinfl', ''),
                    }
                )

                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f"Xodim yaratildi: {employee.full_name}")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f"Xodim allaqachon mavjud: {employee.full_name}")
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Xato: {_data['fio']} - {str(e)}")
                )

        self.stdout.write(
            self.style.SUCCESS("Import jarayoni tugadi!")
        )