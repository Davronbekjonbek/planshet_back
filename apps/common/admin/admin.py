from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.urls import path, reverse
from apps.common.admin_form import PlanshetExcelUploadForm, HududJsonUploadForm
from apps.common.models import PlanshetExcelImport, HududImportProxy
from apps.common.services.from_excel_to_db_service import PlanshetExcelImporter
from apps.common.services.hududlar_to_db_service import HududJsonImporter


# Register your models here.
class BaseAdmin(admin.ModelAdmin):
    readonly_fields = ('created_at', 'updated_at')

    # fieldsets = (
    #     ('Vaqt ma\'lumotlari', {
    #         'fields': ('created_at', 'updated_at'),
    #         'classes': ('collapse',)
    #     }),
    # )



    # Custom admin actions
    def export_as_csv(modeladmin, request, queryset):
        """Export selected items as CSV"""
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{modeladmin.model._meta.verbose_name_plural}.csv"'

        writer = csv.writer(response)

        # Write header
        field_names = [field.name for field in modeladmin.model._meta.fields]
        writer.writerow(field_names)

        # Write data
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])

        return response

    export_as_csv.short_description = "CSV formatida eksport qilish"



@admin.register(PlanshetExcelImport)
class PlanshetExcelImportAdmin(admin.ModelAdmin):
    change_list_template = "admin/planshet_import_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path("upload/", self.admin_site.admin_view(self.upload_view), name="planshet_excel_upload"),
        ]
        return my_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["upload_url"] = reverse("admin:planshet_excel_upload")
        return super().changelist_view(request, extra_context=extra_context)

    def upload_view(self, request):
        if request.method == "POST":
            form = PlanshetExcelUploadForm(request.POST, request.FILES)
            if form.is_valid():
                file = form.cleaned_data["file"]
                sheets = form.cleaned_data["sheets"]

                importer = PlanshetExcelImporter(file)
                results = importer.run(sheets=tuple(sheets))

                for key, res in results.items():
                    messages.success(
                        request,
                        _("%(key)s → imported: %(i)s, existing: %(e)s, errors: %(x)s") % {
                            "key": key, "i": res.get("imported", 0),
                            "e": res.get("existing", 0), "x": res.get("errors", 0),
                        }
                    )

                # (B) Hardcode o‘rniga dinamik reverse:
                changelist_url = reverse(
                    f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist"
                )
                return redirect(changelist_url)
        else:
            form = PlanshetExcelUploadForm()

        return render(request, "admin/import_excel.html", {"form": form})



@admin.register(HududImportProxy)
class HududImportAdmin(admin.ModelAdmin):
    change_list_template = "admin/hudud_import_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path("upload/", self.admin_site.admin_view(self.upload_view), name="hudud_json_upload"),
        ]
        return my_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        # Variant A: bevosita URL
        extra_context["upload_url"] = reverse("admin:hudud_json_upload")
        return super().changelist_view(request, extra_context=extra_context)

    def upload_view(self, request):
        if request.method == "POST":
            form = HududJsonUploadForm(request.POST, request.FILES)
            if form.is_valid():
                file = form.cleaned_data["file"]
                importer = HududJsonImporter(file_obj=file)
                try:
                    res = importer.run()
                except Exception as e:
                    messages.error(request, f"Import xatolik: {e}")
                else:
                    messages.success(
                        request,
                        _("Viloyatlar: +%(rc)s / =%(re)s; Tumanlar: +%(dc)s / =%(de)s") % {
                            "rc": res.regions_created,
                            "re": res.regions_existing,
                            "dc": res.districts_created,
                            "de": res.districts_existing,
                        }
                    )
                # changelist’ga qaytish
                url = reverse(f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist")
                return redirect(url)
        else:
            form = HududJsonUploadForm()

        return render(request, "admin/hudud_import.html", {"form": form})