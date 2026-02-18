from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Sum
from .models import LampioneNuovo, LampioneManutenzione
import folium
from folium.plugins import MarkerCluster

def index(request):
    # Questa mancava! Serve solo a mostrare la pagina di benvenuto
    return render(request, 'core/index.html')

def mappa_lampioni(request):
    start_coords = [41.9028, 12.4964]
    m = folium.Map(location=start_coords, zoom_start=12, tiles="cartodbpositron")
    
    lampioni = LampioneNuovo.objects.all()
    marker_cluster = MarkerCluster().add_to(m)

    # Ne carichiamo 2500 per avere un buon compromesso tra velocità e visione
    for lampione in lampioni[:2500]: 
        if lampione.latitudine and lampione.longitudine:
            folium.Marker(
                location=[lampione.latitudine, lampione.longitudine],
                popup=f"ID: {lampione.arm_id}",
                icon=folium.Icon(color="blue", icon="lightbulb-o", prefix="fa")
            ).add_to(marker_cluster)

    m = m._repr_html_()
    return render(request, 'core/mappa.html', {'mappa': m})

def dashboard(request):
    # 1. Ottieni tutti i dati raggruppati
    query = (
        LampioneManutenzione.objects
        .values('tcs_descr')
        .annotate(totale=Count('id'))
        .order_by('-totale')
        .exclude(tcs_descr__isnull=True)
    )

    # 2. Logica "Top 10 + Altro"
    TOP_N = 10
    labels = []
    data = []
    
    # Prendiamo i primi 10
    for item in query[:TOP_N]:
        labels.append(item['tcs_descr'])
        data.append(item['totale'])
    
    # Calcoliamo la somma di tutti gli altri (dal 11esimo in poi)
    altri_count = 0
    for item in query[TOP_N:]:
        altri_count += item['totale']
    
    if altri_count > 0:
        labels.append('Altro (Guasti minori)')
        data.append(altri_count)

    context = {
        'chart_labels': labels,
        'chart_data': data,
    }
    return render(request, 'core/dashboard.html', context)

def dettaglio_guasto(request, motivo_guasto):
    # 3. Questa vista viene chiamata quando clicchi sul grafico
    # Recupera tutti i lampioni con QUEL motivo specifico
    lampioni = LampioneManutenzione.objects.filter(tcs_descr=motivo_guasto)
    
    context = {
        'motivo': motivo_guasto,
        'lampioni': lampioni
    }
    return render(request, 'core/dettaglio.html', context)

def dettaglio_lampione(request, arm_id):
    # 1. Recupera il lampione (o da errore 404 se non esiste)
    lampione = get_object_or_404(LampioneManutenzione, arm_id=arm_id)
    
    # 2. Crea la mappa centrata sulle coordinate del lampione
    # Nota: Assumo che nel DB i campi siano float. Se sono nulli, metti un default.
    lat = lampione.latitudine if lampione.latitudine else 44.647128 # Esempio (Modena)
    lon = lampione.longitudine if lampione.longitudine else 10.925227
    
    m = folium.Map(location=[lat, lon], zoom_start=19, control_scale=True)

    # Aggiungi il marker
    folium.Marker(
        [lat, lon],
        tooltip=f"Lampione {lampione.arm_id}",
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(m)

    # 3. Renderizza
    context = {
        'lampione': lampione,
        'mappa': m._repr_html_() # Trasforma la mappa in HTML
    }
    return render(request, 'core/lampione_singolo.html', context)