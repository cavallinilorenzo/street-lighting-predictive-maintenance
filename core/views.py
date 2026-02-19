from django.db import connection
from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Sum, Count, Avg, F, ExpressionWrapper, DurationField
from .models import LampioneNuovo, LampioneManutenzione
from django.core.paginator import Paginator
from django.shortcuts import render
import folium
from folium.plugins import MarkerCluster
import random
from django.urls import reverse
from datetime import datetime, timedelta

def index(request):
    # Questa mancava! Serve solo a mostrare la pagina di benvenuto
    return render(request, 'core/index.html')

def mappa_lampioni(request):
    # Coordinate centrali (puoi anche calcolarle come media dei punti)
    start_coords = [41.9028, 12.4964]
    
    # Creazione Mappa Base (Dark mode per stile "Cyberpunk" o standard)
    m = folium.Map(location=start_coords, zoom_start=13, tiles="cartodbpositron")
    
    # Ottimizzazione: prendiamo solo i campi che ci servono per non appesantire la query
    lampioni = LampioneNuovo.objects.exclude(latitudine__isnull=True).exclude(longitudine__isnull=True)[:2500]
    
    marker_cluster = MarkerCluster().add_to(m)

    for lampione in lampioni:
        # --- 1. SIMULAZIONE PREDITTIVA (Placeholder) ---
        # Qui in futuro interrogherai il tuo modello AI. 
        # Per ora simuliamo i "giorni rimasti alla rottura".
        giorni_alla_rottura = random.randint(1, 365) 
        
        # --- 2. LOGICA COLORI (SEMAFORO) ---
        if giorni_alla_rottura < 30:
            colore_icona = "red"
            stato_salute = "CRITICO"
        elif giorni_alla_rottura < 90:
            colore_icona = "orange"
            stato_salute = "ATTENZIONE"
        else:
            colore_icona = "green"
            stato_salute = "OTTIMO"

        # --- 3. CREAZIONE LINK AL DETTAGLIO ---
        # Usiamo 'reverse' per costruire l'URL dinamico verso la view 'dettaglio_lampione'
        # Assicurati che nel tuo urls.py il name sia 'dettaglio_lampione'
        url_dettaglio = reverse('dettaglio_asset', args=[lampione.pk])

        # --- 4. POPUP HTML PERSONALIZZATO ---
        # Creiamo una stringa HTML per rendere il popup bello e funzionale
        popup_html = f"""
            <div style="font-family: sans-serif; min-width: 150px;">
                <h4 style="margin-bottom: 5px;">Lampione #{lampione.arm_id}</h4>
                <b style="color: gray;">Stato:</b> 
                <span style="color:{colore_icona}; font-weight:bold;">{stato_salute}</span><br>
                
                <b style="color: gray;">Prev. Rottura:</b> tra {giorni_alla_rottura} gg<br>
                <hr style="margin: 5px 0;">
                
                <a href="{url_dettaglio}" target="_blank" 
                   style="display: block; text-align:center; background-color: #00f2ff; color: #000; 
                          padding: 5px; text-decoration: none; border-radius: 4px; font-weight: bold;">
                   Vedi Dettaglio Completo
                </a>
            </div>
        """

        # Aggiunta Marker
        folium.Marker(
            location=[lampione.latitudine, lampione.longitudine],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"ID: {lampione.arm_id} ({stato_salute})", # Appare al passaggio del mouse
            icon=folium.Icon(color=colore_icona, icon="lightbulb-o", prefix="fa")
        ).add_to(marker_cluster)

    m = m._repr_html_()
    return render(request, 'core/mappa.html', {'mappa': m})

from django.db.models.functions import Lag
from django.db.models.expressions import Window

def dashboard(request):
    # 1. Ottieni tutti i dati raggruppati
    print(LampioneManutenzione.objects.filter(arm_data_ini='2018-01-01'))
    query = (
        LampioneManutenzione.objects
        .values('tcs_descr')
        .annotate(totale=Count('id'))
        .order_by('-totale')
        .exclude(tcs_descr__isnull=True)
        .exclude(tcs_descr='') # Escludi anche le stringhe vuote
    )
    query_manutenzione = (
    LampioneManutenzione.objects
        .values('tci_id', 'tci_descr')
        .annotate(
            numero_utilizzi=Count('id'),
            media=Avg('giorni_guasto'),
        )
        .order_by('-numero_utilizzi')
        .exclude(tci_id__isnull=True)
        .exclude(tci_id=0)
        .exclude(tci_descr__isnull=True)
        .exclude(tci_descr='')
    )

    query_manutenzione=query_manutenzione[:5]
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
        'chart_Intervento': [item['tci_descr'] for item in query_manutenzione],
        'chart_Intervento_data': [item['numero_utilizzi'] for item in query_manutenzione],
        'chart_Intervento_media': [int(item['media']) for item in query_manutenzione],

    }
    #print(query_manutenzione)
    return render(request, 'core/dashboard.html', context)

