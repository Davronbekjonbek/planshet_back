from celery import shared_task
from .kobo_import import KoBoDataImporter
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def import_kobo_data_task(self):
    """KoBoToolbox ma'lumotlarini import qilish uchun Celery task"""
    try:
        importer = KoBoDataImporter()
        results = importer.import_data()

        if results['success']:
            logger.info(f"Celery task muvaffaqiyatli yakunlandi: {results['results']}")
            return results
        else:
            logger.error(f"Celery task xatolik bilan yakunlandi: {results}")
            raise Exception(results.get('error', 'Noma\'lum xatolik'))

    except Exception as exc:
        logger.error(f"Celery task da xatolik: {exc}")
        # Retry qilish
        if self.request.retries < self.max_retries:
            logger.info(f"Task ni qayta ishga tushirish: {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(countdown=60 * (self.request.retries + 1), exc=exc)
        else:
            logger.error("Barcha retry urinishlar muvaffaqiyatsiz tugadi")
            raise exc
