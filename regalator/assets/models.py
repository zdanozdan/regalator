from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
import os


def asset_upload_path(instance, filename):
    """Generuje ścieżkę dla uploadowanych plików"""
    return f'assets/{instance.category.name if instance.category else "uncategorized"}/{filename}'


class Category(models.Model):
    """Kategoria assetów"""
    name = models.CharField(max_length=100, verbose_name="Nazwa")
    description = models.TextField(blank=True, verbose_name="Opis")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Kategoria nadrzędna")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Utworzono")
    
    class Meta:
        verbose_name = "Kategoria"
        verbose_name_plural = "Kategorie"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Tag(models.Model):
    """Tag dla assetów"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Nazwa")
    color = models.CharField(max_length=7, default="#007bff", verbose_name="Kolor")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Utworzono")
    
    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tagi"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Asset(models.Model):
    """Asset (zdjęcie, PDF, etc.)"""
    
    ASSET_TYPES = [
        ('image', 'Obraz'),
        ('pdf', 'PDF'),
        ('document', 'Dokument'),
        ('video', 'Wideo'),
        ('audio', 'Audio'),
        ('other', 'Inne'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Tytuł")
    slug = models.SlugField(max_length=250, unique=True, verbose_name="Slug")
    description = models.TextField(blank=True, verbose_name="Opis")
    file = models.FileField(upload_to=asset_upload_path, verbose_name="Plik")
    file_type = models.CharField(max_length=20, choices=ASSET_TYPES, verbose_name="Typ pliku")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Kategoria")
    tags = models.ManyToManyField(Tag, blank=True, verbose_name="Tagi")
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Dodane przez")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Dodano")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Zaktualizowano")
    is_public = models.BooleanField(default=True, verbose_name="Publiczne")
    is_splash_image = models.BooleanField(default=False, verbose_name="Obraz splash")
    
    class Meta:
        verbose_name = "Asset"
        verbose_name_plural = "Assety"
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        """Automatyczne generowanie sluga jeśli nie istnieje"""
        if not self.slug:
            self.slug = self.generate_unique_slug()
        
        # Jeśli ten asset ma być splash image, odznacz wszystkie inne
        if self.is_splash_image:
            Asset.objects.filter(is_splash_image=True).exclude(id=self.id).update(is_splash_image=False)
        
        super().save(*args, **kwargs)
    
    def generate_unique_slug(self):
        """Generuje unikalny slug na podstawie tytułu"""
        base_slug = slugify(self.title)
        slug = base_slug
        counter = 1
        
        # Sprawdź czy slug już istnieje
        while Asset.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    @property
    def filename(self):
        """Zwraca nazwę pliku"""
        return os.path.basename(self.file.name)
    
    @property
    def file_size(self):
        """Zwraca rozmiar pliku w MB"""
        try:
            size_bytes = self.file.size
            size_mb = size_bytes / (1024 * 1024)
            return f"{size_mb:.2f} MB"
        except:
            return "Nieznany"
    
    @property
    def file_extension(self):
        """Zwraca rozszerzenie pliku"""
        return os.path.splitext(self.filename)[1].lower()
    
    def get_absolute_url(self):
        """Zwraca URL do szczegółów assetu"""
        from django.urls import reverse
        return reverse('assets:asset_detail', args=[self.slug])
    
    @classmethod
    def get_splash_image(cls):
        """Zwraca aktualny splash image"""
        return cls.objects.filter(is_splash_image=True).first()
