import csv
from django.utils import timezone
from datetime import datetime
from django.core.management.base import BaseCommand
from core.models import Lampione

class Command(BaseCommand):
    help = 'Importa dati lampioni da CSV'

    def add_arguments(self, parser):
        parser.add_argument('path', type=str, help='Percorso del file CSV')

    def handle(self, *args, **kwargs):
        path = kwargs['path']
        buffer_dati = []
        
        print(f"Leggo il file: {path}...")

        # Funzione helper per convertire le date italiane (gg/mm/aaaa)
        def parse_date(date_str, is_datetime=False):
            if not date_str or date_str.strip() == '':
                return None
            try:
                if is_datetime:
                    # Parsa la data (ancora "naive")
                    dt = datetime.strptime(date_str, '%d/%m/%Y %H:%M:%S')
                    # La rende "aware" (gli assegna il fuso orario corrente, es. Europe/Rome)
                    return timezone.make_aware(dt)
                else:
                    # Per le date senza orario (DateField), non serve il fuso orario
                    return datetime.strptime(date_str, '%d/%m/%Y').date()
            except ValueError:
                return None

        with open(path, 'r', encoding='utf-8') as file:
            # QUI STA IL TRUCCO: delimiter=';'
            reader = csv.DictReader(file, delimiter=';')
            
            for row in reader:
                try:
                    l = Lampione(
                        arm_id=int(row['arm_id']),
                        
                        # Parsing date
                        arm_data_ini=parse_date(row['arm_data_ini']),
                        arm_data_fin=parse_date(row['arm_data_fin']),
                        
                        # Parsing numeri (float/int)
                        arm_altezza=float(row['arm_altezza'] or 0),
                        arm_lunghezza_sbraccio=float(row['arm_lunghezza_sbraccio'] or 0),
                        arm_numero_lampade=int(float(row['arm_numero_lampade'] or 0)),
                        arm_lmp_potenza_nominale=float(row['arm_lmp_potenza_nominale'] or 0),
                        
                        # Stringhe
                        tar_descr=row['tar_descr'],
                        tpo_descr=row['tpo_descr'],
                        
                        # Manutenzione (Datetime)
                        sgn_data_inserimento=parse_date(row['sgn_data_inserimento'], is_datetime=True),
                        tcs_descr=row['tcs_descr'],
                        tci_descr=row['tci_descr']
                    )
                    buffer_dati.append(l)
                except Exception as e:
                    print(f"Errore riga ID {row.get('arm_id', '?')}: {e}")

        # Salvataggio Bulk
        print(f"Trovate {len(buffer_dati)} righe. Inizio salvataggio...")
        Lampione.objects.bulk_create(buffer_dati, batch_size=2000, ignore_conflicts=True)
        
        self.stdout.write(self.style.SUCCESS(f'Fatto! Importati {len(buffer_dati)} lampioni.'))