from django.db import models

# Create your models here.
class Lampione(models.Model):
    # arm_id sembra essere l'identificativo univoco
    arm_id = models.IntegerField(unique=True, db_index=True)
    
    # Date (possono essere vuote, quindi null=True)
    arm_data_ini = models.DateField(null=True, blank=True)
    arm_data_fin = models.DateField(null=True, blank=True)
    
    # Dati tecnici
    arm_altezza = models.FloatField(default=0.0)
    arm_lunghezza_sbraccio = models.FloatField(default=0.0)
    arm_numero_lampade = models.IntegerField(default=0)
    arm_lmp_potenza_nominale = models.FloatField(default=0.0)
    
    # Descrizioni
    tar_descr = models.CharField(max_length=255, null=True, blank=True) # Es: Armatura stradale
    tpo_descr = models.CharField(max_length=255, null=True, blank=True) # Es: Sbraccio su palo
    
    # Manutenzione
    sgn_data_inserimento = models.DateTimeField(null=True, blank=True)
    tcs_descr = models.CharField(max_length=255, null=True, blank=True) # Es: lampada intermittente
    tci_descr = models.CharField(max_length=255, null=True, blank=True) # Es: sostituito lampada

    def __str__(self):
        return f"Lampione {self.arm_id}"