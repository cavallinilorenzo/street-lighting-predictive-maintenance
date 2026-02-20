# 💡 Smart City: Manutenzione Predittiva Illuminazione Pubblica

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-4.2+-092E20.svg?logo=django&logoColor=white)
![XGBoost](https://img.shields.io/badge/Machine%20Learning-XGBoost-F37626.svg)
![UI](https://img.shields.io/badge/UI-Cyberpunk_Theme-00f2ff.svg)

Progetto realizzato per l'**Hackathon SCIoTeM 2026**.

Questa piattaforma web trasforma la gestione dell'illuminazione pubblica in un processo proattivo tramite l'utilizzo del **Machine Learning**. Invece di intervenire a guasto avvenuto, il sistema prevede quando e perché un lampione si romperà, ottimizzando le risorse e migliorando la sicurezza della Smart City.

## ✨ Funzionalità Principali

* 🗺️ **Mappa Interattiva (Geolocalizzazione):** Visualizzazione dei lampioni su mappa (Folium) con pin colorati in base al rischio di guasto AI (Verde = Ottimo, Arancione = Attenzione, Rosso = Critico).
* 📊 **Dashboard Statistica:** Analisi dei dati storici, cause di guasto ricorrenti e distribuzione del rischio calcolato dall'AI tramite grafici interattivi (Chart.js).
* 🧠 **Explainable AI (XAI):** L'algoritmo fornisce una logica decisionale in linguaggio naturale (es. *"Forte usura temporale: l'asset è in funzione da oltre 9 anni"* oppure *"Stress termico: elevata potenza 150W"*) per rendere il modello comprensibile ai tecnici manutentori.
* ⏳ **Analisi di Sopravvivenza (Survival ML):** Modello predittivo avanzato basato su XGBoost AFT (Accelerated Failure Time) che stima i **giorni residui di vita** dell'hardware.
* 📄 **Reportistica PDF:** Generazione dinamica di Report Tecnici scaricabili per il singolo asset, completi di dati hardware, stime e link a Google Maps.
* 🎨 **UI/UX Cyberpunk:** Interfaccia utente moderna e accattivante, con tema dark, accenti neon (cyan, arancione, rosso) e **layout fully responsive.**

## 🛠️ Stack Tecnologico

### Backend & Database
* **Python**
* **Django** (Web Framework & ORM)
* **SQLite** (Database)
* **ReportLab** (Generazione PDF)

### Frontend
* **HTML5 & CSS3**
* **Bootstrap 5**
* **Chart.js** (Data Visualization)
* **Folium / Leaflet** (Mappe interattive GIS)

### Machine Learning (Pipeline)
* **XGBoost** (Survival:AFT per la stima dei giorni al guasto)
* **Scikit-learn** (Preprocessing, Pipeline)
* **Pandas & NumPy** (Data Manipulation)
* **Joblib** (Model serialization)

## 🤖 Come funziona il Modello di Machine Learning?

Il cuore del progetto non è un semplice classificatore binario, ma un modello di **Survival Analysis (Analisi di Sopravvivenza)**.

1. **Training (`train_lampioni_survival.py`):** Utilizziamo XGBoost AFT (`survival:aft`). Il modello apprende dai dati storici tenendo conto della "censura" (lampioni ancora funzionanti) e dei guasti effettivi, imparando la correlazione tra le feature fisiche (potenza, altezza, modello) e la curva di decadimento vitale.
2. **Inference (`preditcc_lampioni_survival.py`):** Calcoliamo i giorni stimati di vita residua per ogni asset attualmente in funzione.
3. **Scoring & XAI (`score_model.py`):** I giorni residui vengono mappati in una **Probabilità di Rischio a 60 Giorni** tramite una funzione di decadimento esponenziale inverso (`Rischio = exp(-giorni_residui / COSTANTE_DECADIMENTO)`). Questo garantisce un rischio dinamico e scientificamente fondato.
