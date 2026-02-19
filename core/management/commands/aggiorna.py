from django.core.management.base import BaseCommand
from django.core.exceptions import FieldError
from core.models import LampioneNuovo, LampioneManutenzione
from datetime import date

class Command(BaseCommand):
    help = 'Aggiorna la data di fine validità dei lampioni dal 13/02/2026 al 19/02/2026'

    def handle(self, *args, **options):
        # Definiamo le date come oggetti "date" nativi di Python
        data_vecchia = date(2026, 2, 13)
        data_nuova = date(2026, 2, 19)

        self.stdout.write(self.style.WARNING(f"Inizio aggiornamento date da {data_vecchia.strftime('%d/%m/%Y')} a {data_nuova.strftime('%d/%m/%Y')}..."))

        # =========================================================
        # 1. AGGIORNAMENTO TABELLA LAMPIONENUOVO
        # =========================================================
        try:
            # .filter() trova tutte le righe con la data vecchia
            # .update() le sovrascrive tutte in un colpo solo con la data nuova
            righe_aggiornate_nuovo = LampioneNuovo.objects.filter(arm_data_fin=data_vecchia).update(arm_data_fin=data_nuova)
            
            self.stdout.write(self.style.SUCCESS(
                f"  -> core_LampioneNuovo: Aggiornati con successo {righe_aggiornate_nuovo} lampioni."
            ))
        except FieldError:
            self.stdout.write(self.style.ERROR("  -> core_LampioneNuovo non possiede il campo 'arm_data_fin'."))

        # =========================================================
        # 2. AGGIORNAMENTO TABELLA LAMPIONEMANUTENZIONE (Se applicabile)
        # =========================================================
        try:
            righe_aggiornate_manutenzione = LampioneManutenzione.objects.filter(arm_data_fin=data_vecchia).update(arm_data_fin=data_nuova)
            
            self.stdout.write(self.style.SUCCESS(
                f"  -> core_LampioneManutenzione: Aggiornate con successo {righe_aggiornate_manutenzione} righe."
            ))
        except FieldError:
            # È normale che entri qui se la tabella storico non ha il campo arm_data_fin (come da standard relazionale)
            self.stdout.write(self.style.NOTICE(
                "  -> core_LampioneManutenzione ignorata: non possiede il campo 'arm_data_fin' (normale in un DB relazionale)."
            ))

        self.stdout.write(self.style.SUCCESS("\nOPERAZIONE COMPLETATA!"))