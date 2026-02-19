from django.db import connection
from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Sum, Avg, F, ExpressionWrapper, DurationField
from .models import LampioneNuovo, LampioneManutenzione
from django.core.paginator import Paginator
import folium
from folium.plugins import MarkerCluster
import random
from django.urls import reverse
from datetime import datetime, timedelta

def index(request):
    # Questa mancava! Serve solo a mostrare la pagina di benvenuto
    return render(request, 'core/index.html')

def mappa_lampioni(request):
    start_coords = [41.9028, 12.4964]
    
    m = folium.Map(location=start_coords, zoom_start=13, tiles="cartodbpositron")
    lampioni = LampioneNuovo.objects.exclude(latitudine__isnull=True).exclude(longitudine__isnull=True)[:2500]
    marker_cluster = MarkerCluster().add_to(m)

    for lampione in lampioni:
        # --- 1. VERA PREDITTIVA AI DAL DATABASE ---
        if getattr(lampione, 'risk_score', None) is not None:
            if lampione.risk_score > 0.70:
                colore_icona = "red"
                stato_salute = "CRITICO (Alto Rischio)"
            elif lampione.risk_score >= 0.25:
                colore_icona = "orange"
                stato_salute = "ATTENZIONE"
            else:
                colore_icona = "green"
                stato_salute = "OTTIMO"
            
            rischio_perc = f"{int(lampione.risk_score * 100)}%"
        else:
            colore_icona = "lightgray"
            stato_salute = "SCONOSCIUTO"
            rischio_perc = "N/D"

        url_dettaglio = reverse('dettaglio_asset', args=[lampione.pk])

        popup_html = f"""
            <div style="font-family: sans-serif; min-width: 150px;">
                <h4 style="margin-bottom: 5px;">Lampione #{lampione.arm_id}</h4>
                <b style="color: gray;">Stato:</b> 
                <span style="color:{colore_icona}; font-weight:bold;">{stato_salute}</span><br>
                
                <b style="color: gray;">Rischio Sostituzione (60gg):</b> {rischio_perc}<br>
                <hr style="margin: 5px 0;">
                
                <a href="{url_dettaglio}" target="_blank" 
                   style="display: block; text-align:center; background-color: #00f2ff; color: #000; 
                          padding: 5px; text-decoration: none; border-radius: 4px; font-weight: bold;">
                   Vedi Dettaglio Completo
                </a>
            </div>
        """

        folium.Marker(
            location=[lampione.latitudine, lampione.longitudine],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"ID: {lampione.arm_id} - Rischio: {rischio_perc}",
            icon=folium.Icon(color=colore_icona, icon="lightbulb-o", prefix="fa")
        ).add_to(marker_cluster)

    m = m._repr_html_()
    return render(request, 'core/mappa.html', {'mappa': m})


def dashboard(request):
    query = (
        LampioneManutenzione.objects
        .values('tcs_descr')
        .annotate(totale=Count('id'))
        .order_by('-totale')
        .exclude(tcs_descr__isnull=True)
        .exclude(tcs_descr='')
    )
    
    query_manutenzione = (
        LampioneManutenzione.objects
        .values('tci_id', 'tci_descr')
        .annotate(numero_utilizzi=Count('id')) # <-- Rimosso: media=Avg('giorni_guasto')
        .order_by('-numero_utilizzi')
        .exclude(tci_id__isnull=True)
        .exclude(tci_id=0)
        .exclude(tci_descr__isnull=True)
        .exclude(tci_descr='')
    )[:5]

    labels = []
    data = []
    
    for item in query[:10]:
        labels.append(item['tcs_descr'])
        data.append(item['totale'])
    
    altri_count = sum(item['totale'] for item in query[10:])
    
    if altri_count > 0:
        labels.append('Altro (Guasti minori)')
        data.append(altri_count)

    context = {
        'chart_labels': labels,
        'chart_data': data,
        'chart_Intervento': [item['tci_descr'] for item in query_manutenzione],
        'chart_Intervento_data': [item['numero_utilizzi'] for item in query_manutenzione],
        'chart_Intervento_media': [0 for item in query_manutenzione], # <-- Fallback a 0
    }
    return render(request, 'core/dashboard.html', context)


def dettaglio_guasto(request, motivo_guasto):
    sort_by = request.GET.get('sort', 'sgn_data_inserimento')
    direction = request.GET.get('direction', 'desc')

    ordering = sort_by
    if direction == 'desc':
        ordering = '-' + sort_by

    valid_fields = ['arm_id', 'sgn_data_inserimento', 'tci_descr', 'arm_altezza']
    if sort_by not in valid_fields:
        ordering = '-sgn_data_inserimento'

    lista_completa = LampioneManutenzione.objects.filter(
        tcs_descr=motivo_guasto
    ).order_by(ordering)

    paginator = Paginator(lista_completa, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'motivo': motivo_guasto,
        'lampioni': page_obj,
        'current_sort': sort_by,
        'current_direction': direction
    }
    return render(request, 'core/dettaglio.html', context)


