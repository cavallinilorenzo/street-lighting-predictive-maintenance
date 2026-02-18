import os
import sys
import django
import pandas as pd
import numpy as np
from django.utils.timezone import make_aware

# --- CONFIGURAZIONE DJANGO ---
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'street_lighting_predictive_maintenance.settings')

try:
    django.setup()
except Exception:
    sys.path.append(os.path.dirname(os.getcwd()))
    django.setup()

from core.models import LampioneManutenzione

# --- CONFIGURAZIONE FILE ---
NOME_FILE = 'lampioni_manutenzione_coordinate.csv'

def clean_int(value, default=0):
    """Converte valori NaN, float o stringhe in intero. Restituisce default se nullo."""
    try:
        if pd.isna(value) or value == '':
            return default
        return int(float(value))
    except (ValueError, TypeError):
        return default

def clean_float(value, default=0.0):
    """Pulisce i campi float."""
    try:
        if pd.isna(value) or value == '':
            return default
        return float(value)
    except (ValueError, TypeError):
        return default

def run():
    print(f"1. Leggo il CSV: {NOME_FILE}...")
    try:
        # Leggiamo il CSV
        df = pd.read_csv(NOME_FILE, sep=',') 
        
        # FIX 1: Puliamo i nomi delle colonne da eventuali spazi (es. ' arm_id' -> 'arm_id')
        df.columns = df.columns.str.strip()

        print("   Conversione date e gestione Timezone...")
        colonne_date = ['arm_data_ini', 'arm_data_fin', 'sgn_data_inserimento']
        for col in colonne_date:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
                # Rendiamo le date "aware"
                df[col] = df[col].apply(lambda x: make_aware(x) if pd.notnull(x) and x.tzinfo is None else x)

    except FileNotFoundError:
        print(f"ERRORE: Non trovo il file '{NOME_FILE}'. Assicurati che sia nella stessa cartella dello script.")
        return

    print(f"2. Svuoto la tabella LampioneManutenzione...")
    LampioneManutenzione.objects.all().delete()

    print(f"3. Preparazione di {len(df)} record...")
    lampioni_da_creare = []

    for index, row in df.iterrows():
        try:
            lampione = LampioneManutenzione(
                arm_id = clean_int(row.get('arm_id')), # Meglio usare clean_int anche qui per sicurezza
                
                # Date
                arm_data_ini = row.get('arm_data_ini') if pd.notnull(row.get('arm_data_ini')) else None,
                arm_data_fin = row.get('arm_data_fin') if pd.notnull(row.get('arm_data_fin')) else None,
                sgn_data_inserimento = row.get('sgn_data_inserimento') if pd.notnull(row.get('sgn_data_inserimento')) else None,

                # Campi Float
                arm_altezza = clean_float(row.get('arm_altezza')),
                arm_lunghezza_sbraccio = clean_float(row.get('arm_lunghezza_sbraccio')),
                
                # FIX 2: Campi Interi
                # Nello screenshot si vedono valori come '1.0' per le lampade, quindi usiamo clean_int
                arm_numero_lampade = clean_int(row.get('arm_numero_lampade'), default=1),
                
                # FIX 3: Corretto il typo 'lap' -> 'lmp' nel 'get'
                # Se nel CSV la colonna è diversa, questo eviterà il crash ma metterà 0
                arm_lmp_potenza_nominale = clean_int(row.get('arm_lmp_potenza_nominale', row.get('arm_lap_potenza_nominale')), default=0),
                
                # Testi (gestione NaN per evitare errori su campi CharField)
                tar_cod = row.get('tar_cod') if pd.notnull(row.get('tar_cod')) else None,
                tar_descr = row.get('tar_descr') if pd.notnull(row.get('tar_descr')) else None,
                
                # FIX 4: Gli ID nello screenshot sono float (es. 19.0, 45.0), vanno convertiti
                tmo_id = clean_int(row.get('tmo_id')),
                
                tpo_cod = row.get('tpo_cod') if pd.notnull(row.get('tpo_cod')) else None,
                tpo_descr = row.get('tpo_descr') if pd.notnull(row.get('tpo_descr')) else None,
                
                sgn_id = clean_int(row.get('sgn_id')),
                
                tcs_id = clean_int(row.get('tcs_id')),
                tcs_descr = row.get('tcs_descr') if pd.notnull(row.get('tcs_descr')) else None,
                
                tci_id = clean_int(row.get('tci_id')),
                tci_descr = row.get('tci_descr') if pd.notnull(row.get('tci_descr')) else None,
                
                # Coordinate
                latitudine = clean_float(row.get('latitudine')),
                longitudine = clean_float(row.get('longitudine'))
            )
            lampioni_da_creare.append(lampione)
            
        except Exception as e:
            print(f"Errore critico alla riga {index}: {e}")

    print(f"4. Inserimento bulk di {len(lampioni_da_creare)} record...")
    # ignore_conflicts=True è utile se ci sono duplicati di ID che vuoi saltare, altrimenti rimuovilo
    LampioneManutenzione.objects.bulk_create(lampioni_da_creare, batch_size=1000)
    
    print("--- SUCCESS: Database popolato correttamente! ---")

if __name__ == '__main__':
    run()