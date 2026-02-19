import os
import json
import joblib
import numpy as np
import pandas as pd
import xgboost as xgb

MODEL_DIR = "model_lampioni_survival"


def load_artifacts(model_dir: str = MODEL_DIR):
    preprocessor_path = os.path.join(model_dir, "preprocessor.joblib")
    model_path = os.path.join(model_dir, "xgb_aft.json")
    meta_path = os.path.join(model_dir, "meta.json")

    if not os.path.exists(preprocessor_path):
        raise FileNotFoundError(f"Non trovo {preprocessor_path}")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Non trovo {model_path}")
    if not os.path.exists(meta_path):
        raise FileNotFoundError(f"Non trovo {meta_path}")

    preprocessor = joblib.load(preprocessor_path)

    booster = xgb.Booster()
    booster.load_model(model_path)

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    return preprocessor, booster, meta


def _validate_and_prepare_features(df: pd.DataFrame, feature_cols):
    # controlla colonne
    missing = [c for c in feature_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Mancano colonne richieste: {missing}")

    X = df[feature_cols].copy()

    # conversione numerica robusta (tmo_id può essere numerico: se è stringa, il preprocessor lo gestisce via imputazione/onehot)
    for c in ["arm_altezza", "arm_lmp_potenza_nominale", "giorni_osservati_finora"]:
        X[c] = pd.to_numeric(X[c], errors="coerce")

    # tmo_id: proviamo a numeric, ma se resta stringa va bene uguale
    X["tmo_id"] = pd.to_numeric(X["tmo_id"], errors="ignore")

    # sanity: giorni_osservati_finora deve essere > 0 (altrimenti i risultati possono diventare assurdi)
    # non blocchiamo tutto: mettiamo NaN e verrà imputato, ma stampiamo quante righe sono sospette.
    bad_obs = (pd.to_numeric(X["giorni_osservati_finora"], errors="coerce").fillna(-1) <= 0)
    n_bad = int(bad_obs.sum())
    return X, n_bad


def predict_file(input_csv: str, output_csv: str, chunksize: int = 200_000):
    preprocessor, booster, meta = load_artifacts()
    feature_cols = meta["feature_cols"]

    first = True
    total_rows = 0
    total_bad_obs = 0

    for chunk in pd.read_csv(input_csv, chunksize=chunksize):
        X, n_bad = _validate_and_prepare_features(chunk, feature_cols)
        total_bad_obs += n_bad

        X_t = preprocessor.transform(X)
        dmat = xgb.DMatrix(X_t)
        pred = booster.predict(dmat)

        out = chunk.copy()
        out["pred_giorni_al_guasto"] = pred

        # opzionale: giorni residui (mai negativi)
        obs = pd.to_numeric(out["giorni_osservati_finora"], errors="coerce")
        out["pred_giorni_residui"] = (out["pred_giorni_al_guasto"] - obs).clip(lower=0)

        out.to_csv(output_csv, index=False, mode="w" if first else "a", header=first)
        first = False

        total_rows += len(chunk)
        print(f"Predette {total_rows} righe...")

    if total_bad_obs > 0:
        print(
            f"⚠️ Attenzione: {total_bad_obs} righe avevano giorni_osservati_finora <= 0 o non numerico. "
            "Questo può peggiorare molto le predizioni. Controlla quella colonna."
        )

    print(f"\n✅ Output salvato in: {output_csv}")


def predict_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Utility se vuoi usare direttamente un DataFrame invece del file."""
    preprocessor, booster, meta = load_artifacts()
    feature_cols = meta["feature_cols"]

    X, n_bad = _validate_and_prepare_features(df, feature_cols)
    if n_bad > 0:
        print(f"⚠️ {n_bad} righe con giorni_osservati_finora <= 0 o non numerico")

    X_t = preprocessor.transform(X)
    dmat = xgb.DMatrix(X_t)
    pred = booster.predict(dmat)

    out = df.copy()
    out["pred_giorni_al_guasto"] = pred
    obs = pd.to_numeric(out["giorni_osservati_finora"], errors="coerce")
    out["pred_giorni_residui"] = (out["pred_giorni_al_guasto"] - obs).clip(lower=0)
    return out


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        raise SystemExit("Uso: python predict_lampioni_survival.py input.csv output.csv")

    inp, outp = sys.argv[1], sys.argv[2]
    predict_file(inp, outp, chunksize=200_000)
