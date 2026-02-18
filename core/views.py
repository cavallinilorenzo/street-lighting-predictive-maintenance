from django.shortcuts import render
from .models import LampioneNuovo
import folium
from folium.plugins import MarkerCluster

# Questa è la tua Home Page
def home(request):
    return render(request, 'core/index.html') # Carica il nuovo index.html

# Questa è la pagina con la Mappa
def mappa_lampioni(request):
    start_coords = [41.9028, 12.4964]
    m = folium.Map(location=start_coords, zoom_start=12, tiles="cartodbpositron")
    
    lampioni = LampioneNuovo.objects.all()
    marker_cluster = MarkerCluster().add_to(m)

    # Ne carichiamo 1000 per avere un buon compromesso tra velocità e visione
    for lampione in lampioni[:2500]: 
        if lampione.latitudine and lampione.longitudine:
            folium.Marker(
                location=[lampione.latitudine, lampione.longitudine],
                popup=f"ID: {lampione.arm_id}",
                icon=folium.Icon(color="blue", icon="lightbulb-o", prefix="fa")
            ).add_to(marker_cluster)

    m = m._repr_html_()
    return render(request, 'core/mappa.html', {'mappa': m})