import os
import sys
import django
import pandas as pd

# --- CONFIGURAZIONE DJANGO ---
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'street_lighting_predictive_maintenance.settings')

try:
    django.setup()
except Exception as e:
    sys.path.append(os.path.dirname(os.getcwd()))
    django.setup()

from core.models import LampioneNuovo

# --- CONFIGURAZIONE FILE ---
NOME_FILE = 'lampioni_coordinate_finali.csv'

def run():
    print(f"1. Leggo il CSV: {NOME_FILE}...")
    try:
        # Nota: assicurati che il separatore sia quello corretto del tuo file finale
        df = pd.read_csv(NOME_FILE, sep=',') 
    except FileNotFoundError:
        print(f"ERRORE: Non trovo il file '{NOME_FILE}'.")
        return

    # Sostituiamo i valori NaN con None (fondamentale per i campi Null in Django)
    df = df.where(pd.notnull(df), None)

    print(f"2. CANCELLO tutti i dati esistenti dalla tabella LampioneNuovo...")
    tot_cancellati = LampioneNuovo.objects.all().count()
    LampioneNuovo.objects.all().delete()
    print(f"   Pulizia completata: rimossi {tot_cancellati} record.")

    print("3. Preparazione oggetti per l'inserimento...")
    lampioni_da_creare = []

    for index, row in df.iterrows():
        try:
            # Creiamo l'istanza del modello mappando i campi chiave per le tue icone
            lampione = LampioneNuovo(
                arm_id = row['arm_id'],
                
                # Campi descrittivi per le icone (Assicurati che esistano nel models.py)
                # Se nel tuo models.py hanno nomi diversi, correggi la parte a sinistra dell'uguale
                tar_descr = row.get('tar_descr', 'Non noto'), # Tipo armatura
                tpo_descr = row.get('tpo_descr', 'Non noto'), # Tipo supporto
                
                # Dati tecnici (opzionali ma utili per i popup)
                arm_altezza = row.get('arm_altezza', 0),
                arm_lmp_potenza_nominale = row.get('arm_lmp_potenza_nominale', 0),
                
                # Coordinate geografiche
                latitudine = row['latitudine'],
                longitudine = row['longitudine']
            )
            lampioni_da_creare.append(lampione)
            
        except KeyError as e:
            print(f"ERRORE: Colonna mancante nel CSV: {e}")
            return

    print(f"4. Esecuzione inserimento massivo (Bulk Create) di {len(lampioni_da_creare)} elementi...")
    
    # Usiamo batch_size per evitare di sovraccaricare la memoria se i record sono molti
    LampioneNuovo.objects.bulk_create(lampioni_da_creare, batch_size=1000)
    
    print("--- SUCCESS: Database popolato correttamente! ---")

if __name__ == '__main__':
    run()