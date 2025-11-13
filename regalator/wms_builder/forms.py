from django import forms
from .models import Warehouse, WarehouseZone, WarehouseRack, WarehouseShelf
from decimal import Decimal


class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = ['name', 'description', 'width', 'height']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'width': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class ZoneForm(forms.ModelForm):
    class Meta:
        model = WarehouseZone
        fields = ['name', 'x', 'y', 'width', 'height', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'x': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'y': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'width': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
        }


class RackForm(forms.ModelForm):
    class Meta:
        model = WarehouseRack
        fields = ['name', 'x', 'y', 'width', 'height', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'x': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'y': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'width': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
        }


class ShelfForm(forms.ModelForm):
    class Meta:
        model = WarehouseShelf
        fields = ['name', 'x', 'y', 'width', 'height', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'x': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'y': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'width': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
        }


class ZoneSyncForm(forms.Form):
    """Formularz synchronizacji strefy do Location"""
    barcode = forms.CharField(
        max_length=100,
        required=True,
        label="Kod kreskowy",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Wprowadź kod kreskowy'})
    )


class RackSyncForm(forms.Form):
    """Formularz synchronizacji regału do Location"""
    barcode = forms.CharField(
        max_length=100,
        required=True,
        label="Kod kreskowy",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Wprowadź kod kreskowy'})
    )


class ShelfSyncForm(forms.Form):
    """Formularz synchronizacji półki do Location"""
    barcode = forms.CharField(
        max_length=100,
        required=True,
        label="Kod kreskowy",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Wprowadź kod kreskowy'})
    )

