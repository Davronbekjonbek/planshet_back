import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings

from apps.home.models import Tochka, NTochka


class Command(BaseCommand):
    help = "datas/rastalar.json faylidan rastalarni bazaga yuklaydi"

    def handle(self, *args, **options):
        base_dir = settings.BASE_DIR
        file_path = os.path.join(base_dir, 'datas', 'rastalar.json')

        with open(file_path, encoding='utf-8') as f:
            data = json.load(f)

        for _data in data:
            try:
                # Tochka (Obyekt) ni olish yoki yaratish
                obyekt_name = _data['name']
                obyekt_code = _data['obyekt']

                tochka = Tochka.objects.filter(code=obyekt_code).first()
                # NTochka (Rasta) ni yaratish
                ntochka, n_created = NTochka.objects.get_or_create(
                    name=obyekt_name,
                    hudud=tochka
                )

                if n_created:
                    self.stdout.write(
                        self.style.SUCCESS(f"NTochka yaratildi: {ntochka.name}")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f"NTochka allaqachon mavjud: {ntochka.name}")
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Xato: {_data['name']} - {str(e)}")
                )

        self.stdout.write(
            self.style.SUCCESS("Import jarayoni tugadi!")
        )
