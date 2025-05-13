import os
import csv
from tkinter import Tk, filedialog
from collections import defaultdict
import unicodedata
import re

def normalize(text):
    if not text:
        return ""
    text = unicodedata.normalize('NFKD', text.strip().lower()).encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'[\s\-_]+', ' ', text)

def load_csv_descriptions(folder_path):
    """Carica descrizioni normalizzate da tutti i file CSV nella cartella"""
    descriptions = defaultdict(str)
    
    for filename in os.listdir(folder_path):
        if filename.lower().endswith('.csv'):
            with open(os.path.join(folder_path, filename), 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    column = normalize(row.get('original_column_name', ''))
                    desc = row.get('column_description', '').strip().replace('\n', ' ')  # Remove newlines
                    val_desc = row.get('value_description', '').strip().replace('\n', ' ')  # Remove newlines
                    full_desc = desc
                    if val_desc:
                        full_desc += f" ({val_desc})"
                    if column and full_desc:
                        descriptions[column] = full_desc
    return descriptions

def select_schema_file():
    root = Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    return filedialog.askopenfilename(title="Seleziona file schema .txt", filetypes=[("File di testo", "*.txt")])

def select_csv_folder():
    root = Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    return filedialog.askdirectory(title="Seleziona cartella con CSV")

def append_comments_to_schema(schema_text, descriptions):
    output = []
    for line in schema_text.splitlines():
        match = re.match(r'^\s*("?[\w\s\[\]\-]+"?)\s+[\w()]+.*?(,?)\s*$', line)
        if match and not line.strip().lower().startswith(("create table", "foreign key", "primary key")):
            col_name = normalize(match.group(1).strip('"'))
            comment = descriptions.get(col_name)
            if comment:
                comment = comment.replace("'", "’")  # Evita conflitti con apici SQL
                line = f"{line} -- '{comment}'"
        output.append(line)
    return "\n".join(output)

def main():
    print("📄 Seleziona lo schema .txt")
    schema_path = select_schema_file()
    print("📂 Seleziona la cartella con i file .csv")
    csv_folder = select_csv_folder()

    if not schema_path or not csv_folder:
        print("❌ Selezione annullata.")
        return

    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_text = f.read()

    descriptions = load_csv_descriptions(csv_folder)
    updated_schema = append_comments_to_schema(schema_text, descriptions)

    # Sovrascrive il file con i commenti
    with open(schema_path, 'w', encoding='utf-8') as f:
        f.write(updated_schema)

    print("✅ File aggiornato con commenti descrittivi.")

if __name__ == "__main__":
    main()
