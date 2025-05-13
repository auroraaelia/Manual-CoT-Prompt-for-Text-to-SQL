import sqlite3
import json
from typing import Dict, List, Union
from pathlib import Path

def get_db_path() -> str:
    """Chiede all'utente il percorso del database SQLite"""
    while True:
        db_path = input("Inserisci il percorso completo del database SQLite: ").strip()
        if Path(db_path).is_file() and (db_path.endswith('.sqlite') or db_path.endswith('.db')):
            return db_path
        print("Errore: File non trovato o estensione non valida (.sqlite o .db)")

def get_output_path() -> str:
    """Chiede all'utente dove salvare il prompt finale"""
    while True:
        output_path = input("Inserisci il percorso dove salvare il prompt finale (es: ./prompt.txt): ").strip()
        if output_path:
            try:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                return output_path
            except Exception as e:
                print(f"Errore nel percorso: {e}")
        print("Per favore inserisci un percorso valido")

def get_schema_analysis() -> str:
    """Chiede all'utente l'output del primo prompt"""
    print("\nIncolla l'output del primo prompt (formato 'table.column'):")
    print("Premi INVIO + Ctrl+D (Linux/Mac) o Ctrl+Z+Invio (Windows) per terminare:")
    lines = []
    while True:
        try:
            line = input()
            if line.strip():
                lines.append(line.strip())
        except EOFError:
            break
    return '\n'.join(lines)

def get_question() -> str:
    """Chiede all'utente la domanda originale"""
    return input("\nInserisci la domanda originale: ").strip()

def extract_clean_instances(db_path: str, columns_input: str) -> Dict[str, List[Union[str, int, float]]]:
    """Estrae i valori unici puliti per le colonne specificate"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Permette accesso alle colonne per nome
    cursor = conn.cursor()
    
    # Parsing delle colonne
    columns = [line.strip() for line in columns_input.split('\n') if line.strip()]
    table_columns = {}
    
    for col in columns:
        if '.' in col:
            table, column = col.split('.')[:2]
            table = table.strip('"')  # Rimuove eventuali doppi apici
            column = column.strip('"')
            if table not in table_columns:
                table_columns[table] = []
            if column not in table_columns[table]:
                table_columns[table].append(column)
    
    # Estrazione dati
    sample_data = {}
    
    for table, columns in table_columns.items():
        for column in columns:
            try:
                # Query per valori distinti, escludendo NULL e stringhe vuote
                query = f'SELECT DISTINCT "{column}" FROM "{table}" WHERE "{column}" IS NOT NULL AND "{column}" != "" ORDER BY "{column}"'
                cursor.execute(query)
                
                # Raccolta e pulizia dei valori
                values = []
                for row in cursor.fetchall():
                    val = row[0]
                    
                    # Conversione e pulizia del valore
                    if isinstance(val, str):
                        val = val.strip()
                        if not val:  # Salta stringhe vuote dopo lo strip
                            continue
                    
                    values.append(val)
                
                # Aggiungi al risultato solo se ci sono valori validi
                if values:
                    key = f"{table}.{column}"
                    sample_data[key] = values[:20]  # Limita a 50 valori per colonna
                    
            except sqlite3.Error as e:
                print(f"⚠️ Errore estraendo {table}.{column}: {e}")
                continue
    
    conn.close()
    return sample_data

def generate_final_prompt(schema_analysis: str, sample_data: Dict, question: str) -> str:
    """Genera il prompt completo per il modello"""
    # Creiamo una versione custom del JSON
    json_lines = ['{']
    
    for i, (key, values) in enumerate(sample_data.items()):
        # Formatta i valori come stringa su una riga
        values_str = ', '.join(f'"{v}"' if isinstance(v, str) else str(v) for v in values)
        line = f'    "{key}": [{values_str}]'
        
        # Aggiungi una virgola se non è l'ultimo elemento
        if i < len(sample_data) - 1:
            line += ','
        
        json_lines.append(line)
    
    json_lines.append('}')
    formatted_data = '\n'.join(json_lines)
    
    return f'''*Role*: You are a senior SQL expert specialized in writing **highly accurate**, **optimized**, **format-precise** and **schema-faithful** SQL queries.

*Reference*: You will be provided with:
1. Your previous schema analysis identifying the essential tables and columns.
2. Sample data instances for the selected columns (showing actual data **formatting** only, **never semantics**).
3. A natural language question related to the database.

*Task*: Write the most accurate SQL query that answers the question, ensuring:
  - **Full alignment** with the schema.
  - **Careful and accurate handling** of data formats **strictly as observed in the sample data**.
  - **Strict adherence** to SQLite syntax, functions, and conventions.

*Reasoning Step Instructions*:
1. Read the question again to remember exactly what information must be retrieved.
2. Identify only needed columns from the schema analysis.
3. **Meticulously examine** the provided sample data, **character by character** - do **not guess** or assume structure.
4. **Explicitly describe** the observed structure and formatting of the data in each relevant column.
5. Base all logic **only** on the **explicitly described sample data formats**.
6. Use only **SQLite-supported syntax and functions** that are appropriate for the observed data formats.
7. Describe your reasoning step-by-step and output the complete and precise SQL query.

*Output:*
  - Step-by-step reasoning.
  - The final and correct SQL query inside a proper SQL code block.

*Important notes*:
  - Treat every **sample value as definitive evidence**: do not rely at all on assumptions about common data formats or outside knowledge.
  - **Never assume standard formats** (e.g., ISO dates, numeric strings) without explicit validation from the sample data.
  - Avoid SQLite functions that don’t directly match the sample format unless a clear transformation (based on sample structure) is shown.
  - Base any format **parsing or filtering logic** **exclusively** on the actual structure of the sample values you have described. 
  - Sample data is provided **only to help you understand the structure and format of the fields**, not as source data for filtering.
  - **Do not use the sample values directly in the query** unless they are explicitly required by the question.

---

*Schema Analysis:*
{schema_analysis}

---

*Sample Data:*
{sample_data}

---

*Question:*  
{question}'''

def main():
    print("=== SQL Query Generator ===")
    print("Inserisci i dati richiesti:\n")
    
    # Input utente
    db_path = get_db_path()
    schema_analysis = get_schema_analysis()
    question = get_question()
    output_path = get_output_path()
    
    # Estrazione dati
    print("\n⏳ Estraggo i dati dal database...")
    sample_data = extract_clean_instances(db_path, schema_analysis)
    
    # Generazione prompt finale
    final_prompt = generate_final_prompt(schema_analysis, sample_data, question)
    
    # Salva su file
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_prompt)
        print(f"\n✅ Prompt salvato con successo in: {output_path}")
        
        # Anteprima del prompt
        print("\n--- ANTEPRIMA DEL PROMPT ---")
        print(final_prompt[:500] + "..." if len(final_prompt) > 500 else final_prompt)
        print("\n[...continua nel file...]")
    except Exception as e:
        print(f"\n❌ Errore durante il salvataggio: {e}")

if __name__ == "__main__":
    main()