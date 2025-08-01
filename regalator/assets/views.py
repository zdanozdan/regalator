from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Asset, Category, Tag
from .forms import AssetUploadForm, AssetEditForm
import os


@login_required
def asset_list(request):
    """Lista wszystkich assetów"""
    assets = Asset.objects.all()
    
    # Filtrowanie
    category_id = request.GET.get('category')
    if category_id:
        assets = assets.filter(category_id=category_id)
    
    file_type = request.GET.get('type')
    if file_type:
        assets = assets.filter(file_type=file_type)
    
    search_query = request.GET.get('search')
    if search_query:
        assets = assets.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(tags__name__icontains=search_query)
        ).distinct()
    
    # Sortowanie
    sort_by = request.GET.get('sort', '-uploaded_at')
    assets = assets.order_by(sort_by)
    
    # Paginacja
    paginator = Paginator(assets, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Kontekst
    categories = Category.objects.all()
    tags = Tag.objects.all()
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'tags': tags,
        'search_query': search_query,
        'category_filter': category_id,
        'type_filter': file_type,
        'sort_by': sort_by,
        'asset_types': Asset.ASSET_TYPES,
    }
    
    return render(request, 'assets/asset_list.html', context)


@login_required
def asset_detail(request, slug):
    """Szczegóły assetu"""
    asset = get_object_or_404(Asset, slug=slug)
    
    # Podobne assety
    similar_assets = Asset.objects.filter(
        Q(category=asset.category) | Q(tags__in=asset.tags.all())
    ).exclude(id=asset.id).distinct()[:6]
    
    context = {
        'asset': asset,
        'similar_assets': similar_assets,
    }
    
    return render(request, 'assets/asset_detail.html', context)


@login_required
def asset_upload(request):
    """Upload nowego assetu"""
    if request.method == 'POST':
        form = AssetUploadForm(request.POST, request.FILES)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.uploaded_by = request.user
            
            # Automatyczne określenie typu pliku
            if not asset.file_type:
                ext = os.path.splitext(asset.file.name)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                    asset.file_type = 'image'
                elif ext == '.pdf':
                    asset.file_type = 'pdf'
                elif ext in ['.doc', '.docx', '.txt', '.rtf']:
                    asset.file_type = 'document'
                elif ext in ['.mp4', '.avi', '.mov', '.wmv']:
                    asset.file_type = 'video'
                elif ext in ['.mp3', '.wav', '.ogg']:
                    asset.file_type = 'audio'
                else:
                    asset.file_type = 'other'
            
            asset.save()
            form.save_m2m()  # Zapisz many-to-many relationships
            
            messages.success(request, f'Asset "{asset.title}" został dodany pomyślnie.')
            return redirect('assets:asset_detail', slug=asset.slug)
    else:
        form = AssetUploadForm()
    
    context = {
        'form': form,
        'categories': Category.objects.all(),
        'tags': Tag.objects.all(),
    }
    
    return render(request, 'assets/asset_upload.html', context)


@login_required
def asset_edit(request, slug):
    """Edycja assetu"""
    asset = get_object_or_404(Asset, slug=slug)
    
    # Sprawdź uprawnienia
    if asset.uploaded_by != request.user and not request.user.is_staff:
        messages.error(request, 'Nie masz uprawnień do edycji tego assetu.')
        return redirect('assets:asset_detail', slug=asset.slug)
    
    if request.method == 'POST':
        form = AssetEditForm(request.POST, request.FILES, instance=asset)
        if form.is_valid():
            # Jeśli tytuł się zmienił, wygeneruj nowy slug
            if form.cleaned_data['title'] != asset.title:
                asset.slug = asset.generate_unique_slug()
            
            form.save()
            messages.success(request, f'Asset "{asset.title}" został zaktualizowany.')
            return redirect('assets:asset_detail', slug=asset.slug)
    else:
        form = AssetEditForm(instance=asset)
    
    context = {
        'form': form,
        'asset': asset,
        'categories': Category.objects.all(),
        'tags': Tag.objects.all(),
    }
    
    return render(request, 'assets/asset_edit.html', context)


@login_required
def asset_delete(request, slug):
    """Usuwanie assetu"""
    asset = get_object_or_404(Asset, slug=slug)
    
    # Sprawdź uprawnienia
    if asset.uploaded_by != request.user and not request.user.is_staff:
        messages.error(request, 'Nie masz uprawnień do usunięcia tego assetu.')
        return redirect('assets:asset_detail', slug=asset.slug)
    
    if request.method == 'POST':
        title = asset.title
        asset.delete()
        messages.success(request, f'Asset "{title}" został usunięty.')
        return redirect('assets:asset_list')
    
    context = {
        'asset': asset,
    }
    
    return render(request, 'assets/asset_delete.html', context)


@login_required
def category_list(request):
    """Lista kategorii"""
    categories = Category.objects.all()
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'assets/category_list.html', context)


@login_required
def category_detail(request, category_id):
    """Szczegóły kategorii z assetami"""
    category = get_object_or_404(Category, id=category_id)
    assets = Asset.objects.filter(category=category).order_by('-uploaded_at')
    
    # Paginacja
    paginator = Paginator(assets, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'page_obj': page_obj,
    }
    
    return render(request, 'assets/category_detail.html', context)


@login_required
def tag_detail(request, tag_id):
    """Szczegóły tagu z assetami"""
    tag = get_object_or_404(Tag, id=tag_id)
    assets = Asset.objects.filter(tags=tag).order_by('-uploaded_at')
    
    # Paginacja
    paginator = Paginator(assets, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'tag': tag,
        'page_obj': page_obj,
    }
    
    return render(request, 'assets/tag_detail.html', context)


@login_required
def asset_download(request, slug):
    """Download assetu"""
    asset = get_object_or_404(Asset, slug=slug)
    
    # Sprawdź czy plik istnieje
    if not asset.file:
        messages.error(request, 'Plik nie istnieje.')
        return redirect('assets:asset_detail', slug=asset.slug)
    
    # Tutaj można dodać logikę liczenia downloadów
    return redirect(asset.file.url)
