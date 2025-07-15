from datetime import datetime

from ..models import Product, TochkaProductHistory
from apps.home.models import PeriodDate


def get_product_by_uuid(uuid):
    """
    Retrieve a TochkaProduct instance by its UUID.

    :param uuid: UUID of the TochkaProduct.
    :return: TochkaProduct instance or None if not found.
    """
    try:
        return Product.objects.get(uuid=uuid)
    except Product.DoesNotExist:
        return None


def get_period_by_today():
    """
    Get the current period based on today's date.

    :return: Period string in the format 'YYYY-MM'.
    """
    today = datetime.today().date()
    try:
        return PeriodDate.objects.get(date=today)
    except PeriodDate.DoesNotExist:
        return None


def get_period_by_type_today(period_type:str = 'weekly'):
    """
    Get the current period based on today's date.

    :return: Period string in the format 'YYYY-MM'.
    """
    today = datetime.today().date()
    try:
        return PeriodDate.objects.get(date=today, period__period_type=period_type)
    except PeriodDate.DoesNotExist:
        return None


def get_tochka_product_history(ntochka, product, period):
    try:
        return TochkaProductHistory.objects.get(
            ntochka=ntochka,
            product=product,
            period__period=period,
        )
    except TochkaProductHistory.DoesNotExist:
        return None

