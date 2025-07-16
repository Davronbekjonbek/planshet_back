from django.contrib import admin

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