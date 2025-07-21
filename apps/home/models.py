import  uuid
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel

ICON_COLORS = {
    'restaurant': '#FF7043',       # Kafe oshxona – iliq
    'water': '#039BE5',            # Suv xizmatlari – moviy
    'flash': '#FDD835',            # Elektr – sariq
    'shirt': '#BA68C8',            # Kiyim – binafsha
    'bed': '#8D6E63',              # Mebel – jigar rang
    'cart': '#4CAF50',             # Do‘kon – yashil
    'eye': '#00ACC1',              # Optika – havorang
    'leaf': '#558B2F',             # Qishloq xo‘jaligi – tabiiy yashil
    'construct': '#FFA000',        # Ta’mirlash – to'q sariq
    'home': '#43A047',             # Oilaviy biznes – yashil
    'briefcase': '#546E7A',        # Xizmat joyi – to'q kulrang
    'storefront': '#8E24AA',       # Savdo markazi – binafsha
    'car': '#616161',              # Avto – kulrang
    'tv': '#3949AB',               # Texnika – ko‘k
    'school': '#1E88E5',           # O‘quv markazi – moviy
    'person': '#F06292',           # Uyda ishlovchi – pushti
    'people': '#6D4C41',           # Xususiy shaxs – jigarrang
    'nutrition': '#66BB6A',        # Oziq-ovqat – och yashil
    'location': '#BDBDBD',         # Boshqa – neytral kulrang
}

class Region(BaseModel):
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Viloyatning nomi"))
    code = models.CharField(max_length=10, unique=True, verbose_name=_("Viloyatning kodi"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Viloyat")
        verbose_name_plural = _("Viloyatlar")
        ordering = ['name']
        db_table = 'region'


class District(BaseModel):
    name = models.CharField(max_length=100, verbose_name=_("Tumanning nomi"))
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='districts', verbose_name=_("Viloyat"))
    code = models.CharField(max_length=10, verbose_name=_("Tumanning kodi"))


    def __str__(self):
        return f"{self.region.code}{self.code} - {self.name}"

    class Meta:
        verbose_name = "Tuman"
        verbose_name_plural = "Tumanlar"
        ordering = ['name']
        unique_together = ('code', 'region')
        db_table = 'district'


class Period(BaseModel):
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Davrning nomi"))
    period_type = models.CharField(max_length=50, choices=(('weekly', 'Haftalik'), ('monthly', 'Oylik')), default='monthly', verbose_name=_("Davr turi"))
    is_active = models.BooleanField(default=True, verbose_name=_("Faol"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Davr"
        verbose_name_plural = "Davrlar"
        db_table = 'period'


class PeriodDate(BaseModel):
    period = models.ForeignKey(Period, on_delete=models.CASCADE, related_name='period_dates', verbose_name=_("Davr"))
    date = models.DateField(verbose_name=_("Sana"))

    def __str__(self):
        return f"{self.period.name} - {self.date}"

    class Meta:
        verbose_name = "Davr sanasi"
        verbose_name_plural = "Davr sanalari"
        db_table = 'period_date'



class Tochka(BaseModel):
    ICON_CHOICES = (
        ('restaurant', 'Kafe oshxona'),
        ('water', 'Suv xizmatlari'),
        ('flash', 'Elektr ustasi'),
        ('shirt', 'Kiyim do‘koni'),
        ('bed', 'Uy mebellari'),
        ('cart', 'Mahsulot do‘koni'),
        ('eye', 'Ko‘zoynak optika'),
        ('leaf', 'Qishloq xo‘jaligi'),
        ('construct', 'Ta’mirlash ishlari'),
        ('home', 'Oilaviy Biznes'),
        ('briefcase', 'Xizmat joyi'),
        ('storefront', 'Savdo markazi'),
        ('car', 'Avto do‘kon'),
        ('tv', 'Elektronika texnika'),
        ('school', 'O‘quv markazi'),
        ('person', 'Uyda ishlovchi'),
        ('people', 'Xususiy shaxs'),
        ('nutrition', 'Oziq ovqat mahsulotlari'),
        ('location', 'Boshqa'),
    )

    name = models.CharField(max_length=100, verbose_name=_("Obyekt nomi"))
    icon = models.CharField(max_length=10, choices=ICON_CHOICES, default='nutrition', verbose_name=_("Icon"))
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, verbose_name=_("UUID"))
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='tochkas', verbose_name=_("Tuman"))
    code = models.CharField(max_length=20, unique=True, verbose_name=_("Obyekt kodi"))
    inn = models.CharField(max_length=20, default=0, blank=True,  verbose_name=_("INN kodi"))
    address = models.CharField(max_length=255, verbose_name=_("Manzil"), blank=True, null=True)
    plan = models.IntegerField(verbose_name=_("Plan id"), default=0)
    lat = models.FloatField(verbose_name=_("Lat"), default=0.0)
    lon = models.FloatField(verbose_name=_("Lon"), default=0.0)
    employee = models.ForeignKey('home.Employee', on_delete=models.CASCADE, related_name='tochkas', verbose_name=_("Xodim"))
    is_active = models.BooleanField(default=True, verbose_name=_("Faol"))

    @property
    def icon_color(self):
        return ICON_COLORS.get(self.icon, '#BDBDBD')

    @property
    def icon_display(self):
        return  self.get_icon_display()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Obyekt"
        verbose_name_plural = "Obyektlar"
        ordering = ['name']
        db_table = 'obyekt'


class NTochka(BaseModel):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, verbose_name=_("UUID"))
    name = models.CharField(max_length=100, verbose_name=_("Rasta nomi"))
    hudud = models.ForeignKey(Tochka, on_delete=models.CASCADE, related_name='ntochkas', verbose_name=_("Obyekt"))
    is_active = models.BooleanField(default=True, verbose_name=_("Faol"))
    in_proccess = models.BooleanField(default=False, verbose_name=_("Ariza orqali yaratilgan"))

    def __str__(self):
        return f"{self.hudud.name} - {self.name}"

    class Meta:
        verbose_name = "Rasta"
        verbose_name_plural = "Rastalar"
        ordering = ['name']
        db_table = 'rasta'


