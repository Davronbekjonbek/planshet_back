from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import PeriodDate, Period


@receiver(post_save, sender=PeriodDate)
def create_history_for_new_period(sender, instance, created, **kwargs):
    """
    Yangi PeriodDate yaratilganda, oldingi perioddagi
    'vaqtinchalik' yoki 'mavsumiy' statusli history larni
    yangi period uchun ko'chirish.
    """
    if not created:
        return

    # Faqat weekly period uchun
    if instance.period.period_type != 'weekly':
        return

    # Shu Period uchun birinchi PeriodDate bo'lishi kerak
    if PeriodDate.objects.filter(period=instance.period).count() > 1:
        return

    # Oldingi Period ni topish (id bo'yicha oldingi weekly period)
    previous_period = Period.objects.filter(
        id__lt=instance.period.id,
        period_type='weekly'
    ).order_by('-id').first()

    if not previous_period:
        return

    # Oldingi period ning PeriodDate sini topish
    previous_period_dates = PeriodDate.objects.filter(
        period=previous_period
    )

    if not previous_period_dates.exists():
        return

    # Import here to avoid circular import
    from apps.form.models import TochkaProductHistory

    # Oldingi perioddagi shartga mos history larni olish
    previous_histories = TochkaProductHistory.objects.filter(
        period__in=previous_period_dates,
        status__in=['vaqtinchalik', 'mavsumiy'],
        tochka_product__is_weekly=True
    ).select_related('tochka_product')

    # Yangi history larni yaratish
    new_histories = []
    for history in previous_histories:
        new_histories.append(
            TochkaProductHistory(
                product=history.product,
                ntochka=history.ntochka,
                hudud=history.hudud,
                tochka_product=history.tochka_product,
                employee=history.employee,
                period=instance,  # Yangi PeriodDate
                status=history.status,  # Oldingi status saqlanadi
                price=0,
                unit_price=0,
                unit_miqdor=history.tochka_product.miqdor,
                is_from_period_create=True,
            )
        )

    if new_histories:
        TochkaProductHistory.objects.bulk_create(
            new_histories,
            ignore_conflicts=True  # unique_together xatoligini oldini olish
        )
