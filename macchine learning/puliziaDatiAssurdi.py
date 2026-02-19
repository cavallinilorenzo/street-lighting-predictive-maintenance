import csv

# nome file csv (modificalo se serve)
file_path = "predizioneDelGesu.csv"

count_less_60 = 0
count_less_1200 = 0
count_greater_1200 = 0

with open(file_path, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)

    for row in reader:
        try:
            residui = float(row["pred_giorni_residui"])

            if residui < 60:
                count_less_60 += 1

            if residui < 365:
                count_less_1200 += 1

            if residui > 365:
                count_greater_1200 += 1

        except:
            # salta eventuali valori non validi
            continue

print("RISULTATI:")
print(f"pred_giorni_residui < 60: {count_less_60}")
print(f"pred_giorni_residui < 365: {count_less_1200}")
print(f"pred_giorni_residui > 365: {count_greater_1200}")