class Employee(BaseModel):
    full_name = models.CharField(max_length=200, verbose_name=_("F.I.Sh"))
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, verbose_name=_("UUID"))
    login = models.CharField(max_length=100, unique=True, verbose_name=_("Login"))
    password = models.CharField(max_length=100, verbose_name=_("Parol"))
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='employees', verbose_name=_("Tuman"))
    status = models.FloatField(verbose_name=_("Status"), default=1.0)
    pinfl = models.CharField(max_length=14, blank=True, null=True, verbose_name=_("PINFL"), unique=True)

    permission1 = models.BooleanField(default=True, verbose_name=_("Ruxsat 1"))
    permission2 = models.BooleanField(default=True, verbose_name=_("Ruxsat 2"))
    permission3 = models.BooleanField(default=True, verbose_name=_("Ruxsat 3"))
    permission4 = models.BooleanField(default=False, verbose_name=_("Ruxsat 4"))
    permission5 = models.BooleanField(default=False, verbose_name=_("Ruxsat 5"))

    phone1 = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Telefon 1  (mtel)"))
    phone2 = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Telefon 2  (otel)"))

    permission_plov = models.BooleanField(default=False, verbose_name=_("Palov uchun ruxsat"))
    gps_permission = models.BooleanField(default=True, verbose_name=_("GPS ruxsat"))
    lang = models.CharField(max_length=10, default='uz', verbose_name=_("Til"), choices=(('uz', 'Uzbek'), ('ru', 'Rus')), blank=True)

    def __str__(self):
        return f"{self.full_name}"

    class Meta:
        verbose_name = "Xodim"
        verbose_name_plural = "Xodimlar"
        db_table = 'employee'

