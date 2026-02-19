# core/management/commands/score_model.py

import os
import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand
from joblib import load

class Command(BaseCommand):
    help = "Calcola i risk score sull'anagrafica attiva e aggiorna il Database Django."

    def add_arguments(self, parser):
        parser.add_argument("--model", type=str, required=True, help="Path al modello .joblib.")
        parser.add_argument("--csv", type=str, required=True, help="Path al CSV delle armature attive (es. lampioni_attivi_coordinate.csv).")
        parser.add_argument("--out-csv", type=str, default="ml_artifacts/risk_scores_con_residui.csv")

    def handle(self, *args, **opts):
        model_path = opts["model"]
        csv_path = opts["csv"]
        out_csv = os.path.join(settings.BASE_DIR, opts["out_csv"])
        os.makedirs(os.path.dirname(out_csv), exist_ok=True)

        self.stdout.write(f"Carico modello: {model_path}")
        clf = load(model_path)
        
        self.stdout.write(f"Leggo CSV anagrafica: {csv_path}")
        df = pd.read_csv(csv_path, low_memory=False)
        
        # 1. Isoliamo ID validi
        df['arm_id'] = pd.to_numeric(df['arm_id'], errors='coerce')
        df = df[df['arm_id'].notna()].copy()
        df['arm_id'] = df['arm_id'].astype(int)

        # 2. LA MAGIA: Calcoliamo 'giorni_osservati_finora' al volo se manca
        if 'giorni_osservati_finora' not in df.columns:
            if 'arm_data_ini' in df.columns:
                self.stdout.write("Calcolo l'età dei lampioni da 'arm_data_ini'...")
                # Trasformiamo la colonna in date reali
                df['arm_data_ini'] = pd.to_datetime(df['arm_data_ini'], errors='coerce')
                # Sottraiamo la data di installazione ad oggi per ottenere i giorni
                df['giorni_osservati_finora'] = (pd.Timestamp.now() - df['arm_data_ini']).dt.days
                # Se un lampione non ha la data inserita (NaN), gli diamo la media dell'impianto
                mediana_eta = df['giorni_osservati_finora'].median()
                df['giorni_osservati_finora'] = df['giorni_osservati_finora'].fillna(mediana_eta)
            else:
                raise ValueError("Errore: Il CSV non ha né 'giorni_osservati_finora' né 'arm_data_ini'.")

        # 3. Allineamento Feature per il Modello
        feature_cols = ["arm_altezza", "arm_lmp_potenza_nominale", "giorni_osservati_finora", "tmo_id"]
        
        # Conversione dei tipi per evitare crash
        df['tmo_id'] = df['tmo_id'].astype(str)
        for c in ["arm_altezza", "arm_lmp_potenza_nominale", "giorni_osservati_finora"]:
            df[c] = pd.to_numeric(df[c], errors='coerce')

        X = df[feature_cols].copy()
        
        # 4. Predizione AI
        self.stdout.write("Calcolo delle predizioni in corso...")
        proba = clf.predict_proba(X)[:, 1]
        df["risk_score"] = proba
        # Salvataggio file CSV per sicurezza/debug
        df_out = df[["arm_id", "risk_score"]].sort_values("risk_score", ascending=False)
        df_out.to_csv(out_csv, index=False)
        self.stdout.write(self.style.SUCCESS(f"Punteggi salvati su file: {out_csv}"))

        # --- AGGIORNAMENTO DATABASE DJANGO ---
        from core.models import LampioneNuovo
        from django.utils.timezone import now
        
        self.stdout.write("Aggiornamento del Database in corso...")
        scores_dict = df_out.set_index('arm_id')['risk_score'].to_dict()
        
        pred = pd.read_csv("macchine learning\\predizioneDelGesu.csv")

        merged = df_out.merge(
            pred[["arm_id", "pred_giorni_residui"]],
            on="arm_id",
            how="inner"
        )
        merged.loc[merged["pred_giorni_residui"] > 10000, "pred_giorni_residui"] = -1

        merged=merged.set_index('arm_id')['pred_giorni_residui'].to_dict()
        
        # Prendiamo dal DB solo i lampioni che esistono nel CSV
        lampioni = LampioneNuovo.objects.filter(arm_id__in=scores_dict.keys())
        #print(giorni_dict)
        for lampione in lampioni:
            lampione.risk_score = scores_dict[lampione.arm_id]
            lampione.risk_score_date = now()
            lampione.traQuantoSiRompe = merged[lampione.arm_id]
            
        LampioneNuovo.objects.bulk_update(lampioni, ['risk_score', 'risk_score_date','traQuantoSiRompe'])
        self.stdout.write(self.style.SUCCESS("Database Django aggiornato con successo! Siete pronti per la mappa!"))