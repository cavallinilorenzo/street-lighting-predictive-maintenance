from django.db import models

# Create your models here.
class LampioneBase(models.Model):
    arm_id = models.IntegerField(db_index=True)
    arm_data_ini = models.DateField(null=True, blank=True)
    arm_data_fin = models.DateField(null=True, blank=True)
    arm_altezza = models.FloatField(null=True, blank=True)
    arm_lunghezza_sbraccio = models.FloatField(null=True, blank=True)
    arm_numero_lampade = models.IntegerField(null=True, blank=True)
    arm_lmp_potenza_nominale = models.FloatField(null=True, blank=True)
    tar_cod = models.CharField(max_length=50, null=True, blank=True)
    tar_descr = models.CharField(max_length=255, null=True, blank=True)
    tmo_id = models.FloatField(null=True, blank=True)
    tpo_cod = models.CharField(max_length=50, null=True, blank=True)
    tpo_descr = models.CharField(max_length=255, null=True, blank=True)
    
    # Campi manutenzione (possono essere nulli)
    sgn_id = models.FloatField(null=True, blank=True)
    sgn_data_inserimento = models.DateTimeField(null=True, blank=True)
    tcs_id = models.FloatField(null=True, blank=True)
    tcs_descr = models.CharField(max_length=255, null=True, blank=True)
    tci_id = models.FloatField(null=True, blank=True)
    tci_descr = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        abstract = True

# Tabella per lampioni_nuovi.csv
class LampioneNuovo(LampioneBase):
    latitudine = models.FloatField(null=True, blank=True)
    longitudine = models.FloatField(null=True, blank=True)
    giorni_vita_attuale = models.IntegerField(null=True, blank=True)
    traQuantoSiRompe = models.IntegerField(null=True, blank=True)
    risk_score= models.FloatField(null=True, blank=True)
    risk_score_date= models.DateTimeField(null=True, blank=True)
    pass

class Segnalazioni(models.Model):
    arm_id = models.IntegerField(db_index=True)
    note = models.CharField(max_length=255, null=True, blank=True)
    problema = models.CharField(max_length=255, null=True, blank=True)
    datetime= models.DateTimeField(null=True, blank=True)

# Tabella per lampioni_con_manutenzione.csv
class LampioneManutenzione(LampioneBase):
    latitudine = models.FloatField(null=True, blank=True)
    longitudine = models.FloatField(null=True, blank=True)
    pass