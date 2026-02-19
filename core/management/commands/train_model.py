# core/management/commands/train_model.py

import json
import os
import numpy as np
import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand
from joblib import dump

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder
from sklearn.model_selection import train_test_split

class Command(BaseCommand):
    help = "Allena modello predittivo sul nuovo dataset CSV statico."

    def add_arguments(self, parser):
        parser.add_argument("--csv", type=str, required=True, help="Path al nuovo CSV.")
        parser.add_argument("--out-dir", type=str, default="ml_artifacts")

    def handle(self, *args, **opts):
        csv_path = opts["csv"]
        out_dir = os.path.join(settings.BASE_DIR, opts["out_dir"])
        os.makedirs(out_dir, exist_ok=True)

        self.stdout.write(f"Leggo nuovo CSV: {csv_path}")
        df = pd.read_csv(csv_path)

        # 1. Creazione Target (y = 1 se giorni_guasto > 0 altrimenti 0)
        df['y'] = (df['giorni_guasto'] > 0).astype(int)

        # 2. Pulizia tipi
        df['arm_altezza'] = pd.to_numeric(df['arm_altezza'], errors='coerce')
        df['arm_lmp_potenza_nominale'] = pd.to_numeric(df['arm_lmp_potenza_nominale'], errors='coerce')
        df['giorni_osservati_finora'] = pd.to_numeric(df['giorni_osservati_finora'], errors='coerce')
        df['tmo_id'] = df['tmo_id'].astype(str)

        self.stdout.write(f"Righe lette: {len(df):,}")
        self.stdout.write(f"Guasti trovati: {df['y'].sum():,} ({df['y'].mean()*100:.2f}%)")

        # 3. Definizione Feature
        numeric_features = ["arm_altezza", "arm_lmp_potenza_nominale", "giorni_osservati_finora"]
        categorical_features = ["tmo_id"]

        X = df[numeric_features + categorical_features].copy()
        y = df['y'].values

        # 4. Split Train/Test randomico
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        self.stdout.write(f"Train size: {len(X_train)}  Test size: {len(X_test)}")

        # 5. Pipeline Preprocessing
        numeric_transformer = "passthrough"
        categorical_transformer = Pipeline(steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("ordinal", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)),
        ])

        preprocessor = ColumnTransformer(
            transformers=[
                ("num", numeric_transformer, numeric_features),
                ("cat", categorical_transformer, categorical_features),
            ],
            remainder="drop",
            n_jobs=-1
        )

        cat_indices = list(range(len(numeric_features), len(numeric_features) + len(categorical_features)))

        # 6. Modello con BILANCIAMENTO CLASSI per risolvere le probabilità a 0%
        model = HistGradientBoostingClassifier(
            max_iter=300,
            learning_rate=0.05,
            early_stopping=True,
            random_state=42,
            #categorical_features=cat_indices,
            class_weight="balanced"  # <-- Questo forzerà probabilità alte per i lampioni a rischio!
        )

        clf = Pipeline(steps=[
            ("preprocess", preprocessor),
            ("model", model),
        ])

        self.stdout.write("Avvio training modello...")
        clf.fit(X_train, y_train)

        # 7. Valutazione
        proba = clf.predict_proba(X_test)[:, 1]
        if len(np.unique(y_test)) > 1:
            roc = roc_auc_score(y_test, proba)
            ap = average_precision_score(y_test, proba)
            self.stdout.write(f"ROC-AUC: {roc:.4f}")
            self.stdout.write(f"PR-AUC (Average Precision): {ap:.4f}")

        # 8. Salvataggio
        model_path = os.path.join(out_dir, f"risk_model_h60d.joblib")
        meta_path = os.path.join(out_dir, f"risk_model_h60d.meta.json")

        dump(clf, model_path)

        meta = {
            "numeric_features": numeric_features,
            "categorical_features": categorical_features,
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

        self.stdout.write(self.style.SUCCESS(f"Modello salvato: {model_path}"))