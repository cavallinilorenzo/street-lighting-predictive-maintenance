# 💡 Smart City: Manutenzione Predittiva Illuminazione Pubblica

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-6.0.2-092E20.svg?logo=django&logoColor=white)
![XGBoost](https://img.shields.io/badge/Machine%20Learning-XGBoost-F37626.svg)
![UI](https://img.shields.io/badge/UI-Cyberpunk_Theme-00f2ff.svg)

Progetto realizzato per l'**Hackathon SCIoTeM 2026**.

Questo progetto è una piattaforma web sviluppata per ottimizzare la gestione dell'illuminazione pubblica all'interno di una Smart City. Utilizzando tecniche di Machine Learning, il sistema converte l'approccio alla manutenzione da reattivo (intervento a guasto avvenuto) a proattivo. L'obiettivo è stimare anticipatamente la probabilità di guasto dei lampioni, permettendo una pianificazione efficiente delle risorse e migliorando la sicurezza urbana.

## Funzionalità Principali
* **Mappa Interattiva (Geolocalizzazione)**: Visualizzazione dei lampioni su mappa. Ogni asset è contrassegnato da un livello di rischio di guasto (Ottimo, Attenzione, Critico) calcolato dall'algoritmo predittivo.
* **Dashboard Statistica**: Interfaccia dedicata all'analisi dei dati storici, che permette di monitorare le cause di guasto ricorrenti e le tipologie di interventi di manutenzione effettuati.
* **Reportistica Automatica**: Generazione dinamica di report tecnici in formato PDF per il singolo asset. Il documento include specifiche hardware, coordinate GPS e stime di rischio predittivo.
* **Explainable AI (XAI)**: L'applicativo fornisce una spiegazione testuale in linguaggio naturale per giustificare il livello di rischio, basandosi su parametri misurabili come l'età di servizio dell'impianto, lo stress termico (es. potenza elevata) e l'incidenza storica di guasti per modelli simili.
* **Sistema di Segnalazione Guasti**: Modulo dedicato agli operatori per la segnalazione di anomalie fisiche sul campo (es. lampada fulminata, danni strutturali o usura). Ogni segnalazione genera l'apertura di un ticket di manutenzione all'interno del database, consentendo un tracciamento puntuale degli interventi necessari.

## Modello Predittivo
* Il cuore del progetto si basa su tecniche di **Analisi di Sopravvivenza (Survival Analysis)**.
* Analizzando le caratteristiche hardware e lo storico dei guasti, il modello stima i giorni residui di vita di ciascun asset.
* Il risultato viene convertito in una probabilità di guasto a 60 giorni, fornendo un punteggio di rischio dinamico e scientificamente fondato, utile per stabilire le priorità operative.

## Stack Tecnologico
* **Backend e Database**: Python, Django (Web Framework), SQLite, ReportLab (per i PDF).
* **Frontend e UI**: HTML5, CSS3, Bootstrap 5, Chart.js (Data Visualization), Folium / Leaflet (Mappe interattive GIS).
* **Machine Learning**: Scikit-learn, XGBoost, Pandas, NumPy, Joblib.
