import os
import sys
import django
import pandas as pd
import numpy as np
from django.utils.timezone import make_aware

# --- CONFIGURAZIONE DJANGO ---
sys.path.append(os.getcwd())
# Assicurati che il nome del progetto nelle settings sia corretto
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'street_lighting_predictive_maintenance.settings')

try:
    django.setup()
except Exception:
    sys.path.append(os.path.dirname(os.getcwd()))
    django.setup()

# IMPORTIAMO IL NUOVO MODELLO
from core.models import LampioneNuovo

# --- CONFIGURAZIONE FILE ---
# Inserisci qui il nome esatto del file CSV che hai nello screenshot
NOME_FILE = 'lampioni_coordinate_finali.csv' 

def clean_int(value, default=0):
    """
    Converte valori NaN, float (es. 613.0) o stringhe in intero.
    Fondamentale perché nel CSV gli ID appaiono come float.
    """
    try:
        if pd.isna(value) or value == '':
            return default
        return int(float(value))
    except (ValueError, TypeError):
        return default

def clean_float(value, default=0.0):
    """Pulisce i campi float (es. Latitudine, Altezze)."""
    try:
        if pd.isna(value) or value == '':
            return default
        # Sostituisce la virgola con il punto se necessario
        if isinstance(value, str):
            value = value.replace(',', '.')
        return float(value)
    except (ValueError, TypeError):
        return default

def run():
    print(f"1. Leggo il CSV: {NOME_FILE}...")
    try:
        # Leggiamo il CSV
        df = pd.read_csv(NOME_FILE, sep=',') 
        
        # FIX CRITICO: Normalizziamo tutte le colonne in minuscolo e rimuoviamo spazi
        # Questo risolve il problema di "Latitudine" (maiuscolo) vs "latitudine" (modello)
        df.columns = df.columns.str.strip().str.lower()

        print("   Conversione date e gestione Timezone...")
        # Aggiungi qui tutte le colonne che contengono date
        colonne_date = ['arm_data_ini', 'arm_data_fin', 'sgn_data_inserimento']
        
        for col in colonne_date:
            if col in df.columns:
                # dayfirst=True è importante per date formato italiano (31/12/2020)
                df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
                # Rendiamo le date "aware" (con fuso orario) per Django
                df[col] = df[col].apply(lambda x: make_aware(x) if pd.notnull(x) and x.tzinfo is None else x)

    except FileNotFoundError:
        print(f"ERRORE: Non trovo il file '{NOME_FILE}'. Assicurati che sia nella cartella corretta.")
        return

    print(f"2. Svuoto la tabella LampioneNuovo...")
    LampioneNuovo.objects.all().delete()

    print(f"3. Preparazione dei record da inserire...")
    lampioni_da_creare = []
    errori_count = 0

    for index, row in df.iterrows():
        try:
            # MAPPING DEI CAMPI
            # Usiamo .get('nome_colonna_csv') per mappare al modello
            
            lampione = LampioneNuovo(
                # --- Identificativi ---
                arm_id = clean_int(row.get('arm_id')),
                
                # --- Date ---
                arm_data_ini = row.get('arm_data_ini') if pd.notnull(row.get('arm_data_ini')) else None,
                arm_data_fin = row.get('arm_data_fin') if pd.notnull(row.get('arm_data_fin')) else None,
                sgn_data_inserimento = row.get('sgn_data_inserimento') if pd.notnull(row.get('sgn_data_inserimento')) else None,

                # --- Dati Tecnici (Float e Int) ---
                # Nello screenshot le colonne sembrano avere questi nomi, verifica se corrispondono al tuo Modello Django
                arm_altezza = clean_float(row.get('arm_altezza')), 
                arm_lunghezza_sbraccio = clean_float(row.get('arm_lunghezza_sbraccio')),
                
                # clean_int qui è vitale perché nello screenshot '1.0' è float
                arm_numero_lampade = clean_int(row.get('arm_numero_lampade'), default=1),
                
                # Gestione potenza (cerca 'arm_lmp...' o 'arm_lap...' per sicurezza)
                arm_lmp_potenza_nominale = clean_int(row.get('arm_lmp_potenza_nominale', row.get('arm_lap_potenza_nominale')), default=0),
                
                # --- Classificazioni (Tar, Tmo, Tpo) ---
                tar_cod = row.get('tar_cod') if pd.notnull(row.get('tar_cod')) else None,
                tar_descr = row.get('tar_descr') if pd.notnull(row.get('tar_descr')) else None,
                
                # ID esterni (tmo, sgn, tcs, tci) convertiti con clean_int per gestire i ".0"
                tmo_id = clean_int(row.get('tmo_id')),
                
                tpo_cod = row.get('tpo_cod') if pd.notnull(row.get('tpo_cod')) else None,
                tpo_descr = row.get('tpo_descr') if pd.notnull(row.get('tpo_descr')) else None,
                
                sgn_id = clean_int(row.get('sgn_id')),
                
                tcs_id = clean_int(row.get('tcs_id')),
                tcs_descr = row.get('tcs_descr') if pd.notnull(row.get('tcs_descr')) else None,
                
                tci_id = clean_int(row.get('tci_id')),
                tci_descr = row.get('tci_descr') if pd.notnull(row.get('tci_descr')) else None,
                
                # --- Coordinate ---
                # Grazie al 'df.columns.str.lower()' all'inizio, prenderà sia 'Latitudine' che 'latitudine'
                latitudine = clean_float(row.get('latitudine')),
                longitudine = clean_float(row.get('longitudine'))
            )
            lampioni_da_creare.append(lampione)
            
        except Exception as e:
            errori_count += 1
            # Stampa l'errore solo per i primi 5 per non intasare la console
            if errori_count <= 5:
                print(f"Errore riga {index}: {e}")

    print(f"4. Inserimento bulk di {len(lampioni_da_creare)} record...")
    if len(lampioni_da_creare) > 0:
        LampioneNuovo.objects.bulk_create(lampioni_da_creare, batch_size=1000)
        print("--- SUCCESS: Database popolato correttamente! ---")
    else:
        print("--- ATTENZIONE: Nessun record inserito. Controlla i nomi delle colonne nel CSV. ---")

if __name__ == '__main__':
    run()