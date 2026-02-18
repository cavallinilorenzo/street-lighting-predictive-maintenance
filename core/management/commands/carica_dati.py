import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import LampioneNuovo, LampioneManutenzione

class Command(BaseCommand):
    help = 'Importa entrambi i CSV nelle tabelle dedicate'

    def handle(self, *args, **options):
        self.importa_csv('lampioni_nuovi_10k.csv', LampioneNuovo)
        self.importa_csv('lampioni_con_manutenzione.csv', LampioneManutenzione)

    def importa_csv(self, file_path, model_class):
        self.stdout.write(f"Caricamento di {file_path}...")
        oggetti = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                # Helper per pulire i dati
                def clean_float(val): return float(val) if val and val.strip() else None
                def clean_int(val): return int(float(val)) if val and val.strip() else None
                def parse_dt(val, is_time=False):
                    if not val or val.strip() == '': return None
                    try:
                        if is_time:
                            dt = datetime.strptime(val, '%d/%m/%Y %H:%M:%S')
                            return timezone.make_aware(dt)
                        return datetime.strptime(val, '%d/%m/%Y').date()
                    except: return None

                obj = model_class(
                    arm_id=clean_int(row['arm_id']),
                    arm_data_ini=parse_dt(row['arm_data_ini']),
                    arm_data_fin=parse_dt(row['arm_data_fin']),
                    arm_altezza=clean_float(row['arm_altezza']),
                    arm_lunghezza_sbraccio=clean_float(row['arm_lunghezza_sbraccio']),
                    arm_numero_lampade=clean_int(row['arm_numero_lampade']),
                    arm_lmp_potenza_nominale=clean_float(row['arm_lmp_potenza_nominale']),
                    tar_cod=row['tar_cod'],
                    tar_descr=row['tar_descr'],
                    tmo_id=clean_float(row['tmo_id']),
                    tpo_cod=row['tpo_cod'],
                    tpo_descr=row['tpo_descr'],
                    sgn_id=clean_float(row['sgn_id']),
                    sgn_data_inserimento=parse_dt(row['sgn_data_inserimento'], True),
                    tcs_id=clean_float(row['tcs_id']),
                    tcs_descr=row['tcs_descr'],
                    tci_id=clean_float(row['tci_id']),
                    tci_descr=row['tci_descr'],
                )
                oggetti.append(obj)
        
        model_class.objects.bulk_create(oggetti, batch_size=1000)
        self.stdout.write(self.style.SUCCESS(f"Completato: {len(oggetti)} righe caricate."))