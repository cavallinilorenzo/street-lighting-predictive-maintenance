from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import LampioneNuovo # Sostituisci con il nome reale del tuo modello

class Command(BaseCommand):
    help = 'Aggiorna il campo arm_data_fin alla data odierna per tutti i record'

    def handle(self, *args, **kwargs):
        data_odierna = timezone.now().date()
        
        # Esegui l'aggiornamento (aggiungi .filter() prima di .update() se necessario)
        righe_aggiornate = LampioneNuovo.objects.update(arm_data_fin=data_odierna)
        
        # Mostra un messaggio di successo nel terminale
        self.stdout.write(
            self.style.SUCCESS(f'Successo! {righe_aggiornate} record aggiornati a {data_odierna}')
        )