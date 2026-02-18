from django.contrib import admin
from django.urls import path
from core.views import index, dashboard, dettaglio_guasto, dettaglio_lampione, mappa_lampioni

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Homepage (quella che hai caricato tu)
    path('', index, name='index'), 

    # Statistiche (Grafico a torta)
    path('statistiche/', dashboard, name='statistiche'),

    # Percorso per la Mappa
    path('mappa/', mappa_lampioni, name='mappa_lampioni'), 

    # Lista filtrata (quando clicchi sulla fetta della torta)
    path('dettaglio-guasto/<str:motivo_guasto>/', dettaglio_guasto, name='dettaglio_guasto'),

    # NUOVO: Dettaglio del singolo lampione
    path('lampione/<int:arm_id>/', dettaglio_lampione, name='dettaglio_lampione'),
]