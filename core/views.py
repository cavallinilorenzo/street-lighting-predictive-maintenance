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
        .exclude(tcs_descr='') # Escludi anche le stringhe vuote
    )

    # DEBUG: Stampa nella console di VS Code (quella nera dove gira il server)
    # per vedere se il database risponde
    print(f"DEBUG: Trovati {query.count()} gruppi di guasti.")

    labels = []
    data = []
    
    # Prendi i primi 10
    for item in query[:10]:
        labels.append(item['tcs_descr'])
        data.append(item['totale'])
    
    # Calcoliamo la somma di tutti gli altri (dal 11esimo in poi)
    altri_count = 0
    for item in query[10:]:
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

def dettaglio_lampione(request, pk):
    # Cerchiamo per la Primary Key (id) univoca di Django
    lampione = get_object_or_404(LampioneManutenzione, pk=pk)
    
    # Ora puoi comunque accedere all'arm_id reale del lampione
    codice_fisico = lampione.arm_id 

    # Mappa e resto del codice rimangono uguali
    lat = lampione.latitudine if lampione.latitudine else 44.647
    lon = lampione.longitudine if lampione.longitudine else 10.925
    m = folium.Map(location=[lat, lon], zoom_start=19)
    folium.Marker([lat, lon], tooltip=f"Lampione {codice_fisico}").add_to(m)

    storico = LampioneManutenzione.objects.filter(arm_id=lampione.arm_id).exclude(pk=pk).order_by('-sgn_data_inserimento')

    return render(request, 'core/lampione_singolo.html', {
        'lampione': lampione,
        'storico': storico,
        'mappa': m._repr_html_()
    })