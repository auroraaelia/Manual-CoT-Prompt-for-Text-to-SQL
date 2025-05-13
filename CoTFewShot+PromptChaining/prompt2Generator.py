import sqlite3
import os
import csv
from tkinter import Tk, filedialog
from collections import defaultdict
import unicodedata
import re
import random


def safe_sql_identifier(name):
    """Formatta correttamente gli identificatori SQL con caratteri speciali"""
    return f'"{name}"' if not name.replace('_', '').isalnum() else name


def select_db_file():
    """Seleziona il file SQLite con dialog"""
    root = Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    return filedialog.askopenfilename(
        title="Seleziona database SQLite",
        filetypes=[("Database", "*.sqlite *.db *.sqlite3"), ("Tutti i file", "*.*")]
    )


def select_folder():
    """Seleziona la cartella con i file CSV"""
    root = Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    return filedialog.askdirectory(title="Seleziona cartella con file CSV")


def normalize_text(text):
    """Normalizza il testo per il matching"""
    if not text:
        return ""
    text = unicodedata.normalize('NFKD', str(text)).encode('ascii', 'ignore').decode('ascii')
    return ' '.join(text.strip().lower().split()).replace('_', ' ').replace('-', ' ')


def load_csv_descriptions(folder_path):
    """Carica le descrizioni dai file CSV"""
    descriptions = defaultdict(str)

    if not folder_path or not os.path.isdir(folder_path):
        return descriptions

    for filename in os.listdir(folder_path):
        if filename.lower().endswith('.csv'):
            try:
                with open(os.path.join(folder_path, filename), 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)

                    for row in reader:
                        original_column_name = row.get('original_column_name', '')
                        column_description = row.get('column_description', '').strip()
                        value_description = row.get('value_description', '').strip()

                        if original_column_name:
                            normalized_key = normalize_text(original_column_name)
                            full_desc = column_description
                            if value_description:
                                full_desc += f" ({value_description})" if full_desc else value_description
                            if full_desc:
                                descriptions[normalized_key] = full_desc

            except Exception as e:
                print(f"⚠️ Errore lettura file {filename}: {str(e)}")
                continue

    return descriptions


def format_value(value):
    """Formatta i valori per l'output"""
    if value is None:
        return "NULL"
    elif isinstance(value, bytes):
        return "<BLOB>"
    elif isinstance(value, str):
        return f'"{value.strip()}"'
    return str(value)


def is_valid_example(value):
    """Verifica se un valore è valido per essere mostrato come esempio"""
    return value is not None and value != 0 and value != '' and value != b''


def get_distinct_random_examples(cursor, table, column, limit=2):
    """Ottiene esempi casuali validi e distinti per una colonna"""
    query = f"SELECT DISTINCT {safe_sql_identifier(column)} FROM {safe_sql_identifier(table)} WHERE {safe_sql_identifier(column)} IS NOT NULL AND {safe_sql_identifier(column)} != '' AND {safe_sql_identifier(column)} != 0"

    if column.lower().endswith('id'):  # Evita di mostrare solo ID
        query += f" AND {safe_sql_identifier(column)} NOT LIKE '%ID%'"

    query += f" ORDER BY RANDOM() LIMIT {limit}"

    try:
        cursor.execute(query)
        results = cursor.fetchall()
        examples = []
        seen = set()

        for row in results:
            if is_valid_example(row[0]):
                formatted = format_value(row[0])
                if formatted not in seen:
                    seen.add(formatted)
                    examples.append(formatted)
                    if len(examples) == limit:
                        break

        # Se non abbiamo abbastanza esempi distinti, proviamo con una query più ampia
        if len(examples) < limit:
            query = f"SELECT {safe_sql_identifier(column)} FROM {safe_sql_identifier(table)} WHERE {safe_sql_identifier(column)} IS NOT NULL AND {safe_sql_identifier(column)} != '' AND {safe_sql_identifier(column)} != 0 ORDER BY RANDOM() LIMIT 100"
            cursor.execute(query)
            results = cursor.fetchall()

            for row in results:
                if is_valid_example(row[0]):
                    formatted = format_value(row[0])
                    if formatted not in seen:
                        seen.add(formatted)
                        examples.append(formatted)
                        if len(examples) == limit:
                            break

        return examples
    except Exception as e:
        print(f"⚠️ Errore durante il fetch per {table}.{column}: {str(e)}")
        return []


def analyze_database(db_path, descriptions):
    testo_introduttivo = (
        "I'm giving you the {CURRENT DB SCHEMA} with some {ADDITIONAL INFORMATIONS} "
        "which are about examples of instances and information about them. "
        "Then I give you two {EXAMPLES} of right queries belonging to the same database. "
        "Your task is to answer to the {QUESTION} with the correct SQL queries thinking step by step.\n"
    )
    print(testo_introduttivo)
    """Analizza il database con le descrizioni"""
    if not db_path:
        print("❌ Nessun file selezionato")
        return

    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cursor = conn.cursor()

        # 1. STAMPA LO SCHEMA COMPLETO (CREATE TABLE) SENZA COMMENTI
        print("{CURRENT DB SCHEMA}")
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables_schema = cursor.fetchall()

        for table in tables_schema:
            name, sql = table
            print(f"-- Tabella: {name}")
            print(f"{sql};")
            print("\n" + "-" * 50 + "\n")

        # =============================================
        # 2. ANALISI DETTAGLIATA DELLE TABELLE (CON COMMENTI)
        # =============================================

        print("{ADDITIONAL INFORMATION}")

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [row[0] for row in cursor.fetchall()]

        print(f"\n📊 Tabelle trovate: {len(tables)}\n")

        for table in tables:
            print(f" {table.upper()}")
            try:
                cursor.execute(f"PRAGMA table_info({safe_sql_identifier(table)});")
                columns_info = cursor.fetchall()
                column_names = [col[1] for col in columns_info]

                for col_name in column_names:
                    examples = get_distinct_random_examples(cursor, table, col_name)

                    if not examples:
                        continue

                    output = f"  {table}.{col_name}: {', '.join(examples)}"

                    normalized_col = normalize_text(col_name)
                    desc = descriptions.get(normalized_col, "")

                    if desc:
                        clean_desc = ' '.join(line.strip() for line in desc.splitlines() if line.strip())
                        output += f" (⚠️ {clean_desc})"

                    print(output)

                print("-" * 50 + "\n")

            except Exception as e:
                print(f"  ⚠️ Errore durante l'analisi tabella {table}: {str(e)}")
                print("-" * 50 + "\n")

        # =======================
        # OUTPUT TESTO DOPO ANALISI
        # =======================
        print("{EXAMPLES}\n")
        print("{QUESTION}\n")
        question = input(" ")

    except Exception as e:
        print(f"\n❌ Errore grave: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()
        input("\nPremi INVIO per uscire...")


if __name__ == "__main__":
    csv_folder = select_folder()
    descriptions = load_csv_descriptions(csv_folder)

    db_file = select_db_file()
    analyze_database(db_file, descriptions)
