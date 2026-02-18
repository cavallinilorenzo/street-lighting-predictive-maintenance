import os
import sys
import django
import pandas as pd
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
    """Converte valori NaN o invalidi in un intero o None."""
    try:
        if pd.isna(value):
            return default
        return int(float(value)) # float(value) gestisce casi come "1.0"
    except (ValueError, TypeError):
        return default

def run():
    print(f"1. Leggo il CSV: {NOME_FILE}...")
    try:
        df = pd.read_csv(NOME_FILE, sep=',') 
        
        print("   Conversione date e gestione Timezone...")
        colonne_date = ['arm_data_ini', 'arm_data_fin', 'sgn_data_inserimento']
        for col in colonne_date:
            if col in df.columns:
                # Trasformiamo in datetime
                df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
                # Rendiamo le date "aware" (con fuso orario) per evitare i warning
                df[col] = df[col].apply(lambda x: make_aware(x) if pd.notnull(x) and x.tzinfo is None else x)

    except FileNotFoundError:
        print(f"ERRORE: Non trovo il file '{NOME_FILE}'.")
        return

    print(f"2. Svuoto la tabella LampioneManutenzione...")
    LampioneManutenzione.objects.all().delete()

    print(f"3. Preparazione di {len(df)} record...")
    lampioni_da_creare = []

    for index, row in df.iterrows():
        try:
            lampione = LampioneManutenzione(
                arm_id = row['arm_id'],
                
                # Date (ora sono oggetti "timezone-aware")
                arm_data_ini = row.get('arm_data_ini') if pd.notnull(row.get('arm_data_ini')) else None,
                arm_data_fin = row.get('arm_data_fin') if pd.notnull(row.get('arm_data_fin')) else None,
                sgn_data_inserimento = row.get('sgn_data_inserimento') if pd.notnull(row.get('sgn_data_inserimento')) else None,

                # Campi Numerici con pulizia per evitare l'errore NaN
                arm_altezza = row.get('arm_altezza', 0.0) if pd.notnull(row.get('arm_altezza')) else 0.0,
                arm_lunghezza_sbraccio = row.get('arm_lunghezza_sbraccio', 0.0) if pd.notnull(row.get('arm_lunghezza_sbraccio')) else 0.0,
                
                # QUI RISOLVIAMO IL TUO ERRORE:
                arm_numero_lampade = clean_int(row.get('arm_numero_lampade'), default=1),
                arm_lmp_potenza_nominale = clean_int(row.get('arm_lap_potenza_nominale'), default=0),
                
                # Testi
                tar_cod = row.get('tar_cod'),
                tar_descr = row.get('tar_descr'),
                tmo_id = row.get('tmo_id'),
                tpo_cod = row.get('tpo_cod'),
                tpo_descr = row.get('tpo_descr'),
                sgn_id = row.get('sgn_id'),
                tcs_id = row.get('tcs_id'),
                tcs_descr = row.get('tcs_descr'),
                tci_id = row.get('tci_id'),
                tci_descr = row.get('tci_descr'),
                
                # Coordinate
                latitudine = row['latitudine'],
                longitudine = row['longitudine']
            )
            lampioni_da_creare.append(lampione)
            
        except Exception as e:
            print(f"Errore critico alla riga {index}: {e}")

    print(f"4. Inserimento bulk di {len(lampioni_da_creare)} record...")
    LampioneManutenzione.objects.bulk_create(lampioni_da_creare, batch_size=1000)
    
    print("--- SUCCESS: Database popolato correttamente! ---")

if __name__ == '__main__':
    run()