def dettaglio_guasto(request, motivo_guasto):
    # 1. Recupera i parametri di ordinamento (default: data decrescente)
    sort_by = request.GET.get('sort', 'sgn_data_inserimento')
    direction = request.GET.get('direction', 'desc')

    # 2. Determina il prefisso per l'ordinamento Django ('-' significa discendente)
    ordering = sort_by
    if direction == 'desc':
        ordering = '-' + sort_by

    # 3. Validazione semplice per sicurezza (evita errori se l'utente scrive campi a caso)
    valid_fields = ['arm_id', 'sgn_data_inserimento', 'tci_descr', 'arm_altezza']
    if sort_by not in valid_fields:
        ordering = '-sgn_data_inserimento' # Fallback sicuro

    # 4. Esegui la query con l'ordinamento dinamico
    lista_completa = LampioneManutenzione.objects.filter(
        tcs_descr=motivo_guasto
    ).order_by(ordering)

    # 5. Paginazione (50 per pagina)
    paginator = Paginator(lista_completa, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'motivo': motivo_guasto,
        'lampioni': page_obj,
        # Passiamo i parametri al template per mantenere l'ordinamento quando cambi pagina
        'current_sort': sort_by,
        'current_direction': direction
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

def dettaglio_asset(request, pk):
    from django.db import connection

    sql = """WITH base AS (
  SELECT
    COALESCE(NULLIF(TRIM(tcs_descr), ''), 'Senza categoria') AS tcs_descr,
    giorni_guasto
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
  CAST(AVG(b.giorni_guasto) AS REAL) AS giorni_medi_rimasti,
  COUNT(*) AS n_eventi
FROM base b
CROSS JOIN tot
GROUP BY b.tcs_descr, tot.n_tot
ORDER BY prob_guasto DESC;

    """
    
    # Recuperiamo l'oggetto dal modello dell'anagrafica (NON manutenzione)
    lampione = get_object_or_404(LampioneNuovo, pk=pk)
    with connection.cursor() as cursor:
        cursor.execute(sql, [lampione.arm_lmp_potenza_nominale, lampione.arm_altezza])  # <- lista/tuple, non dict
        rows = cursor.fetchall()
    
    rows=rows[:5]
    #(tcs_descr, prob_guasto, giorni_medi_rimasti, n_eventi)
    sql="""WITH unione AS (
  -- LampioneNuovo: giorni senza guasto = oggi - data installazione
  SELECT
    arm_lmp_potenza_nominale AS potenza,
    arm_altezza AS altezza,
    (julianday('now') - julianday(arm_data_ini)) AS giorni_senza_guasto
  FROM core_lampionenuovo
  WHERE arm_data_ini IS NOT NULL
    AND arm_lmp_potenza_nominale IS NOT NULL
    AND arm_altezza IS NOT NULL

  UNION ALL

  -- LampioneManutenzione: giorni_senza_guasto = campo giorni_guasto
  SELECT
    arm_lmp_potenza_nominale AS potenza,
    arm_altezza AS altezza,
    CAST(giorni_guasto AS REAL) AS giorni_senza_guasto
  FROM core_lampionemanutenzione
  WHERE giorni_guasto IS NOT NULL
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
    media_giorni_senza_guasto=1500
    with connection.cursor() as cursor:
        cursor.execute(sql)
        righe = cursor.fetchall()
    for i in righe:
        if(i[0]==lampione.arm_lmp_potenza_nominale and i[1]==lampione.arm_altezza):
            print("Trovato record simile: ",i)
            media_giorni_senza_guasto=i[2]
            break
    print(media_giorni_senza_guasto)
    #print(rows)
    print("probabilità: ")
    sumPro=0
    sumGiorni=0
    for row in rows:
        sumPro+=row[1]
        sumGiorni+=row[2]
    
    print(lampione.arm_data_ini,sumGiorni)

    # --- SIMULAZIONE PREDITTIVA (AI Placeholder) ---
    # Generiamo dati coerenti con quelli della mappa
    # In produzione, qui chiameresti il tuo modello ML
    lenght=len(rows)
    if lenght==0:
        giorni_rimanenti = 365  # Se non ci sono dati, assumiamo un asset nuovo di zecca
    else:
        giorni_rimanenti = ((lampione.arm_data_ini + timedelta(days=int(media_giorni_senza_guasto))) - datetime.now().date()).days
    data_rottura = (lampione.arm_data_ini + timedelta(days=int(media_giorni_senza_guasto)))
    print(giorni_rimanenti)
    #giorni_rimanenti = int(sumGiorni / len(rows))
    
    
    stato = "OTTIMO"
    colore_stato = "#00ff9d" # Verde
    messaggio = "Nessun intervento richiesto a breve."
    
    if giorni_rimanenti < 30:
        stato = "CRITICO"
        colore_stato = "#ff0055" # Rosso
        messaggio = "Rischio guasto imminente! Pianificare sostituzione."
    elif giorni_rimanenti < 90:
        stato = "ATTENZIONE"
        colore_stato = "#ff9100" # Arancio
        messaggio = "Usura rilevata, monitorare nelle prossime settimane."

    # Mappa statica per questo asset
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
            "giorniRimasti": ((lampione.arm_data_ini + timedelta(days=int(int(row[2])))) - datetime.now().date()).days
        })
    #print(context)
    return render(request, 'core/lampione_asset.html', context)