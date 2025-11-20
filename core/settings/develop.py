from .base import *  # noqa
from ..jazzmin_conf import *


DEBUG = True
CELERY_TASK_ALWAYS_EAGER = True

# base.py da DEBUG False bo'lishi mumkinligi sababli, middlewarelarni bu yerda tekshirib qo'shamiz
if 'debug_toolbar.middleware.DebugToolbarMiddleware' not in MIDDLEWARE:
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

if 'query_counter.middleware.DjangoQueryCounterMiddleware' not in MIDDLEWARE:
    MIDDLEWARE += ['query_counter.middleware.DjangoQueryCounterMiddleware']

INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
    '172.16.5.61',
    '172.16.8.137'
]

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: True,
    'SHOW_TEMPLATE_CONTEXT': True,
}

CSRF_TRUSTED_ORIGINS += [
    "http://172.16.8.137:8000",
]
