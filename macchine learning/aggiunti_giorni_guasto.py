import pandas as pd
import numpy as np
from pathlib import Path

INPUT_CSV = "..\\lampioni_attivi_coordinate.csv"
OUTPUT_CSV = "datiPerPredict.csv"

print("Carico dataset...")
df = pd.read_csv(INPUT_CSV, dtype=str, low_memory=False)

# pulizia base
df = df.apply(lambda s: s.str.strip() if s.dtype == "object" else s)
df.replace({"": np.nan, "NULL": np.nan, "null": np.nan, "NaN": np.nan, "nan": np.nan}, inplace=True)

# =========================
# PARSE DATE ROBUSTO
# =========================
def parse_date(s):
    dt = pd.to_datetime(s, errors="coerce", format="%Y-%m-%d")
    mask = dt.isna() & s.notna()
    if mask.any():
        dt2 = pd.to_datetime(s[mask], errors="coerce", dayfirst=True)
        dt.loc[mask] = dt2
    return dt

df["arm_data_ini"] = parse_date(df["arm_data_ini"])
df["sgn_data_inserimento"] = parse_date(df["sgn_data_inserimento"])

# =========================
# CALCOLO DIFFERENZA GIORNI
# =========================
df["giorni_guasto"] = (
    df["sgn_data_inserimento"] - df["arm_data_ini"]
).dt.days



# se non esiste segnalazione → 0
df["giorni_guasto"] = df["giorni_guasto"].fillna(0)

df["giorni_osservati_finora"] = np.where(
    df["giorni_guasto"] == 0,
    (pd.Timestamp.today()-df["arm_data_ini"]).dt.days,
    df["giorni_guasto"]
)


# convertiamo in intero
df["giorni_guasto"] = df["giorni_guasto"].astype(int)
df=df[["arm_id","arm_altezza","arm_lmp_potenza_nominale","tmo_id","giorni_guasto","giorni_osservati_finora"]].copy()

# =========================
# SAVE
# =========================
df = df[df["giorni_guasto"] >= 0].copy()
df.to_csv(OUTPUT_CSV, index=False)

print(f"\nFile creato: {Path(OUTPUT_CSV).resolve()}")
print("Colonna 'giorni_guasto' aggiunta.")
