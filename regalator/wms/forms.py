from django import forms
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileForm(forms.ModelForm):
    """Formularz edycji profilu użytkownika"""
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Imię'
        }),
        label="Imię"
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nazwisko'
        }),
        label="Nazwisko"
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@example.com'
        }),
        label="Email"
    )
    
    class Meta:
        model = UserProfile
        fields = ['avatar', 'phone', 'department', 'position']
        widgets = {
            'avatar': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+48 123 456 789'
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Magazyn'
            }),
            'position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Kompletator'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            # Zaktualizuj dane użytkownika
            user = profile.user
            user.first_name = self.cleaned_data.get('first_name', '')
            user.last_name = self.cleaned_data.get('last_name', '')
            user.email = self.cleaned_data.get('email', '')
            user.save()
            profile.save()
        return profile 