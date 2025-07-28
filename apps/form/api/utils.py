from datetime import datetime, time, timedelta

from ..models import Product, TochkaProduct, TochkaProductHistory
from apps.home.models import PeriodDate, Tochka, NTochka

from django.core.cache import cache

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


def get_period_by_type_today(period_type='weekly'):
    """
    Bugungi kun uchun period olish (cache bilan)
    """
    today = datetime.today()
    cache_key = f'period_{period_type}_{today}'
    period = cache.get(cache_key)

    if period is None:
        try:
            period = PeriodDate.objects.get(
                period__period_type=period_type,
                date = today.date()
            )
            seconds_until_midnight = (
                    datetime.combine(today + timedelta(1), time.min) -
                    datetime.now()
            ).seconds
            cache.set(cache_key, period, seconds_until_midnight)
        except PeriodDate.DoesNotExist:
            return None

    return period


def get_tochka_product_history(ntochka, product, period):
    try:
        return TochkaProductHistory.objects.get(
            ntochka=ntochka,
            product=product,
            period__period=period,
        )
    except TochkaProductHistory.DoesNotExist:
        return None


def generate_tochka_code(district):
    """
    Tochka uchun yangi kod generatsiya qilish
    """
    last_tochka = Tochka.objects.filter(
        district=district
    ).order_by('-id').values_list('code', flat=True).first()

    if last_tochka and '-' in last_tochka:
        last_num = int(last_tochka.split('-')[-1])
        new_code = f"{district.code}-{last_num + 1:04d}"
    else:
        new_code = f"{district.code}-0001"

    return new_code


def generate_ntochka_code(tochka):
    """
    NTochka uchun yangi kod generatsiya qilish
    """

    last_ntochka = NTochka.objects.filter(
        hudud=tochka
    ).order_by('-id').values_list('code', flat=True).first()

    if last_ntochka and '-' in last_ntochka:
        last_num = int(last_ntochka.split('-')[-1])
        new_code = f"{tochka.code}-{last_num + 1:03d}"
    else:
        new_code = f"{tochka.code}-001"

    return new_code


def get_tochka_product_by_id(tochka_product_id):
    """
    Get TochkaProduct by ID.

    :param tochka_product_id: ID of the TochkaProduct
    :return: TochkaProduct instance or None if not found
    """
    try:
        return TochkaProduct.objects.get(id=tochka_product_id)
    except TochkaProduct.DoesNotExist:
        return None
