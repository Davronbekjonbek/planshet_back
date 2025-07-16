from .models import Period, PeriodDate
from django import forms
from .widget import MultiDateWidget


class PeriodForm(forms.ModelForm):
    selected_dates = forms.CharField(
        widget=MultiDateWidget(),
        required=False,
        help_text="Kalendardan bir nechta kunni tanlang",
        label="Sanalarni tanlang"
    )

    class Meta:
        model = Period
        fields = ['name', 'period_type', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # Mavjud period uchun tanlangan sanalarni yuklash
            existing_dates = list(self.instance.period_dates.values_list('date', flat=True))
            if existing_dates:
                date_strings = [str(d) for d in existing_dates]
                self.fields['selected_dates'].initial = ','.join(date_strings)

    def save(self, commit=True):
        instance = super().save(commit)
        # Eski sanalarni o'chirish
        if instance.pk and self.instance.period_dates.exists():
            instance.period_dates.all().delete()

        # Yangi sanalarni saqlash
        selected_dates = self.cleaned_data.get('selected_dates', [])
        print(selected_dates)
        if selected_dates:
            for date_str in selected_dates:
                if date_str.strip():
                    try:
                        from datetime import datetime
                        # Sana formatini tekshirish
                        parsed_date = datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
                        PeriodDate.objects.create(
                            period=instance,
                            date=parsed_date
                        )
                    except ValueError as e:
                        print(f"Invalid date format {date_str}: {e}")
                    except Exception as e:
                        print(f"Error saving date {date_str}: {e}")
        return instance