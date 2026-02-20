import pandas as pd
from datetime import datetime

input_file = "lampioni_attivi_coordinate.csv"
output_file = "dataset_con_vita.csv"

# leggi csv
df = pd.read_csv(input_file)

# data odierna
oggi = datetime.today()

# conversione colonna data (formato italiano giorno/mese/anno)
df["arm_data_ini"] = pd.to_datetime(df["arm_data_ini"], dayfirst=True, errors="coerce")

# calcolo giorni vita attuale
df["giorni_vita_attuale"] = (oggi - df["arm_data_ini"]).dt.days

# salva nuovo file
df.to_csv(output_file, index=False)

print("Creato file:", output_file)