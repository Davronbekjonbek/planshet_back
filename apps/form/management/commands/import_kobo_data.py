from django.core.management.base import BaseCommand
from apps.form.utils.kobo_import import KoBoDataImporter


class Command(BaseCommand):
    help = 'KoBoToolbox dan ma\'lumotlarni import qilish'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Faqat test rejimida ishlatish (ma\'lumot saqlanmaydi)',
        )

    def handle(self, *args, **options):
        importer = KoBoDataImporter()

        if options['dry_run']:
            self.stdout.write("DRY RUN rejimi")
            data = importer.fetch_kobo_data()
            if data:
                self.stdout.write(f"Jami {data.get('count', 0)} ta yozuv topildi")
        else:
            results = importer.import_data()

            if results['success']:
                stats = results['results']
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Import muvaffaqiyatli yakunlandi:\n"
                        f"- Jami submissionlar: {stats['total_submissions']}\n"
                        f"- Qayta ishlangan mahsulotlar: {stats['processed_products']}\n"
                        f"- Saqlangan mahsulotlar: {stats['saved_products']}\n"
                        f"- Xatoliklar: {stats['errors']}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"Import xatolik bilan yakunlandi: {results.get('error')}")
                )
