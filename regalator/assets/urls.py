from django.urls import path
from . import views

app_name = 'assets'

urlpatterns = [
    # Lista assetów
    path('', views.asset_list, name='asset_list'),
    
    # Upload (musi być przed <slug:slug>/)
    path('upload/', views.asset_upload, name='asset_upload'),
    
    # Kategorie
    path('categories/', views.category_list, name='category_list'),
    path('categories/<int:category_id>/', views.category_detail, name='category_detail'),
    
    # Tagi
    path('tags/<int:tag_id>/', views.tag_detail, name='tag_detail'),
    
    # Szczegóły assetu (używając slug) - musi być na końcu
    path('<slug:slug>/', views.asset_detail, name='asset_detail'),
    path('<slug:slug>/edit/', views.asset_edit, name='asset_edit'),
    path('<slug:slug>/delete/', views.asset_delete, name='asset_delete'),
    path('<slug:slug>/download/', views.asset_download, name='asset_download'),
] 