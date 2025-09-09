from django.db import models

# Create your models here.
class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan sana")

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.__class__.__name__} created at {self.created_at}"



class KoboForm(models.Model):
    form_id = models.CharField(max_length=100, unique=True, verbose_name="Kobo form id")
    name = models.CharField(max_length=255, verbose_name="Form nomi")
    api_token = models.CharField(max_length=255, verbose_name="API token")
    is_active = models.BooleanField(default=True, verbose_name="Faol")


class PlanshetExcelImport(KoboForm):
    class Meta:
        proxy = True
        verbose_name = "📥 Excel import (Planshet)"
        verbose_name_plural = "📥 Excel import (Planshet)"


class HududImportProxy(KoboForm):
    class Meta:
        proxy = True
        verbose_name = "📥 Hududlar (JSON import)"
        verbose_name_plural = "📥 Hududlar (JSON import)"