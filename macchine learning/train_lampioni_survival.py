import os
import json
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder

import xgboost as xgb


# ----------------------------
# CONFIG
# ----------------------------
RANDOM_STATE = 42

FEATURE_COLS = [
    "arm_altezza",
    "arm_lmp_potenza_nominale",
    "tmo_id",
    "giorni_osservati_finora",
]
TARGET_COL = "giorni_guasto"

MODEL_DIR = "model_lampioni_survival"
os.makedirs(MODEL_DIR, exist_ok=True)


def build_preprocessor() -> ColumnTransformer:
    """
    Preprocess robusto:
    - numeriche: imputazione mediana
    - tmo_id: categorica -> one-hot
    """
    categorical = ["tmo_id"]
    numeric = ["arm_altezza", "arm_lmp_potenza_nominale", "giorni_osservati_finora"]

    num_tf = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
    ])

    cat_tf = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=True)),
    ])

    return ColumnTransformer(
        transformers=[
            ("num", num_tf, numeric),
            ("cat", cat_tf, categorical),
        ],
        remainder="drop",
        sparse_threshold=0.3,
    )


def load_csv_sample(path: str, sample_rows: int = 600_000, chunksize: int = 200_000) -> pd.DataFrame:
    """
    Legge un campione dal CSV a chunk (ottimo con dataset enormi).
    Aumenta sample_rows se vuoi più dati per training.
    """
    chunks = []
    read = 0
    for chunk in pd.read_csv(path, chunksize=chunksize):
        chunks.append(chunk)
        read += len(chunk)
        if read >= sample_rows:
            break
    return pd.concat(chunks, ignore_index=True)


def clean_and_make_aft_bounds(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pulisce e crea i bounds per survival AFT.

    Definizioni:
    - guasto osservato: giorni_guasto > 0  -> lower = upper = giorni_guasto
    - censurato (attivo): giorni_guasto = 0 -> lower = giorni_osservati_finora, upper = +inf

    IMPORTANTISSIMO:
    - per i censurati giorni_osservati_finora deve essere > 0 e significare "da quanti giorni è in servizio/osservato".
    """
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]

    required = set(FEATURE_COLS + [TARGET_COL])
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Mancano colonne nel CSV: {sorted(missing)}")

    # Converti a numerico dove serve (vuoti -> NaN)
    for c in FEATURE_COLS + [TARGET_COL]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # Rimuovi righe senza target o senza giorni_osservati_finora
    df = df[df[TARGET_COL].notna()]
    df = df[df["giorni_osservati_finora"].notna()]

    # Event: 1 se guasto, 0 se censurato
    event = (df[TARGET_COL] > 0).astype(np.int8).values
    t_fail = df[TARGET_COL].astype(float).values
    t_obs = df["giorni_osservati_finora"].astype(float).values

    # Sanity check: censurati devono avere t_obs > 0
    bad_censored = (event == 0) & (t_obs <= 0)
    if np.any(bad_censored):
        # eliminiamo queste righe: altrimenti torni al problema dei valori assurdi
        df = df.loc[~bad_censored].copy()
        event = (df[TARGET_COL] > 0).astype(np.int8).values
        t_fail = df[TARGET_COL].astype(float).values
        t_obs = df["giorni_osservati_finora"].astype(float).values

    # Bounds AFT
    lower = np.where(event == 1, t_fail, t_obs)
    upper = np.where(event == 1, t_fail, np.inf)

    df["event"] = event
    df["label_lower_bound"] = lower
    df["label_upper_bound"] = upper

    # Extra sanity: lower deve essere > 0
    df = df[df["label_lower_bound"] > 0]

    return df


def train_model(csv_path: str) -> None:
    print(f"Using xgboost version: {xgb.__version__}")

    # 1) Carico campione e preparo bounds
    df = load_csv_sample(csv_path, sample_rows=600_000, chunksize=200_000)
    df = clean_and_make_aft_bounds(df)

    # 2) Split train/val (stratify su event per bilanciare)
    X = df[FEATURE_COLS]
    yL = df["label_lower_bound"].values.astype(np.float32)
    yU = df["label_upper_bound"].values.astype(np.float32)

    X_train, X_val, yL_train, yL_val, yU_train, yU_val = train_test_split(
        X, yL, yU,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=df["event"]
    )

    # 3) Preprocess
    preprocessor = build_preprocessor()
    Xtr = preprocessor.fit_transform(X_train)
    Xva = preprocessor.transform(X_val)

    # 4) DMatrix con bounds
    dtrain = xgb.DMatrix(Xtr)
    dtrain.set_float_info("label_lower_bound", yL_train)
    dtrain.set_float_info("label_upper_bound", yU_train)

    dval = xgb.DMatrix(Xva)
    dval.set_float_info("label_lower_bound", yL_val)
    dval.set_float_info("label_upper_bound", yU_val)

    # 5) Parametri modello AFT
    params = {
        "objective": "survival:aft",
        "eval_metric": "aft-nloglik",
        "tree_method": "hist",
        "max_depth": 6,
        "eta": 0.05,
        "subsample": 0.85,
        "colsample_bytree": 0.85,
        "lambda": 1.0,
        "alpha": 0.0,
        "aft_loss_distribution": "logistic",
        "aft_loss_distribution_scale": 1.0,
        "seed": RANDOM_STATE,
    }

    booster = xgb.train(
        params=params,
        dtrain=dtrain,
        num_boost_round=5000,
        evals=[(dtrain, "train"), (dval, "val")],
        early_stopping_rounds=200,
        verbose_eval=50,
    )

    # 6) Salvataggio artefatti
    joblib.dump(preprocessor, os.path.join(MODEL_DIR, "preprocessor.joblib"))
    booster.save_model(os.path.join(MODEL_DIR, "xgb_aft.json"))

    meta = {
        "feature_cols": FEATURE_COLS,
        "target_col": TARGET_COL,
        "objective": "survival:aft",
        "notes": "censored rows: lower=giorni_osservati_finora, upper=inf; failures: lower=upper=giorni_guasto",
        "xgboost_version": xgb.__version__,
    }
    with open(os.path.join(MODEL_DIR, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Modello salvato in: {MODEL_DIR}")
    print("   - preprocessor.joblib")
    print("   - xgb_aft.json")
    print("   - meta.json")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        raise SystemExit("Uso: python train_lampioni_survival.py /percorso/dataset.csv")
    train_model(sys.argv[1])
