import pandas as pd

# Carica il dataset (sostituisci con il tuo file)
df = pd.read_csv("aggiunta_giorni.csv")

# Raggruppa per tutte e 4 le colonne e conta le occorrenze
result = (
    df.groupby([
        "arm_altezza",
        "arm_lmp_potenza_nominale",
    ])
    .size()
    .reset_index(name="conteggio_righe")
)

# Mostra risultato
print(result)

# Se vuoi anche salvarlo su file
result.to_csv("combinazioni_conteggi.csv", index=False)