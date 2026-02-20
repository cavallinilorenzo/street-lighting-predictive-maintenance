import io
import random
from datetime import datetime, timedelta

from django.db import connection
from django.shortcuts import render, get_object_or_404
from django.db.models import Count
from django.core.paginator import Paginator
from django.urls import reverse
from django.http import FileResponse

import folium
from folium.plugins import MarkerCluster

# Librerie per il PDF
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from .models import LampioneNuovo, LampioneManutenzione

def index(request):
    top_critici = LampioneNuovo.objects.filter(risk_score__isnull=False).order_by('-risk_score')[:5]
    return render(request, 'core/index.html', {'top_critici': top_critici})


def mappa_lampioni(request):
    start_coords = [41.9028, 12.4964]
    
    m = folium.Map(location=start_coords, zoom_start=13, tiles="cartodbpositron")
    lampioni = LampioneNuovo.objects.exclude(latitudine__isnull=True).exclude(longitudine__isnull=True)[:2500]
    marker_cluster = MarkerCluster().add_to(m)

    for lampione in lampioni:
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
            
            rischio_perc = f"{round(lampione.risk_score * 100)}%"
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
                
                <b style="color: gray;">Rischio Sostituzione (120gg):</b> {rischio_perc}<br>
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
        .annotate(numero_utilizzi=Count('id')) 
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

    tot_critico = LampioneNuovo.objects.filter(risk_score__gt=0.70).count()
    tot_attenzione = LampioneNuovo.objects.filter(risk_score__gte=0.25, risk_score__lte=0.70).count()
    tot_ottimo = LampioneNuovo.objects.filter(risk_score__lt=0.25).count()

    context = {
        'chart_labels': labels,
        'chart_data': data,
        'chart_Intervento': [item['tci_descr'] for item in query_manutenzione],
        'chart_Intervento_data': [item['numero_utilizzi'] for item in query_manutenzione],
        'chart_Intervento_media': [0 for item in query_manutenzione],
        'risk_data': [tot_ottimo, tot_attenzione, tot_critico]
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
    lampione = get_object_or_404(LampioneNuovo, pk=pk)
    
    # --- 1. PRIMO TENTATIVO: Dati specifici per combinazione Altezza / Potenza ---
    sql_specific = """WITH base AS (
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
    
    with connection.cursor() as cursor:
        cursor.execute(sql_specific, [lampione.arm_lmp_potenza_nominale, lampione.arm_altezza])
        rows = cursor.fetchall()
        
    tipo_statistica = "Dato basato su armature con la stessa altezza e potenza."

    # --- 2. FALLBACK PIANO B: Statistica su base cittadina se la prima fallisce ---
    if not rows:
        sql_fallback = """WITH base AS (
          SELECT
            COALESCE(NULLIF(TRIM(tcs_descr), ''), 'Senza categoria') AS tcs_descr
          FROM core_lampionemanutenzione
          WHERE tcs_descr IS NOT NULL
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
        with connection.cursor() as cursor:
            cursor.execute(sql_fallback)
            rows = cursor.fetchall()
        tipo_statistica = "Dati specifici assenti. Media calcolata sull'intera città."

    eta_anni = 0
    if lampione.arm_data_ini:
        try:
            eta_giorni = (datetime.now().date() - lampione.arm_data_ini).days
            eta_anni = eta_giorni // 365
        except TypeError:
            data_ini_parsed = datetime.strptime(str(lampione.arm_data_ini), '%Y-%m-%d').date()
            eta_giorni = (datetime.now().date() - data_ini_parsed).days
            eta_anni = eta_giorni // 365

    if getattr(lampione, 'risk_score', None) is not None:
        giorni_rimanenti = getattr(lampione, 'traQuantoSiRompe', "N/D")
        
        if lampione.risk_score > 0.70:
            stato = "CRITICO"
            colore_stato = "#ef4444" 
            if eta_anni > 5:
                motivazione = f"Forte usura temporale: l'asset è in funzione da oltre {eta_anni} anni, superando la vita utile media stimata."
            elif lampione.arm_lmp_potenza_nominale and lampione.arm_lmp_potenza_nominale > 70:
                motivazione = f"Stress termico/elettrico: l'elevata potenza ({lampione.arm_lmp_potenza_nominale}W) ha storicamente un alto tasso di guasto per questo modello."
            else:
                motivazione = "Il modello ha riscontrato un'alta incidenza di guasti storici per questa specifica combinazione di hardware."
                
        elif lampione.risk_score >= 0.25:
            stato = "ATTENZIONE"
            colore_stato = "#f59e0b"
            if eta_anni > 3:
                motivazione = f"L'asset è in servizio da circa {eta_anni} anni. Si consiglia un monitoraggio per normale decadimento fisiologico."
            else:
                motivazione = "Rilevata una vulnerabilità statistica media per questa classe di armature, indipendente dall'età."
                
        else:
            stato = "OTTIMO"
            colore_stato = "#10b981"
            if eta_anni < 2:
                motivazione = "Installazione recente. Bassissima probabilità di usura fisica o guasti a breve termine."
            else:
                motivazione = "L'hardware si sta dimostrando estremamente affidabile nel tempo rispetto alla media dell'impianto."
    else:
        giorni_rimanenti = "N/D"
        stato = "SCONOSCIUTO"
        colore_stato = "#6c757d"
        motivazione = "In attesa della prima elaborazione dati da parte dell'Intelligenza Artificiale."
            
    messaggio = "Previsione basata sull'intelligenza artificiale."
    
    try:
        data_rottura = datetime.now().date() + timedelta(days=int(giorni_rimanenti))
    except (ValueError, TypeError):
        data_rottura = "N/D"

    # Mappa Folium 100%
    if lampione.latitudine and lampione.longitudine:
        m = folium.Map(location=[lampione.latitudine, lampione.longitudine], zoom_start=19, tiles="cartodbpositron", width='100%', height='100%')
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
        'tipo_statistica': tipo_statistica,
        'ai_data': {
            'giorni': giorni_rimanenti,
            'data_prevista': data_rottura,
            'stato': stato,
            'colore': colore_stato,
            'messaggio': messaggio,
            'motivazione': motivazione
        },
        "nGuasti": len(rows)
    }
        
    return render(request, 'core/lampione_asset.html', context)


def dettaglio_rischio(request, livello):
    sort_by = request.GET.get('sort', 'risk_score')
    direction = request.GET.get('direction', 'desc')

    ordering = sort_by if direction == 'asc' else '-' + sort_by

    valid_fields = ['arm_id', 'risk_score', 'arm_altezza', 'risk_score_date', 'traQuantoSiRompe']
    if sort_by not in valid_fields:
        ordering = '-risk_score'

    if livello == 'critico':
        qs = LampioneNuovo.objects.filter(risk_score__gt=0.70)
        titolo = "Rischio Critico (> 70%)"
    elif livello == 'attenzione':
        qs = LampioneNuovo.objects.filter(risk_score__gte=0.25, risk_score__lte=0.70)
        titolo = "In Osservazione (25% - 70%)"
    else:
        qs = LampioneNuovo.objects.filter(risk_score__lt=0.25)
        titolo = "Stato Ottimo (< 25%)"

    lista_completa = qs.order_by(ordering)

    paginator = Paginator(lista_completa, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'motivo': titolo,
        'lampioni': page_obj,
        'current_sort': sort_by,
        'current_direction': direction,
        'is_risk_view': True,
        'livello': livello
    }
    return render(request, 'core/dettaglio.html', context)


def scarica_pdf_asset(request, pk):
    lampione = get_object_or_404(LampioneNuovo, pk=pk)
    
    eta_anni = 0
    if lampione.arm_data_ini:
        try:
            eta_giorni = (datetime.now().date() - lampione.arm_data_ini).days
            eta_anni = eta_giorni // 365
        except TypeError:
            data_ini_parsed = datetime.strptime(str(lampione.arm_data_ini), '%Y-%m-%d').date()
            eta_giorni = (datetime.now().date() - data_ini_parsed).days
            eta_anni = eta_giorni // 365

    motivazione = "In attesa della prima elaborazione dati da parte dell'Intelligenza Artificiale."
    if getattr(lampione, 'risk_score', None) is not None:
        if lampione.risk_score > 0.70:
            if eta_anni > 5:
                motivazione = f"Forte usura temporale: l'asset è in funzione da oltre {eta_anni} anni, superando la vita utile media stimata."
            elif lampione.arm_lmp_potenza_nominale and lampione.arm_lmp_potenza_nominale > 70:
                motivazione = f"Stress termico/elettrico: l'elevata potenza ({lampione.arm_lmp_potenza_nominale}W) ha storicamente un alto tasso di guasto per questo modello."
            else:
                motivazione = "Il modello ha riscontrato un'alta incidenza di guasti storici per questa specifica combinazione di hardware."
        elif lampione.risk_score >= 0.25:
            if eta_anni > 3:
                motivazione = f"L'asset è in servizio da circa {eta_anni} anni. Si consiglia un monitoraggio per normale decadimento fisiologico."
            else:
                motivazione = "Rilevata una vulnerabilità statistica media per questa classe di armature, indipendente dall'età."
        else:
            if eta_anni < 2:
                motivazione = "Installazione recente. Bassissima probabilità di usura fisica o guasti a breve termine."
            else:
                motivazione = "L'hardware si sta dimostrando estremamente affidabile nel tempo rispetto alla media dell'impianto."

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name='TitleStyle', parent=styles['Heading1'],
        textColor=colors.HexColor('#0f172a'), spaceAfter=20
    )
    subtitle_style = ParagraphStyle(
        name='SubTitle', parent=styles['Heading2'],
        textColor=colors.HexColor('#00f2ff'), spaceAfter=10
    )
    testo_normale = styles['Normal']
    
    elements.append(Paragraph(f"Report Tecnico di Manutenzione Predittiva", title_style))
    elements.append(Paragraph(f"<b>ID Asset:</b> #{lampione.arm_id}", testo_normale))
    elements.append(Paragraph(f"<b>Data Estrazione:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", testo_normale))
    elements.append(Spacer(1, 20))
    
    if lampione.latitudine and lampione.longitudine:
        gmaps_url = f"https://www.google.com/maps/search/?api=1&query={lampione.latitudine},{lampione.longitudine}"
        testo_coords = f"Apri in Google Maps ({lampione.latitudine}, {lampione.longitudine})"
    else:
        gmaps_url = None
        testo_coords = "Coordinate non disponibili"

    elements.append(Paragraph("Specifiche Hardware", subtitle_style))
    data_tecnici = [
        ['Altezza Armatura', f"{lampione.arm_altezza} m" if lampione.arm_altezza else "N/D"],
        ['Potenza Nominale', f"{lampione.arm_lmp_potenza_nominale} W" if lampione.arm_lmp_potenza_nominale else "N/D"],
        ['Modello/Tipologia', f"{lampione.tpo_descr}" if lampione.tpo_descr else "N/D"],
        ['Geolocalizzazione', Paragraph(f'<a href="{gmaps_url}" color="blue">{testo_coords}</a>', testo_normale)]
    ]
    t = Table(data_tecnici, colWidths=[150, 300])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#e2e8f0')),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph("Analisi Predittiva (Machine Learning)", subtitle_style))
    risk_perc = f"{round(lampione.risk_score * 100)}%" if lampione.risk_score else "N/D"
    giorni = getattr(lampione, 'traQuantoSiRompe', "N/D")
    
    data_ml = [
        ['Rischio Sostituzione (120gg)', risk_perc],
        ['Giorni Stimati alla Rottura', f"{giorni} gg" if giorni != "N/D" else "N/D"]
    ]
    t2 = Table(data_ml, colWidths=[200, 250])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#00f2ff')),
        ('TEXTCOLOR', (0,0), (0,-1), colors.HexColor('#0f172a')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(t2)
    elements.append(Spacer(1, 15))
    
    elements.append(Paragraph("<b>Logica Decisionale (Explainable AI):</b>", testo_normale))
    elements.append(Spacer(1, 5))
    elements.append(Paragraph(motivazione, testo_normale))
    
    doc.build(elements)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"Report_Asset_{lampione.arm_id}.pdf")

def dettaglio_intervento(request, tipo_intervento):
    sort_by = request.GET.get('sort', 'sgn_data_inserimento')
    direction = request.GET.get('direction', 'desc')

    ordering = sort_by
    if direction == 'desc':
        ordering = '-' + sort_by

    valid_fields = ['arm_id', 'sgn_data_inserimento', 'tci_descr', 'arm_altezza']
    if sort_by not in valid_fields:
        ordering = '-sgn_data_inserimento'

    # Filtriamo per tipo di intervento (tci_descr)
    lista_completa = LampioneManutenzione.objects.filter(
        tci_descr=tipo_intervento
    ).order_by(ordering)

    paginator = Paginator(lista_completa, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'motivo': tipo_intervento,  # Questo sarà il titolo nella pagina dettaglio.html
        'lampioni': page_obj,
        'current_sort': sort_by,
        'current_direction': direction
    }
    return render(request, 'core/dettaglio.html', context)