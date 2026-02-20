# predict_lampioni_survival.py
# Uso:
#   python predict_lampioni_survival.py input.csv output.csv
#
# Input CSV deve contenere almeno queste colonne:
#   arm_altezza, arm_lmp_potenza_nominale, tmo_id, giorni_osservati_finora
#
# Output aggiunge:
#   pred_giorni_al_guasto
#   pred_giorni_residui

import os
import json
import joblib
import numpy as np
import pandas as pd
import xgboost as xgb

MODEL_DIR = "model_lampioni_survival"

# Limiti "di sicurezza" per evitare numeri fuori scala (regola business)
MAX_YEARS = 5
MAX_DAYS = 365 * MAX_YEARS


def load_artifacts(model_dir: str = MODEL_DIR):
    preprocessor_path = os.path.join(model_dir, "preprocessor.joblib")
    model_path = os.path.join(model_dir, "xgb_aft.json")
    meta_path = os.path.join(model_dir, "meta.json")

    for p in [preprocessor_path, model_path, meta_path]:
        if not os.path.exists(p):
            raise FileNotFoundError(f"File mancante: {p}")

    preprocessor = joblib.load(preprocessor_path)

    booster = xgb.Booster()
    booster.load_model(model_path)

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    feature_cols = meta.get("feature_cols")
    if not feature_cols:
        raise ValueError("meta.json non contiene 'feature_cols'")

    return preprocessor, booster, feature_cols


def prepare_features(df: pd.DataFrame, feature_cols):
    """
    - Verifica colonne
    - Converte numeriche a float (NaN gestito)
    - tmo_id resta categorica (object)
    - Converte pd.NA -> np.nan per compatibilità sklearn
    """
    missing = [c for c in feature_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Mancano colonne richieste: {missing}")

    X = df[feature_cols].copy()

    # pd.NA -> np.nan (evita errore boolean value of NA is ambiguous)
    X = X.replace({pd.NA: np.nan})

    # Numeriche: float
    for c in ["arm_altezza", "arm_lmp_potenza_nominale", "giorni_osservati_finora"]:
        X[c] = pd.to_numeric(X[c], errors="coerce").astype(float)

    # tmo_id: categorica (object). NON usare dtype pandas "string"
    X["tmo_id"] = X["tmo_id"].astype(object)

    # warning per osservati <= 0
    bad_obs = X["giorni_osservati_finora"].isna() | (X["giorni_osservati_finora"] <= 0)
    return X, int(bad_obs.sum())


def predict_days(booster: xgb.Booster, X_transformed):
    """
    Predizione robusta:
    - XGBoost AFT spesso predice una quantità in log-scala (dipende da versione/config).
    - Usiamo una euristica semplice: se la mediana è "piccola", interpretiamo come log-tempo e facciamo exp.
    - Applichiamo comunque un cap MAX_DAYS per evitare valori assurdi in output.
    """
    dmat = xgb.DMatrix(X_transformed)
    pred_raw = booster.predict(dmat)

    # Heuristica log-vs-days:
    # - se pred_raw è log-tempo, tipicamente sta nell'ordine 0..20
    # - se fosse giorni, starebbe spesso a centinaia/migliaia
    med = float(np.median(pred_raw))

    if med <= 50.0:
        # interpretazione: log(giorni)
        pred_days = np.exp(np.clip(pred_raw, -20, 20))  # exp(20)~4.85e8
    else:
        # interpretazione: già in giorni
        pred_days = pred_raw

    # cap fisso business per output
    pred_days = np.clip(pred_days, 0, MAX_DAYS)

    return pred_days, pred_raw, med


def predict_file(input_csv: str, output_csv: str, chunksize: int = 200_000):
    preprocessor, booster, feature_cols = load_artifacts()

    first = True
    total_rows = 0
    total_bad_obs = 0
    printed_header = False

    for chunk in pd.read_csv(input_csv, chunksize=chunksize):
        X, bad_obs = prepare_features(chunk, feature_cols)
        total_bad_obs += bad_obs

        X_t = preprocessor.transform(X)
        pred_days, pred_raw, med = predict_days(booster, X_t)

        # stampa diagnostica una sola volta
        if not printed_header:
            print(f"Diagnostica: mediana pred_raw={med:.4f}  (log-tempo se <=50)")
            print(f"pred_raw min/median/max = {float(np.min(pred_raw)):.4f} / {float(np.median(pred_raw)):.4f} / {float(np.max(pred_raw)):.4f}")
            print(f"pred_days min/median/max = {float(np.min(pred_days)):.2f} / {float(np.median(pred_days)):.2f} / {float(np.max(pred_days)):.2f}")
            printed_header = True

        out = chunk.copy()
        out["pred_giorni_al_guasto"] = pred_days

        obs = pd.to_numeric(out["giorni_osservati_finora"], errors="coerce")
        out["pred_giorni_residui"] = (out["pred_giorni_al_guasto"] - obs).clip(lower=0)

        out.to_csv(output_csv, index=False, mode="w" if first else "a", header=first)
        first = False

        total_rows += len(chunk)
        print(f"Predette {total_rows} righe...")

    if total_bad_obs > 0:
        print(
            f"⚠️ {total_bad_obs} righe hanno giorni_osservati_finora NaN o <= 0. "
            "Queste righe possono avere output meno affidabile."
        )

    print(f"\n✅ Output salvato in: {output_csv}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        raise SystemExit("Uso: python predict_lampioni_survival.py input.csv output.csv")

    inp, outp = sys.argv[1], sys.argv[2]
    predict_file(inp, outp, chunksize=200_000)
