# core/management/commands/score_model.py

import os
from dataclasses import dataclass

import numpy as np
import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand
from joblib import load


@dataclass
class ScoreConfig:
    windows_days: tuple = (30, 90, 180)
    replace_pattern_1: str = "sostituit"
    replace_pattern_2: str = "lampad"


def _parse_dates(series: pd.Series) -> pd.Series:
    # Nel dataset esempio le date sono day-first tipo 1/1/2018. [file:5]
    return pd.to_datetime(series, errors="coerce", dayfirst=True)


def _safe_float(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def _is_replace_lampada(tci_descr: pd.Series, cfg: ScoreConfig) -> pd.Series:
    s = tci_descr.fillna("").astype(str).str.lower()
    return s.str.contains(cfg.replace_pattern_1, regex=False) & s.str.contains(cfg.replace_pattern_2, regex=False)


def _load_csv(path: str, usecols: list[str], max_rows: int | None = None) -> pd.DataFrame:
    df = pd.read_csv(path, usecols=usecols, nrows=max_rows, low_memory=False)
    df.columns = df.columns.str.strip()
    return df


def _extract_static(df: pd.DataFrame) -> pd.DataFrame:
    static_cols_num = [
        "arm_altezza",
        "arm_lunghezza_sbraccio",
        "arm_numero_lampade",
        "arm_lmp_potenza_nominale",
    ]
    static_cols_cat = ["tar_cod", "tmo_id", "tpo_cod"]

    for c in static_cols_num:
        if c in df.columns:
            df[c] = _safe_float(df[c])

    # tmo_id lo trattiamo come categoria (string) per matchare l'encoding del training
    if "tmo_id" in df.columns:
        df["tmo_id"] = pd.to_numeric(df["tmo_id"], errors="coerce").astype("Int64").astype(str)

    # Prendiamo una sola riga “rappresentativa” per armatura
    cols = [c for c in (static_cols_num + static_cols_cat) if c in df.columns]
    static = (
        df.sort_values(["arm_id"])
          .groupby("arm_id", as_index=True)
          .first()[cols]
          .copy()
    )
    return static


def _build_asof_features(events_df: pd.DataFrame, as_of: pd.Timestamp, cfg: ScoreConfig) -> pd.DataFrame:
    df = events_df.copy()

    df["sgn_data_inserimento"] = _parse_dates(df["sgn_data_inserimento"])
    df = df[df["sgn_data_inserimento"].notna()]

    df["arm_id"] = pd.to_numeric(df["arm_id"], errors="coerce").astype("Int64")
    df = df[df["arm_id"].notna()]
    df["arm_id"] = df["arm_id"].astype(int)

    df = df[df["sgn_data_inserimento"] <= as_of].copy()

    if df.empty:
        return pd.DataFrame(columns=["arm_id"])

    df["is_replace"] = _is_replace_lampada(df.get("tci_descr", pd.Series(dtype=str)), cfg)

    df = df.sort_values(["arm_id", "sgn_data_inserimento"])

    rows = []
    as_of64 = np.datetime64(as_of.to_datetime64())

    windows = [np.timedelta64(w, "D") for w in cfg.windows_days]

    for arm_id, g in df.groupby("arm_id", sort=False):
        dates = g["sgn_data_inserimento"].values.astype("datetime64[ns]")
        rep = g["is_replace"].values.astype(bool)

        last_event = dates[-1]
        days_since_last_event = float((as_of64 - last_event) / np.timedelta64(1, "D"))

        if rep.any():
            last_replace = dates[rep][-1]
            days_since_last_replace = float((as_of64 - last_replace) / np.timedelta64(1, "D"))
        else:
            days_since_last_replace = np.nan

        feats = {"arm_id": arm_id, "as_of_date": as_of.to_pydatetime()}
        for w, w_name in zip(windows, cfg.windows_days):
            start = as_of64 - w
            # count dates >= start (and <= as_of by construction)
            cnt = int(np.searchsorted(dates, as_of64, side="right") - np.searchsorted(dates, start, side="left"))
            feats[f"cnt_events_{w_name}d"] = cnt

        feats["days_since_last_event"] = days_since_last_event
        feats["days_since_last_replace"] = days_since_last_replace
        rows.append(feats)

    return pd.DataFrame(rows)


class Command(BaseCommand):
    help = "Calcola i risk score per armatura (probabilità di 'sostituito lampada' entro N giorni) e salva un CSV."

    def add_arguments(self, parser):
        parser.add_argument("--model", type=str, required=True, help="Path al modello .joblib salvato da train_model.")
        parser.add_argument("--csv-events", type=str, required=True, help="CSV con solo righe segnalazioni/eventi.")
        parser.add_argument("--csv-all", type=str, default=None, help="(Opzionale) CSV completo per includere armature senza eventi.")
        parser.add_argument("--as-of", type=str, default=None, help="Data as-of (YYYY-MM-DD). Default: max sgn_data_inserimento eventi.")
        parser.add_argument("--out-csv", type=str, default="ml_artifacts/risk_scores.csv", help="Output CSV relativo a BASE_DIR.")
        parser.add_argument("--max-rows", type=int, default=None, help="Limita righe lette (debug).")
        parser.add_argument("--top-n", type=int, default=50, help="Stampa a schermo le top N armature per rischio.")

    def handle(self, *args, **opts):
        cfg = ScoreConfig()

        model_path = opts["model"]
        events_path = opts["csv_events"]
        all_path = opts["csv_all"]
        max_rows = opts["max_rows"]

        out_csv = os.path.join(settings.BASE_DIR, opts["out_csv"])
        os.makedirs(os.path.dirname(out_csv), exist_ok=True)

        self.stdout.write(f"Carico modello: {model_path}")
        clf = load(model_path)

        # Colonne minime (se mancano, pandas alza errore: meglio scoprirlo subito)
        static_cols_num = ["arm_altezza", "arm_lunghezza_sbraccio", "arm_numero_lampade", "arm_lmp_potenza_nominale"]
        static_cols_cat = ["tar_cod", "tmo_id", "tpo_cod"]

        usecols_events = ["arm_id", "sgn_data_inserimento", "tci_descr"] + static_cols_num + static_cols_cat
        usecols_events = list(dict.fromkeys(usecols_events))  # unique

        self.stdout.write(f"Leggo CSV eventi: {events_path}")
        events_df = _load_csv(events_path, usecols_events, max_rows=max_rows)

        # as-of
        events_df["sgn_data_inserimento"] = _parse_dates(events_df["sgn_data_inserimento"])
        max_event_date = events_df["sgn_data_inserimento"].max()

        if opts["as_of"]:
            as_of = pd.to_datetime(opts["as_of"], errors="raise")
        else:
            as_of = pd.to_datetime(max_event_date)

        if pd.isna(as_of):
            raise ValueError("Impossibile determinare as-of: sgn_data_inserimento è vuoto o non parseabile.")

        self.stdout.write(f"As-of date: {as_of.date()}")

        # Statiche: se csv-all presente, prendiamo statiche da lì per coprire anche armature senza eventi
        if all_path:
            self.stdout.write(f"Leggo CSV completo: {all_path}")
            usecols_all = ["arm_id"] + static_cols_num + static_cols_cat
            all_df = _load_csv(all_path, usecols_all, max_rows=None)
            all_df["arm_id"] = pd.to_numeric(all_df["arm_id"], errors="coerce").astype("Int64")
            all_df = all_df[all_df["arm_id"].notna()].copy()
            all_df["arm_id"] = all_df["arm_id"].astype(int)
            static = _extract_static(all_df)
        else:
            # fallback: statiche dalle righe eventi (copre solo armature con eventi)
            events_df["arm_id"] = pd.to_numeric(events_df["arm_id"], errors="coerce").astype("Int64")
            events_df = events_df[events_df["arm_id"].notna()].copy()
            events_df["arm_id"] = events_df["arm_id"].astype(int)
            static = _extract_static(events_df)

        # Feature dinamiche “as-of”
        dyn = _build_asof_features(events_df, as_of=as_of, cfg=cfg)

        # Unisco static + dyn; se csv-all, avrete armature senza dyn => riempite con 0/NaN
        base = static.reset_index().rename(columns={"index": "arm_id"})
        scored = base.merge(dyn, on="arm_id", how="left")

        # Fill per armature senza eventi (se csv-all)
        for w in cfg.windows_days:
            col = f"cnt_events_{w}d"
            if col in scored.columns:
                scored[col] = scored[col].fillna(0).astype(int)

        # days_since... lasciamo NaN: il modello (se avete SimpleImputer nel pipeline) gestirà.
        # Se NON avete imputer nel train_model, allora dovete fare fill qui.

        # Preparo X con le colonne attese dal train_model
        feature_cols = [
            "arm_altezza",
            "arm_lunghezza_sbraccio",
            "arm_numero_lampade",
            "arm_lmp_potenza_nominale",
            "tar_cod",
            "tmo_id",
            "tpo_cod",
            "cnt_events_30d",
            "cnt_events_90d",
            "cnt_events_180d",
            "days_since_last_event",
            "days_since_last_replace",
        ]

        missing = [c for c in feature_cols if c not in scored.columns]
        if missing:
            raise ValueError(f"Colonne mancanti per lo scoring: {missing}")

        X = scored[feature_cols].copy()

        proba = clf.predict_proba(X)[:, 1]
        scored["risk_score"] = proba
        scored["as_of_date"] = as_of.to_pydatetime()

        scored = scored.sort_values("risk_score", ascending=False)

        scored.to_csv(out_csv, index=False)
        self.stdout.write(self.style.SUCCESS(f"Salvato: {out_csv}  (righe: {len(scored):,})"))

        top_n = int(opts["top_n"])
        self.stdout.write(f"Top {top_n} armature per rischio:")
        self.stdout.write(scored[["arm_id", "risk_score"]].head(top_n).to_string(index=False))
