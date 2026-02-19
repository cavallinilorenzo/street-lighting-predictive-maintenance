import pandas as pd
import numpy as np
import sys
from django.core.management.base import BaseCommand
from core.models import LampioneManutenzione
from django.utils import timezone

class Command(BaseCommand):
    help = 'Svuota la tabella e importa lo storico manutenzioni da CSV includendo TUTTI I CAMPI'

    def handle(self, *args, **options):
        # --- PARAMETRI ---
        CSV_FILE = 'lampioni_manutenzioni_coordinate.csv'
        CHUNK_SIZE = 5000

        self.stdout.write(self.style.WARNING(f"1. Svuotamento tabella 'core_LampioneManutenzione'..."))
        LampioneManutenzione.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Tabella svuotata con successo."))

        self.stdout.write(f"2. Lettura del file {CSV_FILE}...")
        try:
            df = pd.read_csv(CSV_FILE, low_memory=False)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"ERRORE: File {CSV_FILE} non trovato."))
            sys.exit()

        df = df.replace({np.nan: None})

        # --- CONVERSIONE DELLE DATE ---
        if 'sgn_data_inserimento' in df.columns:
            df['sgn_data_inserimento'] = pd.to_datetime(df['sgn_data_inserimento'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
        if 'arm_data_ini' in df.columns:
            df['arm_data_ini'] = pd.to_datetime(df['arm_data_ini'], format='%d/%m/%Y', errors='coerce')
        if 'arm_data_fin' in df.columns:
            df['arm_data_fin'] = pd.to_datetime(df['arm_data_fin'], format='%d/%m/%Y', errors='coerce')

        records_to_create = []
        self.stdout.write("3. Preparazione e Inserimento dei dati completi (Bulk Create)...")

        inseriti = 0

        for index, row in df.iterrows():
            arm_id = row['arm_id']

            # Gestione della TimeZone per la data del guasto
            data_ins = row['sgn_data_inserimento']
            if pd.notnull(data_ins):
                if timezone.is_naive(data_ins):
                    data_ins = timezone.make_aware(data_ins)
            else:
                data_ins = None

            # Creazione del record MAPPANDO TUTTE LE COLONNE DEL CSV
            manutenzione = LampioneManutenzione(
                # Dati del guasto
                sgn_id=row['sgn_id'],
                sgn_data_inserimento=data_ins,
                tcs_id=row['tcs_id'],
                tcs_descr=row['tcs_descr'],
                tci_id=row['tci_id'],
                tci_descr=row['tci_descr'],
                
                # Dati anagrafici del lampione
                arm_id=arm_id,
                arm_data_ini=row['arm_data_ini'].date() if pd.notnull(row['arm_data_ini']) else None,
                arm_data_fin=row['arm_data_fin'].date() if pd.notnull(row['arm_data_fin']) else None,
                arm_altezza=row['arm_altezza'] if pd.notnull(row['arm_altezza']) else 0,
                arm_lunghezza_sbraccio=row['arm_lunghezza_sbraccio'] if pd.notnull(row['arm_lunghezza_sbraccio']) else 0,
                arm_numero_lampade=row['arm_numero_lampade'] if pd.notnull(row['arm_numero_lampade']) else 1,
                arm_lmp_potenza_nominale=row['arm_lmp_potenza_nominale'] if pd.notnull(row['arm_lmp_potenza_nominale']) else -1,
                tar_cod=row['tar_cod'],
                tar_descr=row['tar_descr'],
                tpo_cod=row['tpo_cod'],
                tpo_descr=row['tpo_descr'],
                tmo_id=row['tmo_id'],
                
                # Coordinate
                latitudine=row.get('latitudine', None),
                longitudine=row.get('longitudine', None)
            )
            records_to_create.append(manutenzione)

            # Inserimento a blocchi per non sovraccaricare la RAM
            if len(records_to_create) >= CHUNK_SIZE:
                LampioneManutenzione.objects.bulk_create(records_to_create)
                inseriti += len(records_to_create)
                records_to_create = [] 
                self.stdout.write(f"  -> Processati {index + 1} record...")

        # Inserimento degli ultimi record rimanenti
        if records_to_create:
            LampioneManutenzione.objects.bulk_create(records_to_create)
            inseriti += len(records_to_create)

        self.stdout.write(self.style.SUCCESS(f"\nCOMPLETATO! Inseriti {inseriti} eventi di manutenzione con TUTTI i campi valorizzati."))