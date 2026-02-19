import pandas as pd
from pathlib import Path

INPUT_CSV = "..\\lampioni_attivi_coordinate.csv"
OUTPUT_CSV = "lampioni_senza_2018_attivi.csv"

print("Carico dataset...")
df = pd.read_csv(INPUT_CSV, dtype=str, low_memory=False)

# parse date robusto
df["arm_data_ini"] = pd.to_datetime(df["arm_data_ini"], errors="coerce", dayfirst=True)

# data da eliminare
data_da_rimuovere = pd.Timestamp("2018-01-01")

# filtro: tieni tutto tranne 1 gennaio 2018
df_filtrato = df[df["arm_data_ini"] != data_da_rimuovere].copy()

print(f"Righe originali: {len(df):,}")
print(f"Righe dopo rimozione: {len(df_filtrato):,}")

# salva file
df_filtrato.to_csv(OUTPUT_CSV, index=False)

print(f"\nFile salvato: {Path(OUTPUT_CSV).resolve()}")
