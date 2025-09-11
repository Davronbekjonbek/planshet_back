# apps/importer/forms.py
from django import forms

class PlanshetExcelUploadForm(forms.Form):
    file = forms.FileField(
        label="Excel fayl (.xlsx)",
        help_text="datas/planshet_data.xlsx o'rniga admin orqali yuklang",
        widget=forms.ClearableFileInput(attrs={"accept": ".xlsx"})
    )
    sheets = forms.MultipleChoiceField(
        label="Qaysi listlarni import qilamiz?",
        choices=[
            ("users", "users → Employee"),
            ("obyekt", "obyekt → Tochka"),
            ("category", "category → ProductCategory"),
            ("product", "product → Product"),
        ],
        initial=["users", "obyekt", "category", "product"],
        widget=forms.CheckboxSelectMultiple
    )


class HududJsonUploadForm(forms.Form):
    file = forms.FileField(
        label="Hududlar JSON (.json)",
        widget=forms.ClearableFileInput(attrs={"accept": ".json"})
    )