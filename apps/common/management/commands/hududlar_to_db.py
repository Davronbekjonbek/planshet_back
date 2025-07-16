import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings

from apps.home.models import Region, District


class Command(BaseCommand):
    help = "datas/hududlar.json faylidan viloyat va tumanlarni bazaga yuklaydi"

    def handle(self, *args, **options):
        base_dir = settings.BASE_DIR
        file_path = os.path.join(base_dir, 'datas', 'hududlar.json')

        with open(file_path, encoding='utf-8') as f:
            data = json.load(f)

        for region_data in data:
            print(region_data)
            region, _ = Region.objects.get_or_create(
                code=region_data['kod'],
                defaults={'name': region_data['viloyat']}
            )
            for district_data in region_data.get('childs', []):
                print(district_data)
                District.objects.get_or_create(
                    code=district_data['tumankod'],
                    region=region,
                    defaults={'name': district_data['tuman']}
                )
        self.stdout.write(self.style.SUCCESS('Hududlar muvaffaqiyatli yuklandi!'))