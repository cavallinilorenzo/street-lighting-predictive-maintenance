# 💡 Smart Beam — Predictive Maintenance for Public Street Lighting

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-6.0.2-092E20.svg?logo=django&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-3.2.0-F37626.svg)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.8.0-F7931E.svg?logo=scikitlearn&logoColor=white)

> Developed for the **SCIoTeM 2026 Hackathon**.

📊 **[View the project presentation on Canva](https://canva.link/xd7wuplr4kh79ne)**

---

## Overview

**Smart Beam** is a web platform for managing public street lighting in a Smart City. It uses machine learning to move maintenance from a **reactive** model (repair after failure) to a **proactive** one (act before failure).

For each street light, the system estimates the **probability of failure within the next 60 days** and the **expected remaining lifetime**. Maintenance teams can use these estimates to prioritize work, plan resources, and improve urban safety.

## Key Features

| Feature | Description |
|---|---|
| 🗺️ **Interactive map** | Geolocated view of every street light, color-coded by predicted risk level. |
| 📈 **Analytics dashboard** | Historical analysis of recurring failure causes and maintenance interventions, built with Chart.js. |
| 🧠 **Explainable AI** | A plain-language explanation of each risk score, based on measurable factors such as service age, thermal stress (e.g., high nominal power), and the historical failure rate of similar models. |
| 📄 **Automated PDF reports** | Per-asset technical reports with hardware specifications, GPS coordinates, and predictive risk estimates. |
| 🛠️ **Fault reporting** | Operators can report physical issues found in the field (burnt-out lamp, structural damage, wear). Each report opens a maintenance ticket in the database. |

### Risk Levels

| Level | 60-day failure probability |
|---|---|
| 🟢 **Optimal** | < 25% |
| 🟡 **Warning** | 25% – 70% |
| 🔴 **Critical** | > 70% |

## Predictive Models

The predictive engine combines two complementary models, both trained on asset hardware features and historical maintenance records:

1. **60-day failure risk (classification)**
   A scikit-learn `HistGradientBoostingClassifier` with class balancing estimates the probability that a street light fails within a 60-day horizon. This probability is the asset's **risk score**.

2. **Remaining useful life (survival analysis)**
   An **XGBoost Accelerated Failure Time** model (`survival:aft`) estimates the remaining days before failure. Assets with no recorded failure are treated as right-censored observations, so they still contribute to training.

**Input features:** pole height (`arm_altezza`), nominal lamp power (`arm_lmp_potenza_nominale`), fixture model (`tmo_id`), and days in service (`giorni_osservati_finora`).

## Tech Stack

- **Backend & data:** Python, Django, SQLite, ReportLab (PDF generation)
- **Frontend:** HTML5, CSS3, Bootstrap 5, Chart.js, Folium / Leaflet (GIS maps)
- **Machine learning:** scikit-learn, XGBoost, pandas, NumPy, joblib

## Project Structure

```
street-lighting-predictive-maintenance/
├── core/                                  # Main Django app
│   ├── management/commands/               # CLI commands (data import, training, scoring)
│   ├── templates/core/                    # HTML templates (map, dashboard, asset detail, ...)
│   ├── models.py                          # Street light, maintenance and fault-report models
│   └── views.py                           # Views, risk classification, PDF generation
├── street_lighting_predictive_maintenance/ # Django project settings
├── macchine learning/                     # Data cleaning scripts and survival-model experiments
├── ml_artifacts/                          # Trained risk model and generated risk scores
├── lampioni_attivi_coordinate.csv         # Active street light inventory
├── lampioni_manutenzioni_coordinate.csv   # Historical maintenance records
├── db.sqlite3                             # Pre-populated SQLite database
└── requirements.txt
```

## Getting Started

### Prerequisites

- Python 3.10 or newer
- pip

### Installation

```bash
git clone https://github.com/cavallinilorenzo/street-lighting-predictive-maintenance.git
cd street-lighting-predictive-maintenance

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### Run the Application

The repository includes a pre-populated SQLite database, so you can start the server right away:

```bash
python manage.py migrate
python manage.py runserver
```

Then open <http://127.0.0.1:8000/>.

### Rebuilding the Data and Models (optional)

The pipeline is exposed as custom Django management commands:

```bash
# Import active street lights and historical maintenance records
python manage.py import_lampioneNuovo
python manage.py import_lampioneManutenzione

# Train the 60-day failure risk model
python manage.py train_model --csv <training_dataset.csv>

# Score the active inventory and update the database
python manage.py score_model \
    --model ml_artifacts/risk_model_h60d.joblib \
    --csv lampioni_attivi_coordinate.csv
```

The survival model and data-preparation scripts are in the `macchine learning/` directory.

## Main Routes

| Route | Description |
|---|---|
| `/` | Home page |
| `/mappa/` | Interactive risk map |
| `/statistiche/` | Analytics dashboard |
| `/asset/<id>/` | Asset detail with explainable risk assessment |
| `/asset/<id>/pdf/` | Downloadable PDF report |
| `/dettaglio-rischio/<level>/` | Assets filtered by risk level |
| `/admin/` | Django admin |

## Presentation

The full project presentation, covering the problem, approach, and results, is available on Canva:
👉 **[https://canva.link/xd7wuplr4kh79ne](https://canva.link/xd7wuplr4kh79ne)**

---

<p align="center">Made with 💡 for the SCIoTeM 2026 Hackathon</p>
