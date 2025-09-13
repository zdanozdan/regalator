from django import forms
from django.contrib.auth.models import User
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.utils.text import slugify
from .models import UserProfile, ProductCode, Location, LocationImage, Product, Stock


class ProductCodeForm(forms.ModelForm):
    """Formularz dodawania/edycji kodów produktów"""
    
    class Meta:
        model = ProductCode
        fields = ['code', 'code_type', 'description']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Wprowadź kod kreskowy lub QR',
                'required': True
            }),
            'code_type': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Krótki opis kodu'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)
        
        if self.product:
            self.fields['code'].widget.attrs['data-product-id'] = self.product.id
    
    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code:
            # Check if code already exists for this product
            if self.product and ProductCode.objects.filter(
                product=self.product, 
                code=code
            ).exclude(pk=self.instance.pk if self.instance else None).exists():
                raise forms.ValidationError('Ten kod już istnieje dla tego produktu.')
        return code


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


class LocationEditForm(forms.ModelForm):
    """Formularz edycji lokalizacji"""
    
    class Meta:
        model = Location
        fields = ['name', 'location_type', 'barcode', 'parent', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Wprowadź nazwę lokalizacji',
                'required': True
            }),
            'location_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'barcode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Wprowadź kod kreskowy',
                'required': True
            }),
            'parent': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Wprowadź opis lokalizacji'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.location = kwargs.pop('location', None)
        super().__init__(*args, **kwargs)
        
        # Customize parent field choices
        if self.location:
            # Exclude current location and its children from parent choices
            available_parents = Location.objects.filter(is_active=True).exclude(id=self.location.id)
            self.fields['parent'].choices = [('', 'Brak')] + [
                (loc.id, f"{loc.barcode} - {loc.name}") for loc in available_parents
            ]
    
    
    def clean_barcode(self):
        barcode = self.cleaned_data.get('barcode')
        if barcode:
            # Check if barcode already exists (excluding current instance)
            if self.location and Location.objects.filter(
                barcode=barcode
            ).exclude(id=self.location.id).exists():
                raise forms.ValidationError('Ten kod kreskowy już istnieje.')
        return barcode 


class LocationImageForm(forms.ModelForm):
    """Formularz dodawania i edycji zdjęć lokalizacji"""
    
    class Meta:
        model = LocationImage
        fields = ['image', 'description', 'is_primary']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            #'title': forms.TextInput(attrs={
            #    'class': 'form-control',
            #    'placeholder': 'Wprowadź tytuł zdjęcia',
            #    'maxlength': 200
            #}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Wprowadź opis zdjęcia'
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            #'order': forms.NumberInput(attrs={
            #    'class': 'form-control',
            #    'min': 0,
            #    'placeholder': 'Kolejność wyświetlania'
            #}),
        }
    
    def __init__(self, *args, **kwargs):
        self.location = kwargs.pop('location', None)
        self.is_edit = kwargs.pop('is_edit', False)
        super().__init__(*args, **kwargs)
        
        if self.is_edit:
            # In edit mode, only allow updating description and primary fields
            self.fields['image'].required = False
            self.fields['image'].widget.attrs['disabled'] = True
            self.fields['image'].help_text = 'Zdjęcie nie może być zmienione w trybie edycji'
        else:
            # For new photos, make image field required
            self.fields['image'].required = True
            self.fields['image'].widget.attrs['required'] = True
            self.fields['image'].help_text = 'Obsługiwane formaty: JPG, PNG, GIF (max 5MB)'
        
        # Add labels
        self.fields['description'].label = 'Opis'
        self.fields['is_primary'].label = 'Zdjęcie główne'
            
    def clean_image(self):
        image = self.cleaned_data.get('image')
        
        # In edit mode, ignore any image data and return None
        if self.is_edit:
            return None
            
        if image:
            # Check file size (5MB limit)
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError('Rozmiar pliku nie może przekraczać 5MB.')
            
            # Check file type
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
            if image.content_type not in allowed_types:
                raise forms.ValidationError('Obsługiwane są tylko pliki JPG, PNG i GIF.')
        
        return image
    
    def clean_is_primary(self):
        is_primary = self.cleaned_data.get('is_primary')
        if is_primary and self.location:
            # If this photo is being set as primary, we'll handle the logic in save()
            pass
        return is_primary
    
    def save(self, commit=True):
        photo = super().save(commit=False)
        
        if self.is_edit:
            # In edit mode, only update description and primary fields
            # Don't modify the image field
            if 'image' in self.fields:
                # Remove image from cleaned_data to prevent it from being saved
                if hasattr(self, 'cleaned_data'):
                    self.cleaned_data.pop('image', None)
        
        if self.location:
            photo.location = self.location
            
            # If this photo is being set as primary, unset others
            if photo.is_primary:
                LocationImage.objects.filter(
                    location=self.location, 
                    is_primary=True
                ).exclude(id=photo.id if photo.id else None).update(is_primary=False)
        
        if commit:
            photo.save()
        
        return photo 


