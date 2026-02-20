import pandas as pd
import numpy as np
from pathlib import Path

INPUT_CSV = "lampioni_senza_2018.csv"
OUTPUT_CSV = "aggiunta_giorni.csv"

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
df["arm_data_fin"] = parse_date(df["arm_data_fin"])
df["sgn_data_inserimento"] = parse_date(df["sgn_data_inserimento"])

df.replace({"": np.nan, "NULL": np.nan, "null": np.nan, "NaN": np.nan, "nan": np.nan,0:np.nan,0.0:np.nan,"0.0":np.nan}, inplace=True)


# =========================
# CALCOLO DIFFERENZA GIORNI
# =========================
df["giorni_guasto"] = (
    df["sgn_data_inserimento"] - df["arm_data_ini"]
).dt.days

df["giorni_vita_attuale"]=(df["arm_data_fin"] - df["arm_data_ini"]).dt.days

df=df[df["giorni_vita_attuale"]<=df["giorni_guasto"]].copy()
#df["giorni_vita_attuale"] = np.where(df["giorni_vita_attuale"]>df["giorni_guasto"], df["giorni_guasto"], df["giorni_vita_attuale"])
# se non esiste segnalazione → 0



# convertiamo in intero
#df["giorni_guasto"] = df["giorni_guasto"].astype(int)
#df["giorni_guasto"] = df["giorni_guasto"].dropna()
#df=df[["arm_id","arm_altezza","arm_lmp_potenza_nominale","tmo_id","giorni_guasto"]].copy()

# =========================
# SAVE
# =========================


df = df[df["giorni_guasto"] >= 0].copy()
df=df[["arm_altezza","arm_lmp_potenza_nominale","tmo_id","giorni_guasto","giorni_vita_attuale"]].copy()
df.replace({"arm_altezza": {"NULL": 0, "null": 0, "NaN": 0, "nan": 0,"":0,np.nan:0}}, inplace=True)
df.dropna(inplace=True)

df.to_csv(OUTPUT_CSV, index=False)


print(f"\nFile creato: {Path(OUTPUT_CSV).resolve()}")
print("Colonna 'giorni_guasto' aggiunta.")
