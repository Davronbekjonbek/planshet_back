from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'import-kobo-data-every-hour': {
        'task': 'apps.utils.tasks.import_kobo_data_task',
        'schedule': crontab(minute=0),  # Har soatda
        # 'schedule': crontab(minute=0, hour='*/6'),  # 6 soatda bir marta
        # 'schedule': crontab(minute=0, hour=0),  # Har kuni yarim tunda
    },
}