class ProductColorSizeForm(forms.ModelForm):
    """Formularz dodawania rozmiaru i koloru produktu"""
    size = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Wprowadź rozmiar',
            'required': True,
        }),
        label='Rozmiar'
    )
    color = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Wprowadź kolor',
            'required': True,
        }),
        label='Kolor'
    )


    class Meta:
        model = Product
        fields = []

    def __init__(self, *args, **kwargs):
        self.parent_product = kwargs.pop('parent', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        size = cleaned.get('size')
        color = cleaned.get('color')

        if not self.parent_product:
            raise forms.ValidationError('Brak produktu nadrzędnego.')

        if size and color:
            # Sprawdź duplikaty wśród dzieci tego produktu po JSONField oraz generowanym kodzie
            proposed_code = self._build_code(self.parent_product.code, size, color)

            duplicate_child = Product.objects.filter(
                parent=self.parent_product,
                variants__size=size,
                variants__color=color,
            ).exclude(pk=self.instance.pk if self.instance and self.instance.pk else None).exists()

            duplicate_code = Product.objects.filter(
                code=proposed_code
            ).exclude(pk=self.instance.pk if self.instance and self.instance.pk else None).exists()

            if duplicate_child or duplicate_code:
                raise forms.ValidationError('Wariant o podanym rozmiarze i kolorze już istnieje dla tego produktu.')

        return cleaned

    def save(self, commit=True):
        if not self.parent_product:
            raise forms.ValidationError('Brak produktu nadrzędnego do utworzenia wariantu.')

        size = self.cleaned_data['size']
        color = self.cleaned_data['color']

        # Przygotuj nowy/istniejący obiekt wariantu (to ModelForm na Product bez pól modelu)
        variant: Product = self.instance if self.instance and self.instance.pk else Product()

        # Uzupełnij pola odziedziczone/pochodne
        variant.parent = self.parent_product
        variant.code = self._build_code(self.parent_product.code, size, color)
        variant.name = f"{self.parent_product.name} - {size} - {color}"
        variant.description = self.parent_product.description
        variant.unit = self.parent_product.unit
        variant.variants = {'size': size, 'color': color}

        if commit:
            variant.save()
            # Po zapisie ustaw grupy takie jak w rodzicu
            variant.groups.set(self.parent_product.groups.all())


        return variant

    @staticmethod
    def _build_code(base_code: str, size: str, color: str) -> str:
        size_part = slugify(size)
        color_part = slugify(color)
        # Zachowaj czytelny separator
        return f"{base_code}-{size_part}-{color_part}"


class ProductForm(forms.ModelForm):
    """Formularz edycji produktu"""
    class Meta:
        model = Product
        fields = []

class ProductStockForm(forms.ModelForm):
    """Wiersz stanu magazynowego dla wariantu produktu"""
    class Meta:
        model = Stock
        fields = ['location', 'quantity']
        widgets = {
            'location': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }
        labels = {
            'location': 'Lokalizacja',
            'quantity': 'Ilość',
        }


class BaseProductStockFormSet(BaseInlineFormSet):
    """Walidacja duplikatów lokalizacji w obrębie jednego wariantu"""
    def clean(self):
        super().clean()
        seen_locations = set()
        for form in self.forms:
            if not hasattr(form, 'cleaned_data'):
                continue
            if self.can_delete and form.cleaned_data.get('DELETE'):
                continue
            if form.errors:
                continue
            location = form.cleaned_data.get('location')
            if location:
                if location in seen_locations:
                    form.add_error('location', 'Duplikat lokalizacji w tym wariancie.')
                seen_locations.add(location)


ProductStockInlineFormSet = inlineformset_factory(
    parent_model=Product,
    model=Stock,
    form=ProductStockForm,
    fields=['location', 'quantity'],
    extra=1,
    can_delete=True,
    formset=BaseProductStockFormSet
)