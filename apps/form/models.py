import uuid

from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from apps.common.models import BaseModel

def validate_file_size(value):
    """Validate file size is not greater than 50KB"""
    max_size = 50 * 1024  # 50KB
    if value.size > max_size:
        size_kb = max_size / 1024
        raise ValidationError(
            _(f'Faylning hajmi {size_kb} kbdan katta bo\'lishi mumkin emas'),
            params={'max_size': max_size},
        )


class Birlik(BaseModel):
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Birlikning nomi"))
    code = models.CharField(max_length=10, unique=True, verbose_name=_("Birlikning kodi"))
    miqdor = models.FloatField(verbose_name=_("Miqdor"), default=0.0)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Birlik"
        verbose_name_plural = "Birliklar"
        ordering = ['name']



class ProductCategory(BaseModel):
    name = models.CharField(max_length=400, unique=True, verbose_name=_("Kategoriyaning nomi"))
    name_ru = models.CharField(max_length=400, unique=True, null=True,blank=True, verbose_name=_("Kategoriyaning nomi (Ruscha)"))
    number = models.IntegerField(default=0, verbose_name=_("Kategoriyaning tartib raqami (nt)"))
    code = models.CharField(max_length=10, unique=True, verbose_name=_("Kategoriyaning kodi"))
    union = models.ForeignKey(Birlik, on_delete=models.CASCADE, related_name='categories', verbose_name=_("Birlik"))
    rasfas = models.BooleanField(default=False, verbose_name=_("Rasfas"))
    is_weekly = models.BooleanField(default=False, verbose_name=_("Haftalik"))
    logo = models.ImageField(
        upload_to='product_category_logos/', null=True, blank=True, verbose_name=_("Logo"),
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png']),
            validate_file_size
        ],
    )
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Mahsulot Kategoriyasi"
        verbose_name_plural = "Mahsulot Kategoriyalari"
        ordering = ['name']


class Product(BaseModel):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, verbose_name=_("UUID"))
    name = models.CharField(max_length=400, verbose_name=_("Mahsulotning nomi"))
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name='products', verbose_name=_("Kategoriyasi"))
    code = models.CharField(max_length=10, unique=True, verbose_name=_("Mahsulot kodi"))
    price = models.FloatField(verbose_name=_("Narxi"), default=0.0)
    top = models.IntegerField(default=0, verbose_name=_("Yuqori"))
    bottom = models.IntegerField(default=0, verbose_name=_("Quyi"))
    unit = models.ForeignKey(Birlik, on_delete=models.CASCADE, related_name='products', verbose_name=_("O'lchov birligi"))
    is_import = models.BooleanField(default=False, verbose_name=_("Import qilingan"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Mahsulot"
        verbose_name_plural = "Mahsulotlar"
        ordering = ['name']


class TochkaProduct(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='huds', verbose_name=_("Mahsulot"))
    ntochka = models.ForeignKey('home.NTochka', on_delete=models.CASCADE, related_name='products', verbose_name=_("Kichik hudud"))
    hudud = models.ForeignKey('home.Tochka', on_delete=models.CASCADE, related_name='products', verbose_name=_("Hudud"))
    last_price = models.FloatField(verbose_name=_("Oxirgi Narxi"), default=0.0)
    previous_price = models.FloatField(verbose_name=_("Oldingi Narxi"), default=0.0)
    is_active = models.BooleanField(default=True, verbose_name=_("Faol"))
    is_udalen = models.BooleanField(default=True, verbose_name=_("Udalen"))


    def __str__(self):
        return f"{self.product.name} - {self.ntochka.name}"

    class Meta:
        verbose_name = "Mahsulot Hudud"
        verbose_name_plural = "Mahsulot Hududlar"
        ordering = ['product__name']
        unique_together = ('product', 'ntochka')  # Mahsulot, Hudud va Kichik hudud birgalikda unikalligi uchun


class TochkaProductHistory(BaseModel):
    PRODUCT_STATUS_CHOICES = [
        ('mavjud', 'Mahsulot mavjud'),
        ('chegirma', 'Mahsulot chegirma asosida sotilayabdi'),
        ('mavsumiy', 'Mavjud emas (Mavsumiy mahsulot)'),
        ('vaqtinchalik', 'Mavjud emas (Vaqtincha mavjud emas)'),
        ('sotilmayapti', 'Mavjud emas (Mahsulot sotilmayabdi)'),
        ('obyekt_yopilgan', 'Mavjud emas (Obyekt yopilgan)'),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='history', verbose_name=_("Mahsulot"))
    ntochka = models.ForeignKey('home.NTochka', on_delete=models.CASCADE, related_name='product_history', verbose_name=_("Ntochka"))
    hudud = models.ForeignKey('home.Tochka', on_delete=models.CASCADE, related_name='product_history', verbose_name=_("Hudud"))
    price = models.FloatField(verbose_name=_("Narxi"), default=0.0)
    unit_miqdor = models.FloatField(verbose_name=_("Birlik miqdori"), default=0.0)
    unit_price = models.FloatField(verbose_name=_("Birlik narxi"), default=0.0)
    employee = models.ForeignKey('home.Employee', on_delete=models.CASCADE, related_name='product_history', verbose_name=_("Xodim"))
    period = models.ForeignKey('home.PeriodDate', on_delete=models.CASCADE, related_name='product_history', verbose_name=_("Davr"))
    status = models.CharField(max_length=15, verbose_name=_("Status"), default='mavjud', choices=PRODUCT_STATUS_CHOICES)
    is_checked = models.BooleanField(default=False, verbose_name=_("Tekshirilgan"))
    is_active = models.BooleanField(default=True, verbose_name=_("Faol"))

    def __str__(self):
        return f"{self.product.name} - {self.ntochka.name} - {self.price}"

    class Meta:
        verbose_name = "Mahsulot Narx Tarixi"
        verbose_name_plural = "Mahsulot Narx Tarixlari"
        ordering = ['product__name']
        unique_together = ('product', 'ntochka', 'period')