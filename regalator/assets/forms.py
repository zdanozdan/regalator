from django import forms
from .models import Asset, Category, Tag


class AssetUploadForm(forms.ModelForm):
    """Formularz uploadu assetu"""
    
    class Meta:
        model = Asset
        fields = ['title', 'description', 'file', 'file_type', 'category', 'tags', 'is_public', 'is_splash_image']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Wprowadź tytuł assetu'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Opis assetu (opcjonalnie)'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*,.pdf,.doc,.docx,.txt,.mp4,.mp3,.wav'
            }),
            'file_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'tags': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'size': 5
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_splash_image': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
        self.fields['tags'].queryset = Tag.objects.all()
        self.fields['file_type'].required = False  # Będzie określane automatycznie


class AssetEditForm(forms.ModelForm):
    """Formularz edycji assetu"""
    
    class Meta:
        model = Asset
        fields = ['title', 'description', 'file', 'file_type', 'category', 'tags', 'is_public', 'is_splash_image']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Wprowadź tytuł assetu'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Opis assetu (opcjonalnie)'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*,.pdf,.doc,.docx,.txt,.mp4,.mp3,.wav'
            }),
            'file_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'tags': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'size': 5
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_splash_image': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
        self.fields['tags'].queryset = Tag.objects.all()
        self.fields['file'].required = False  # Plik jest opcjonalny przy edycji


class CategoryForm(forms.ModelForm):
    """Formularz kategorii"""
    
    class Meta:
        model = Category
        fields = ['name', 'description', 'parent']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nazwa kategorii'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Opis kategorii (opcjonalnie)'
            }),
            'parent': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent'].queryset = Category.objects.all()


class TagForm(forms.ModelForm):
    """Formularz tagu"""
    
    class Meta:
        model = Tag
        fields = ['name', 'color']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nazwa tagu'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
        } 