import pandas as pd
import numpy as np
from datetime import timedelta
import random
import sys

def correggi_date_manutenzione(input_file, output_file):
    print(f"--- Elaborazione file: {input_file} ---")

    # 1. Caricamento Intelligente (Prova Virgola, poi Punto e Virgola)
    try:
        # Tentativo 1: Virgola (Standard CSV)
        df = pd.read_csv(input_file, sep=',')
        if len(df.columns) < 2:
            # Se trova 1 sola colonna, probabilmente era punto e virgola
            print("Separatore ',' non ha funzionato, provo con ';'...")
            df = pd.read_csv(input_file, sep=';')
            
    except Exception as e:
        print(f"Errore critico apertura file: {e}")
        return

    # Pulizia nomi colonne (rimuove spazi invisibili)
    df.columns = df.columns.str.strip()
    
    print(f"Colonne rilevate correttamente: {len(df.columns)}")

    # Verifica nome colonna target
    col_target = 'sgn_data_inserimento'
    if col_target not in df.columns:
        print(f"ERRORE: Colonna '{col_target}' non trovata.")
        print(f"Ecco le colonne che vedo: {df.columns.tolist()}")
        return

    # 2. Conversione Date
    # arm_data_ini/fin sono in formato italiano (01/01/2018)
    cols_arm = ['arm_data_ini', 'arm_data_fin']
    for col in cols_arm:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')

    # sgn_data_inserimento
    # Nota: se il file è misto, pd.to_datetime con errors='coerce' gestisce sia / che -
    df[col_target] = pd.to_datetime(df[col_target], dayfirst=True, errors='coerce')

    # Funzione per data random
    def random_date(start, end):
        if pd.isnull(start) or pd.isnull(end):
            return start
        
        # Evita date future se la fine concessione è lontana
        limit_end = min(end, pd.Timestamp.now())
        
        if limit_end <= start:
            return start

        delta = limit_end - start
        int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
        
        if int_delta <= 0: return start
            
        random_second = random.randrange(int_delta)
        return start + timedelta(seconds=random_second)

    # 3. Logica di correzione
    def check_and_fix(row):
        start = row['arm_data_ini']
        end = row['arm_data_fin']
        current = row[col_target]

        if pd.isnull(start) or pd.isnull(end) or pd.isnull(current):
            return current

        # Se la data è valida (tra inizio e fine), la teniamo
        if start <= current <= end:
            return current
        else:
            # Altrimenti random
            return random_date(start, end)

    print("Analisi coerenza date in corso...")
    df[col_target] = df.apply(check_and_fix, axis=1)

    # 4. Formattazione Output
    # Uniformiamo tutto in formato italiano gg/mm/aaaa
    
    # Data con orario
    df[col_target] = df[col_target].dt.strftime('%d/%m/%Y %H:%M:%S')
    
    # Date senza orario
    for col in cols_arm:
        if col in df.columns:
            df[col] = df[col].dt.strftime('%d/%m/%Y')

    # Salvataggio (Usiamo la VIRGOLA per coerenza con l'input rilevato)
    df.to_csv(output_file, index=False, sep=',')
    print(f"Fatto! File salvato come: {output_file}")

# --- ESECUZIONE ---
nome_file_input = 'lampioni_manutenzione_coordinate.csv'
nome_file_output = 'lampioni_corretti.csv'

correggi_date_manutenzione(nome_file_input, nome_file_output)