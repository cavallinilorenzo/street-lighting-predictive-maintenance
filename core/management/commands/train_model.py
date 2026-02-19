# core/management/commands/train_model.py

import json
import os
from dataclasses import dataclass
from datetime import timedelta

import numpy as np
import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand

from joblib import dump

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


@dataclass
class Config:
    horizon_days: int = 60
    test_days: int = 180
    windows_days: tuple = (30, 90, 180)
    replace_pattern_1: str = "sostituit"
    replace_pattern_2: str = "lampad"


def _parse_dates(series: pd.Series) -> pd.Series:
    # Formato nel vostro esempio: 1/1/2018, 31/12/2019 (day-first). [file:5]
    return pd.to_datetime(series, errors="coerce", dayfirst=True)


def _is_replace_lampada(tci_descr: pd.Series, cfg: Config) -> pd.Series:
    s = tci_descr.fillna("").astype(str).str.lower()
    return s.str.contains(cfg.replace_pattern_1, regex=False) & s.str.contains(cfg.replace_pattern_2, regex=False)


def _safe_float(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def build_examples(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    # Teniamo solo righe con data evento valida (quelle senza segnalazione non danno tempo t). [file:5]
    df = df.copy()
    df["sgn_data_inserimento"] = _parse_dates(df["sgn_data_inserimento"])
    df = df[df["sgn_data_inserimento"].notna()]

    if df.empty:
        raise ValueError("Nessun evento con sgn_data_inserimento valido: impossibile costruire esempi.")

    # Pulizia dtypes “leggeri”
    df["arm_id"] = pd.to_numeric(df["arm_id"], errors="coerce").astype("Int64")
    df = df[df["arm_id"].notna()]
    df["arm_id"] = df["arm_id"].astype(int)

    # Statiche (le ripetete su ogni riga; qui prendiamo la prima occorrenza per armatura)
    static_cols_num = [
        "arm_altezza",
        "arm_lunghezza_sbraccio",
        "arm_numero_lampade",
        "arm_lmp_potenza_nominale",
    ]
    static_cols_cat = ["tar_cod", "tmo_id", "tpo_cod"]

    for c in static_cols_num:
        df[c] = _safe_float(df[c])

    # Nota: tmo_id nel CSV è numerico; lo trattiamo come categoria (modello) convertendolo a stringa
    df["tmo_id"] = df["tmo_id"].astype("Int64").astype(str)

    static = (
        df.sort_values(["arm_id", "sgn_data_inserimento"])
          .groupby("arm_id", as_index=True)
          .first()[static_cols_num + static_cols_cat]
          .copy()
    )

    # Flag “replacement”
    df["is_replace"] = _is_replace_lampada(df.get("tci_descr", pd.Series(dtype=str)), cfg)

    # Costruzione esempi
    rows = []

    horizon = np.timedelta64(cfg.horizon_days, "D")
    windows = [np.timedelta64(w, "D") for w in cfg.windows_days]

    for arm_id, g in df.groupby("arm_id", sort=False):
        g = g.sort_values("sgn_data_inserimento")
        dates = g["sgn_data_inserimento"].values.astype("datetime64[ns]")
        is_rep = g["is_replace"].values.astype(bool)

        # Precalcolo “next replace date” per label (scan da destra)
        next_rep_date = np.full(len(dates), np.datetime64("NaT"), dtype="datetime64[ns]")
        nxt = np.datetime64("NaT")
        for i in range(len(dates) - 1, -1, -1):
            next_rep_date[i] = nxt
            if is_rep[i]:
                nxt = dates[i]

        # Stato per “last replace before t”
        last_replace = np.datetime64("NaT")

        # Statiche
        st = static.loc[arm_id] if arm_id in static.index else None

        for i in range(len(dates)):
            t = dates[i]

            # Feature SOLO dal passato: eventi con indice < i
            # Conteggi finestra: uso searchsorted su dates (ordinate) e considero [start, i)
            feats = {}
            for w, w_name in zip(windows, cfg.windows_days):
                start_t = t - w
                start_idx = np.searchsorted(dates, start_t, side="left")
                feats[f"cnt_events_{w_name}d"] = max(0, i - start_idx)

            if i == 0:
                feats["days_since_last_event"] = np.nan
            else:
                feats["days_since_last_event"] = float((t - dates[i - 1]) / np.timedelta64(1, "D"))

            if np.isnat(last_replace):
                feats["days_since_last_replace"] = np.nan
            else:
                feats["days_since_last_replace"] = float((t - last_replace) / np.timedelta64(1, "D"))

            # Label: esiste una sostituzione entro horizon dopo t?
            nr = next_rep_date[i]
            if np.isnat(nr):
                y = 0
                time_to_next_replace = np.nan
            else:
                delta = nr - t
                time_to_next_replace = float(delta / np.timedelta64(1, "D"))
                y = 1 if delta <= horizon else 0

            # Aggiorna last_replace DOPO aver calcolato le feature di questo t
            if is_rep[i]:
                last_replace = t

            row = {
                "arm_id": arm_id,
                "snapshot_date": pd.Timestamp(t).to_pydatetime(),
                "y": int(y),
                "time_to_next_replace_days": time_to_next_replace,
            }

            # Statiche
            if st is not None:
                for c in static_cols_num:
                    row[c] = st[c]
                row["tar_cod"] = st["tar_cod"]
                row["tmo_id"] = st["tmo_id"]
                row["tpo_cod"] = st["tpo_cod"]

            row.update(feats)
            rows.append(row)

    examples = pd.DataFrame(rows)

    # Pulizia: target e snapshot_date non null
    examples = examples[examples["snapshot_date"].notna()].copy()
    return examples


def train_pipeline(train_df: pd.DataFrame):
    target = "y"

    numeric_features = [
        "arm_altezza",
        "arm_lunghezza_sbraccio",
        "arm_numero_lampade",
        "arm_lmp_potenza_nominale",
        "cnt_events_30d",
        "cnt_events_90d",
        "cnt_events_180d",
        "days_since_last_event",
        "days_since_last_replace",
    ]
    categorical_features = ["tar_cod", "tmo_id", "tpo_cod"]

    X = train_df[numeric_features + categorical_features]
    y = train_df[target].astype(int).values

    numeric_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler(with_mean=True, with_std=True)),
    ])

    categorical_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ],
        remainder="drop",
    )

    model = LogisticRegression(
        max_iter=500,
        class_weight="balanced",
        n_jobs=1,
    )

    clf = Pipeline(steps=[
        ("preprocess", preprocessor),
        ("model", model),
    ])

    clf.fit(X, y)
    return clf, numeric_features, categorical_features


