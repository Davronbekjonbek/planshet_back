from django import forms
from django.forms import ModelForm, CheckboxSelectMultiple
from .models import Application, Product, ProductCategory
from apps.home.models import Tochka, NTochka, PeriodDate


class ApplicationForm(ModelForm):
    """Ariza yaratish formasi"""
    
    class Meta:
        model = Application
        fields = [
            'application_type', 
            'tochka', 
            'tochkas',
            'ntochka', 
            'ntochkas',
            'period',
            'comment'
        ]
        widgets = {
            'application_type': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'tochka': forms.Select(attrs={
                'class': 'form-control select2'
            }),
            'tochkas': CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            'ntochka': forms.Select(attrs={
                'class': 'form-control select2'
            }),
            'ntochkas': CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            'period': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Izoh...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set queryset for foreign keys
        self.fields['tochka'].queryset = Tochka.objects.filter(is_active=True)
        self.fields['tochkas'].queryset = Tochka.objects.filter(is_active=True)
        self.fields['ntochka'].queryset = NTochka.objects.filter(is_active=True)
        self.fields['ntochkas'].queryset = NTochka.objects.filter(is_active=True)
        self.fields['period'].queryset = PeriodDate.objects.all().order_by('-id')
        
        # Make fields optional based on application type
        self.fields['tochka'].required = False
        self.fields['tochkas'].required = False
        self.fields['ntochka'].required = False
        self.fields['ntochkas'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        app_type = cleaned_data.get('application_type')
        
        # Validate based on application type
        if app_type in ['for_close_rasta', 'for_open_rasta']:
            if not cleaned_data.get('ntochka') and not cleaned_data.get('ntochkas'):
                raise forms.ValidationError('Rasta tanlash majburiy!')
        
        elif app_type in ['for_close_obyekt', 'for_open_obyekt']:
            if not cleaned_data.get('tochka') and not cleaned_data.get('tochkas'):
                raise forms.ValidationError('Obyekt tanlash majburiy!')
        
        return cleaned_data


class ProductSelectionForm(forms.Form):
    """Mahsulotlarni tanlash formasi"""
    
    products = forms.ModelMultipleChoiceField(
        queryset=Product.objects.filter(is_active=True),
        widget=CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        required=False,
        label='Mahsulotlar'
    )
    
    def __init__(self, *args, **kwargs):
        category_id = kwargs.pop('category_id', None)
        super().__init__(*args, **kwargs)
        
        if category_id:
            self.fields['products'].queryset = Product.objects.filter(
                category_id=category_id,
                is_active=True
            )


class ApplicationFilterForm(forms.Form):
    """Arizalarni filtrlash formasi"""
    
    STATUS_CHOICES = [
        ('', 'Barchasi'),
        ('pending', 'Kutilmoqda'),
        ('approved', 'Tasdiqlangan'),
        ('rejected', 'Rad etilgan'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    application_type = forms.ChoiceField(
        choices=[('', 'Barchasi')] + list(Application.APPLICATION_TYPE_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    period = forms.ModelChoiceField(
        queryset=PeriodDate.objects.all(),
        required=False,
        empty_label='Barchasi',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Qidirish...'
        })
    )