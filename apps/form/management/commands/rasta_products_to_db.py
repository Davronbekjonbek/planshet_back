import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings

from apps.home.models import NTochka, Tochka
from apps.form.models import Product, TochkaProduct


class Command(BaseCommand):
    help = "datas/rasta_products.json faylidan Rasta Mahsulotlarini yuklaydi"

    def handle(self, *args, **options):
        base_dir = settings.BASE_DIR
        file_path = os.path.join(base_dir, 'datas', 'rasta_products.json')

        with open(file_path, encoding='utf-8') as f:
            data = json.load(f)

        for _data in data:
            try:
                # Mahsulotni topish
                product = Product.objects.get(code=_data['product_code'])
                # Rasta (NTochka) ni topish
                ntochka = NTochka.objects.get(id=_data['rasta_code'])
                # Hudud (Tochka)
                hudud = ntochka.hudud

                # TochkaProduct yaratish yoki yangilash
                tp, created = TochkaProduct.objects.get_or_create(
                    product=product,
                    ntochka=ntochka,
                    defaults={
                        'hudud': hudud,
                        'last_price': product.price,
                        'previous_price': product.price,
                        'is_active': True
                    }
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(
                        f"TochkaProduct yaratildi: {product.name} - {ntochka.name}"
                    ))
                else:
                    self.stdout.write(self.style.WARNING(
                        f"TochkaProduct allaqachon mavjud: {product.name} - {ntochka.name}"
                    ))

            except Product.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Mahsulot topilmadi: {_data['product_code']}"))
            except NTochka.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Rasta topilmadi: {_data['rasta_code']}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Xato: {_data} - {str(e)}"))

        self.stdout.write(self.style.SUCCESS('Rasta Mahsulotlar muvaffaqiyatli yuklandi!'))