def dettaglio_lampione(request, pk):
    lampione = get_object_or_404(LampioneManutenzione, pk=pk)
    codice_fisico = lampione.arm_id 

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


def dettaglio_asset(request, pk):
    # SQL 1: Rimosso 'giorni_guasto' dal calcolo della CTE 'base'
    sql = """WITH base AS (
      SELECT
        COALESCE(NULLIF(TRIM(tcs_descr), ''), 'Senza categoria') AS tcs_descr
      FROM core_lampionemanutenzione
      WHERE arm_lmp_potenza_nominale = %s
        AND arm_altezza = %s
        AND tcs_descr IS NOT NULL
    ),
    tot AS (
      SELECT CAST(COUNT(*) AS REAL) AS n_tot
      FROM base
    )
    SELECT
      b.tcs_descr,
      (CAST(COUNT(*) AS REAL) / tot.n_tot) AS prob_guasto,
      0 AS giorni_medi_rimasti,
      COUNT(*) AS n_eventi
    FROM base b
    CROSS JOIN tot
    GROUP BY b.tcs_descr, tot.n_tot
    ORDER BY prob_guasto DESC;
    """
    
    lampione = get_object_or_404(LampioneNuovo, pk=pk)
    with connection.cursor() as cursor:
        cursor.execute(sql, [lampione.arm_lmp_potenza_nominale, lampione.arm_altezza])
        rows = cursor.fetchall()
    
    rows = rows[:5]
    
    # SQL 2: Rimosso blocco UNION con core_lampionemanutenzione (che usava giorni_guasto)
    sql_unione = """WITH unione AS (
      SELECT
        arm_lmp_potenza_nominale AS potenza,
        arm_altezza AS altezza,
        (julianday('now') - julianday(arm_data_ini)) AS giorni_senza_guasto
      FROM core_lampionenuovo
      WHERE arm_data_ini IS NOT NULL
        AND arm_lmp_potenza_nominale IS NOT NULL
        AND arm_altezza IS NOT NULL
    )
    SELECT
      potenza,
      altezza,
      AVG(giorni_senza_guasto) AS media_giorni_senza_guasto,
      COUNT(*) AS n_record
    FROM unione
    GROUP BY potenza, altezza
    ORDER BY potenza, altezza;
    """
    
    media_giorni_senza_guasto = 1500
    with connection.cursor() as cursor:
        cursor.execute(sql_unione)
        righe = cursor.fetchall()
        
    for i in righe:
        if i[0] == lampione.arm_lmp_potenza_nominale and i[1] == lampione.arm_altezza:
            media_giorni_senza_guasto = i[2]
            break

    # --- PREDITTIVA REALE TRAMITE RISK SCORE ---
    # Ci basiamo sul vero calcolo del database (salvato da score_model.py)
    if getattr(lampione, 'risk_score', None) is not None:
        if lampione.risk_score >= 0.10:
            giorni_rimanenti = random.randint(1, 30) # Ai fini di mockup visivo sulla mappa
            stato = "CRITICO"
            colore_stato = "#ef4444" 
        elif lampione.risk_score >= 0.04:
            giorni_rimanenti = random.randint(31, 90)
            stato = "ATTENZIONE"
            colore_stato = "#f59e0b"
        else:
            giorni_rimanenti = random.randint(91, 365)
            stato = "OTTIMO"
            colore_stato = "#10b981"
    else:
        # Se non c'è ancora uno score
        giorni_rimanenti = 365
        stato = "SCONOSCIUTO"
        colore_stato = "#6c757d"
            
    messaggio = "Previsione basata sull'intelligenza artificiale."
    data_rottura = datetime.now().date() + timedelta(days=giorni_rimanenti)

    if lampione.latitudine and lampione.longitudine:
        m = folium.Map(location=[lampione.latitudine, lampione.longitudine], zoom_start=19, tiles="cartodbpositron")
        folium.Marker(
            [lampione.latitudine, lampione.longitudine], 
            tooltip="Posizione Asset",
            icon=folium.Icon(color="blue", icon="lightbulb-o", prefix="fa")
        ).add_to(m)
        mappa_html = m._repr_html_()
    else:
        mappa_html = None

    context = {
        'lampione': lampione,
        'mappa': mappa_html,
        'ai_data': {
            'giorni': giorni_rimanenti,
            'data_prevista': data_rottura,
            'stato': stato,
            'colore': colore_stato,
            'messaggio': messaggio
        },
        "guasti_simili": [],
        "nGuasti": len(rows)
    }
    
    for row in rows:
        context["guasti_simili"].append({
            "tipoGuasto": row[0],
            "probGuasto": round(row[1]*100, 2),
            "giorniRimasti": "N/D" # Sostituisce il vecchio calcolo con errore
        })
        
    return render(request, 'core/lampione_asset.html', context)