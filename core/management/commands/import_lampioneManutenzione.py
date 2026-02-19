import pandas as pd
import numpy as np
import sys
from django.core.management.base import BaseCommand
from core.models import LampioneManutenzione
from django.utils import timezone # Aggiunto per risolvere i warning sulle date

class Command(BaseCommand):
    help = 'Svuota la tabella e importa lo storico manutenzioni da CSV (Importazione Totale)'

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

        # Conversione della data
        if 'sgn_data_inserimento' in df.columns:
            df['sgn_data_inserimento'] = pd.to_datetime(df['sgn_data_inserimento'], format='%d/%m/%Y %H:%M:%S', errors='coerce')

        records_to_create = []
        self.stdout.write("3. Preparazione e Inserimento dei dati (Bulk Create)...")

        inseriti = 0

        for index, row in df.iterrows():
            arm_id = row['arm_id']

            # Gestione della TimeZone per eliminare i RuntimeWarning
            data_ins = row['sgn_data_inserimento']
            if pd.notnull(data_ins):
                # Se la data non ha il fuso orario, Django glielo aggiunge
                if timezone.is_naive(data_ins):
                    data_ins = timezone.make_aware(data_ins)
            else:
                data_ins = None

            manutenzione = LampioneManutenzione(
                sgn_id=row['sgn_id'],
                arm_id=arm_id,  # Associazione diretta dell'ID
                sgn_data_inserimento=data_ins,
                tcs_id=row['tcs_id'],
                tcs_descr=row['tcs_descr'],
                tci_id=row['tci_id'],
                tci_descr=row['tci_descr'],
                latitudine=row.get('latitudine', None),
                longitudine=row.get('longitudine', None)
            )
            records_to_create.append(manutenzione)

            if len(records_to_create) >= CHUNK_SIZE:
                LampioneManutenzione.objects.bulk_create(records_to_create)
                inseriti += len(records_to_create)
                records_to_create = [] 
                self.stdout.write(f"  -> Processati {index + 1} record...")

        if records_to_create:
            LampioneManutenzione.objects.bulk_create(records_to_create)
            inseriti += len(records_to_create)

        self.stdout.write(self.style.SUCCESS(f"\nCOMPLETATO! Inseriti {inseriti} eventi di manutenzione nel database."))