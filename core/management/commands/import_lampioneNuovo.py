import pandas as pd
import numpy as np
import sys
from django.core.management.base import BaseCommand
from core.models import LampioneNuovo
import random
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Svuota la tabella e importa i nuovi lampioni da CSV (Digital Twin)'

    def handle(self, *args, **options):
        # --- PARAMETRI ---
        # Se stai usando il file con le coordinate generato da OSMnx, assicurati che il nome sia questo:
        CSV_FILE = 'output.csv' 
        CHUNK_SIZE = 5000

        self.stdout.write(self.style.WARNING(f"1. Svuotamento della tabella 'core_LampioneNuovo' in corso..."))
        LampioneNuovo.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Tabella svuotata con successo."))

        self.stdout.write(f"2. Lettura del file {CSV_FILE}...")
        try:
            df = pd.read_csv(CSV_FILE, low_memory=False)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"ERRORE: File {CSV_FILE} non trovato. Assicurati che sia nella cartella principale."))
            sys.exit()

        # Sostituisci i NaN di Pandas con None per il DB
        df = df.replace({np.nan: None})

        # Gestione date
        if 'arm_data_ini' in df.columns:
            df['arm_data_ini'] = pd.to_datetime(df['arm_data_ini'], format='%Y-%m-%d', errors='coerce')
        if 'arm_data_fin' in df.columns:
            df['arm_data_fin'] = pd.to_datetime(df['arm_data_fin'], format='%d/%m/%Y', errors='coerce')

        records_to_create = []
        self.stdout.write("3. Preparazione e Inserimento dei dati (Bulk Create)...")
        
        for index, row in df.iterrows():
            # I campi a sinistra ora corrispondono ai nomi delle colonne del CSV
            lampione = LampioneNuovo(
                arm_id=row['arm_id'],
                arm_data_ini=row['arm_data_ini'].date() if pd.notnull(row['arm_data_ini']) else None,
                arm_data_fin=row['arm_data_fin'].date() if pd.notnull(row['arm_data_fin']) else None,
                arm_altezza=row['arm_altezza'],
                arm_lunghezza_sbraccio=row['arm_lunghezza_sbraccio'],
                arm_numero_lampade=row['arm_numero_lampade'],
                arm_lmp_potenza_nominale=row['arm_lmp_potenza_nominale'],
                tar_cod=row['tar_cod'],
                tar_descr=row['tar_descr'],
                tpo_cod=row['tpo_cod'],
                tpo_descr=row['tpo_descr'],
                tmo_id=row['tmo_id'],
                # Inserimento delle coordinate (usa .get per evitare errori se la colonna manca)
                giorni_vita_attuale=row.get('giorni_vita_attuale', None),
                risk_score=row.get('prob_guasto', None)/100,
                latitudine=row.get('latitudine', None),
                traQuantoSiRompe=100/int(row.get('prob_guasto', None)) * 120 + random.randint(int(-((100/row.get('prob_guasto', None) * 120)/10)), int(((100/row.get('prob_guasto', None) * 120)/20))),
                #risk_score_date=row['arm_data_ini'].date() + ,
                longitudine=row.get('longitudine', None)
            )
            if lampione.arm_data_ini and lampione.traQuantoSiRompe:
                lampione.risk_score_date = datetime.now().date() + timedelta(days=int(lampione.traQuantoSiRompe))
            records_to_create.append(lampione)

            if len(records_to_create) >= CHUNK_SIZE:
                LampioneNuovo.objects.bulk_create(records_to_create)
                records_to_create = []
                self.stdout.write(f"  -> Inseriti {index + 1} record...")

        if records_to_create:
            LampioneNuovo.objects.bulk_create(records_to_create)
            self.stdout.write(f"  -> Inseriti tutti i rimanenti.")

        self.stdout.write(self.style.SUCCESS(f"\nCOMPLETATO! Inseriti {len(df)} lampioni nel database."))