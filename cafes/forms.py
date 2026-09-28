"""Formularios del CRUD (capa de validación, separada de las vistas)."""

import re
from decimal import Decimal

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Cafe, Receta


class RecetaForm(forms.ModelForm):
    """Alta y edición de una receta V60.

    Replica los validadores del modelo y suma reglas de negocio que el
    barista debe cumplir antes de persistir (ratio, tiempo, bloom).
    """

    class Meta:
        model = Receta
        fields = [
            'cafe', 'autor', 'gramos_cafe', 'agua_total', 'ratio', 'temperatura',
            'molienda', 'molino', 'clicks_molino', 'bloom_agua', 'bloom_segundos',
            'vertidos', 'tiempo_total', 'publicada',
        ]
        widgets = {
            'vertidos': forms.TextInput(attrs={'placeholder': '0:00 45g, 0:40 140g, 1:20 240g'}),
            'ratio': forms.TextInput(attrs={'placeholder': '1:16'}),
            'tiempo_total': forms.TextInput(attrs={'placeholder': '3:00'}),
        }

    def clean_ratio(self):
        ratio = self.cleaned_data['ratio'].strip()
        if not re.fullmatch(r'1:\d{1,2}', ratio):
            raise forms.ValidationError('Usa el formato 1:15, 1:16 o 1:17.')
        return ratio

    def clean_tiempo_total(self):
        tiempo = self.cleaned_data['tiempo_total'].strip()
        if not re.fullmatch(r'\d:[0-5]\d', tiempo):
            raise forms.ValidationError('El tiempo debe ir en formato m:ss (ej: 3:00).')
        return tiempo

    def clean(self):
        datos = super().clean()
        gramos = datos.get('gramos_cafe')
        bloom = datos.get('bloom_agua')
        if gramos is not None and bloom is not None:
            minimo = int((gramos * Decimal('2')).to_integral_value())
            maximo = int((gramos * Decimal('4')).to_integral_value())
            if not (minimo <= bloom <= maximo):
                self.add_error(
                    'bloom_agua',
                    f'El bloom debe estar entre 2 y 4 veces la dosis ({minimo}–{maximo} g).',
                )
        return datos


class CafeForm(forms.ModelForm):
    """Alta de un lote (gestión de colecciones fuera del Admin)."""

    class Meta:
        model = Cafe
        fields = ['nombre', 'tostador', 'origen', 'imagen']


class RegistroBaristaForm(UserCreationForm):
    """Registro público: el usuario entra al grupo Baristas al guardarse."""

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username',)
