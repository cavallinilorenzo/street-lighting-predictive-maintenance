import pandas as pd
import numpy as np
from pathlib import Path

INPUT_CSV = "lampioni_senza_2018.csv"
OUTPUT_CSV = "lampioni_senza_2018_puliti.csv"

print("Carico dataset...")
df = pd.read_csv(INPUT_CSV, dtype=str, low_memory=False)
print(len(df))
# pulizia base
df = df.apply(lambda s: s.str.strip() if s.dtype == "object" else s)
df.replace({"": np.nan, "NULL": np.nan, "null": np.nan, "NaN": np.nan, "nan": np.nan,0:np.nan,0.0:np.nan,"0.0":np.nan}, inplace=True)

df=df[["arm_altezza","arm_lmp_potenza_nominale","tmo_id"]].copy()

df.dropna(inplace=True)
df.to_csv(OUTPUT_CSV, index=False)