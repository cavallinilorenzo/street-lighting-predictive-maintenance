from django.contrib import admin
from django.urls import path
from core.views import index, dashboard, dettaglio_guasto, dettaglio_lampione, mappa_lampioni, dettaglio_asset

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('mappa/', mappa_lampioni, name='mappa_lampioni'),
    path('statistiche/', dashboard, name='statistiche'), # Assicurati che questo sia prima di dettaglio-guasto
    path('dettaglio-guasto/<path:motivo_guasto>/', dettaglio_guasto, name='dettaglio_guasto'),
    path('lampione/<int:pk>/', dettaglio_lampione, name='dettaglio_lampione'),
    path('asset/<int:pk>/', dettaglio_asset, name='dettaglio_asset'),
]