class Command(BaseCommand):
    help = "Allena un modello per stimare P(sostituzione lampada entro N giorni) usando eventi per armatura."

    def add_arguments(self, parser):
        parser.add_argument("--csv", type=str, required=True, help="Path al CSV completo (anche 1M righe).")
        parser.add_argument("--horizon-days", type=int, default=60, help="Orizzonte N giorni per la label.")
        parser.add_argument("--test-days", type=int, default=180, help="Ultimi X giorni come test set temporale.")
        parser.add_argument("--max-rows", type=int, default=None, help="Limita righe lette (debug).")
        parser.add_argument("--out-dir", type=str, default="ml_artifacts", help="Cartella output (relativa a BASE_DIR).")

    def handle(self, *args, **opts):
        cfg = Config(
            horizon_days=int(opts["horizon_days"]),
            test_days=int(opts["test_days"]),
        )

        csv_path = opts["csv"]
        max_rows = opts["max_rows"]

        out_dir = os.path.join(settings.BASE_DIR, opts["out_dir"])
        os.makedirs(out_dir, exist_ok=True)

        self.stdout.write(f"Leggo CSV: {csv_path}")
        usecols = [
            "arm_id",
            "arm_altezza",
            "arm_lunghezza_sbraccio",
            "arm_numero_lampade",
            "arm_lmp_potenza_nominale",
            "tar_cod",
            "tmo_id",
            "tpo_cod",
            "sgn_data_inserimento",
            "tci_descr",
        ]

        df = pd.read_csv(
            csv_path,
            usecols=usecols,
            nrows=max_rows,
            low_memory=False,
        )

        self.stdout.write(f"Righe lette: {len(df):,}")

        examples = build_examples(df, cfg)
        self.stdout.write(f"Esempi costruiti: {len(examples):,}")

        # Split temporale: ultimi cfg.test_days giorni come test
        examples["snapshot_date"] = pd.to_datetime(examples["snapshot_date"], errors="coerce")
        max_date = examples["snapshot_date"].max()
        split_date = max_date - pd.Timedelta(days=cfg.test_days)

        train_df = examples[examples["snapshot_date"] <= split_date].copy()
        test_df = examples[examples["snapshot_date"] > split_date].copy()

        self.stdout.write(f"Split date: {split_date.date()} (max snapshot: {max_date.date()})")
        self.stdout.write(f"Train: {len(train_df):,}  Test: {len(test_df):,}")
        self.stdout.write(f"Positive rate train: {train_df['y'].mean():.4f}  test: {test_df['y'].mean():.4f}")

        clf, num_feats, cat_feats = train_pipeline(train_df)

        # Eval
        X_test = test_df[num_feats + cat_feats]
        y_test = test_df["y"].astype(int).values
        proba = clf.predict_proba(X_test)[:, 1]

        roc = roc_auc_score(y_test, proba) if len(np.unique(y_test)) > 1 else float("nan")
        ap = average_precision_score(y_test, proba) if len(np.unique(y_test)) > 1 else float("nan")

        self.stdout.write(f"ROC-AUC: {roc:.4f}")
        self.stdout.write(f"PR-AUC (Average Precision): {ap:.4f}")

        # Salvataggio
        model_path = os.path.join(out_dir, f"risk_model_h{cfg.horizon_days}d.joblib")
        meta_path = os.path.join(out_dir, f"risk_model_h{cfg.horizon_days}d.meta.json")

        dump(clf, model_path)

        meta = {
            "horizon_days": cfg.horizon_days,
            "test_days": cfg.test_days,
            "split_date": str(split_date),
            "max_snapshot_date": str(max_date),
            "numeric_features": num_feats,
            "categorical_features": cat_feats,
            "csv_path": csv_path,
            "max_rows": max_rows,
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

        self.stdout.write(self.style.SUCCESS(f"Modello salvato: {model_path}"))
        self.stdout.write(self.style.SUCCESS(f"Metadata salvati: {meta_path}"))
