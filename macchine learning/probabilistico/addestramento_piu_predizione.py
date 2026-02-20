import argparse
import joblib
import numpy as np
import pandas as pd

#python addestramento_piu_predizione.py --train_csv aggiunta_giorni.csv --predict_csv dataset_con_vita.csv --out_csv ..\..\output.csv --horizon 40

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss


HORIZON_DEFAULT = 200

# 75 migliore

def build_target(df: pd.DataFrame, horizon_days: int) -> pd.DataFrame:
    """
    Crea target_60gg = 1 se il lampione (dato lo stato attuale) si guasta entro horizon_days.
    target_60gg = (giorni_guasto - giorni_vita_attuale) <= horizon_days
    """
    required = ["giorni_vita_attuale", "giorni_guasto"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Mancano colonne obbligatorie: {missing}")

    df = df.copy()
    df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=required)

    # vincoli minimi di coerenza
    df = df[(df["giorni_vita_attuale"] >= 0) & (df["giorni_guasto"] >= 0)]
    df = df[df["giorni_guasto"] >= df["giorni_vita_attuale"]]  # evita casi impossibili

    remaining = df["giorni_guasto"] - df["giorni_vita_attuale"]
    df["target_60gg"] = (remaining <= horizon_days).astype(int)

    return df


def infer_categorical_columns(X: pd.DataFrame) -> list[str]:
    cat = [c for c in X.columns if X[c].dtype == object]
    # tmo_id spesso è un "id" discreto: trattalo come categoriale anche se è int
    if "tmo_id" in X.columns and "tmo_id" not in cat:
        cat.append("tmo_id")
    return cat


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train_csv", required=True, help="CSV training con feature + giorni_vita_attuale + giorni_guasto")
    parser.add_argument("--predict_csv", required=True, help="CSV da predire con feature + giorni_vita_attuale")
    parser.add_argument("--out_csv", default="predizioni_prob_60gg.csv", help="Output CSV con probabilità (0-100)")
    parser.add_argument("--model_out", default="modello_prob_guasto_60gg.joblib", help="File modello salvato")
    parser.add_argument("--horizon", type=int, default=HORIZON_DEFAULT, help="Orizzonte in giorni (default 60)")
    args = parser.parse_args()

    # ===== TRAIN =====
    df_train_raw = pd.read_csv(args.train_csv)
    df_train = build_target(df_train_raw, horizon_days=args.horizon)

    if len(df_train) < 200:
        raise RuntimeError(
            f"Troppe poche righe utili dopo la pulizia: {len(df_train)}. "
            f"Controlla NaN e vincoli giorni_guasto >= giorni_vita_attuale."
        )

    y = df_train["target_60gg"].astype(int)

    # NON usare giorni_guasto come feature: è leakage (è il futuro)
    X = df_train.drop(columns=["target_60gg", "giorni_guasto"], errors="ignore")

    # colonne
    categorical = infer_categorical_columns(X)
    numeric = [c for c in X.columns if c not in categorical]

    # preprocess
    cat_pipe = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])

    num_pipe = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    pre = ColumnTransformer(
        transformers=[
            ("cat", cat_pipe, categorical),
            ("num", num_pipe, numeric),
        ],
        remainder="drop",
    )

    # Modello semplice + robusto per dataset piccolo
    base = LogisticRegression(
        solver="liblinear",
        C=0.8,                  # regolarizzazione moderata (stabile con pochi dati)
        class_weight="balanced",# aiuta se target_60gg è sbilanciato
        max_iter=2000,
        random_state=42
    )

    pipe = Pipeline(steps=[("pre", pre), ("clf", base)])

    # split + calibrazione (probabilità più “vere”)
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    # cv=3 è un buon compromesso con 600 righe
    model = CalibratedClassifierCV(pipe, method="sigmoid", cv=3)
    model.fit(X_train, y_train)

    # metriche su validation
    proba_val = model.predict_proba(X_val)[:, 1]
    auc = roc_auc_score(y_val, proba_val)
    ap = average_precision_score(y_val, proba_val)
    brier = brier_score_loss(y_val, proba_val)

    print("=== Validation metrics (su holdout) ===")
    print(f"ROC-AUC: {auc:.4f}")
    print(f"PR-AUC:  {ap:.4f}")
    print(f"Brier:   {brier:.4f}")

    # salva modello
    joblib.dump(model, args.model_out)
    print(f"Modello salvato in: {args.model_out}")

    # ===== PREDICT =====
    df_pred = pd.read_csv(args.predict_csv)

    if "giorni_vita_attuale" not in df_pred.columns:
        raise ValueError("Nel predict_csv manca 'giorni_vita_attuale'.")

    # stesso schema feature del training (senza giorni_guasto)
    X_pred = df_pred.drop(columns=["giorni_guasto"], errors="ignore")

    proba = model.predict_proba(X_pred)[:, 1] * 100.0
    out = df_pred.copy()
    out[f"prob_guasto"] = np.round(proba, 2)

    out.to_csv(args.out_csv, index=False)
    print(f"Predizioni salvate in: {args.out_csv}")
    return args.out_csv
    # prendi colonna

if __name__ == "__main__":
    file_path = main()
    import pandas as pd
    import matplotlib.pyplot as plt


    # leggi csv
    df = pd.read_csv(file_path)
    print(df.head())
    # prendi colonna
    y = df[f"prob_guasto"]  # estrae "prob_guasto_entra_XXgg"

    # grafico
    plt.figure()
    plt.plot(y)

    plt.title("prob_guasto_entra_25gg")
    plt.ylabel("Probabilità guasto entro 25gg")
    plt.xlabel("Index")

    plt.show()