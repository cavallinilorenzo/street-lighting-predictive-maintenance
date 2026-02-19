import csv

risk_file = "ml_artifacts\\risk_scores.csv"
pred_file = "macchine learning\\predizioneDelGesu.csv"
output_file = "risk_scores_con_residui.csv"

# dizionario arm_id -> pred_giorni_residui
pred_residui = {}

# leggo predizioneDelGesu
with open(pred_file, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        arm_id = row["arm_id"]
        residui = row["pred_giorni_residui"]
        pred_residui[arm_id] = residui

# leggo risk_scores e scrivo output
with open(risk_file, newline='', encoding='utf-8') as f_in, \
     open(output_file, "w", newline='', encoding='utf-8') as f_out:

    reader = csv.DictReader(f_in)
    fieldnames = ["arm_id", "risk_score", "pred_giorni_residui"]
    writer = csv.DictWriter(f_out, fieldnames=fieldnames)

    writer.writeheader()

    for row in reader:
        arm_id = row["arm_id"]

        if arm_id in pred_residui:  # solo quelli in comune
            writer.writerow({
                "arm_id": arm_id,
                "risk_score": row["risk_score"],
                "pred_giorni_residui": pred_residui[arm_id]
            })

print("File creato:", output_file)
