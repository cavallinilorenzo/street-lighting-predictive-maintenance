import os
import sys
import django
import pandas as pd

# --- FIX FONDAMENTALE PER IL PERCORSO ---
# Aggiunge la cartella corrente al percorso di Python, così trova il file settings
sys.path.append(os.getcwd())

# --- CONFIGURAZIONE DJANGO ---
# Impostiamo il modulo corretto che abbiamo letto nel tuo manage.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'street_lighting_predictive_maintenance.settings')

try:
    django.setup()
except ModuleNotFoundError:
    # Se fallisce ancora, proviamo ad aggiungere la cartella madre al path
    sys.path.append(os.path.dirname(os.getcwd()))
    django.setup()

from core.models import LampioneNuovo

# --- CONFIGURAZIONE FILE ---
NOME_FILE = 'lampioni_coordinate_finali.csv'

def run():
    print("1. Leggo il CSV...")
    try:
        # Assicurati che il separatore sia corretto (virgola o punto e virgola)
        # Se il file finale è quello generato dal mio script precedente, usa sep=','
        df = pd.read_csv(NOME_FILE, sep=',') 
    except FileNotFoundError:
        print(f"ERRORE: Non trovo il file '{NOME_FILE}'. Assicurati che sia nella stessa cartella dello script.")
        return

    # Pulizia dati: Pandas usa "NaN" per i vuoti, Django vuole None
    df = df.where(pd.notnull(df), None)

    print(f"2. CANCELLO tutti i dati vecchi dalla tabella LampioneNuovo...")
    LampioneNuovo.objects.all().delete()

    print("3. Preparo i nuovi dati...")
    lampioni_da_creare = []

    # Iteriamo sulle righe del CSV
    for index, row in df.iterrows():
        try:
            lampione = LampioneNuovo(
                # --- MAPPA QUI I CAMPI ---
                # A sinistra i nomi nel models.py, a destra i nomi nel CSV
                arm_id = row['arm_id'], 
                
                # Aggiungi qui gli altri campi se necessario (es. arm_altezza=row['arm_altezza'])
                
                # Le coordinate
                latitudine = row['latitudine'],
                longitudine = row['longitudine']
            )
            lampioni_da_creare.append(lampione)
        except KeyError as e:
            print(f"ERRORE: Non trovo la colonna {e} nel CSV. Controlla i nomi delle intestazioni.")
            return

    print(f"4. Sto salvando {len(lampioni_da_creare)} nuovi lampioni nel DB...")
    LampioneNuovo.objects.bulk_create(lampioni_da_creare)
    
    print("FATTO! Database aggiornato con successo.")

if __name__ == '__main__':
    run()