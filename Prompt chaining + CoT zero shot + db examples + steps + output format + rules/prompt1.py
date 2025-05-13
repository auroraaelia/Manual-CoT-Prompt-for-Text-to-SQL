def read_schema_file(file_path):
    """Legge il contenuto del file schema .txt"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def get_user_input(prompt):
    """Ottiene l'input dall'utente"""
    return input(prompt)

def generate_output(schema, question):
    """Genera l'output nel formato specificato"""
    output_template = """*Role*: You are a senior SQL expert trained to analyze databases' schema and data structures.

*Reference*:
You will be provided with:
1. A detailed database schema containing inline comments that provide an **authoritative semantic guidance**.
2. A natural language question related to the database.

*Task*: Your goal is to identify only the **essential columns** required to answer the given question.

*Reasoning Instructions*:
1. Break down the question into **logical components**.
2. Carefully read the **schema** and focus on **inline comments** for guidance.
3. **Map** each question component to specific schema columns.
4. Prioritize columns **directly aligned with comments**.
5. Exclude unnecessary tables or columns.

*Output:*
- Step-by-step reasoning.
- Final essential columns listed in a text block, as: table_name.column_name
(No SQL query or answer generation)

*Rules:*
- **Only** use the schema and comments.
- **No** external assumptions and knowledge.

*Database schema:*
{schema}

*Question:*
{question}"""

    return output_template.format(schema=schema, question=question)

def main():
    try:
        # Ottieni il percorso del file schema dall'utente
        schema_file = get_user_input("Inserisci il percorso del file schema .txt: ")
        
        # Leggi lo schema dal file
        schema_content = read_schema_file(schema_file)
        
        # Ottieni la domanda dall'utente
        user_question = get_user_input("Inserisci la tua question relativa al database: ")
        
        # Genera l'output
        output = generate_output(schema_content, user_question)
        
        # Stampa l'output
        print("\n" + output)
        
    except FileNotFoundError:
        print(f"Errore: File '{schema_file}' non trovato.")
    except Exception as e:
        print(f"Si è verificato un errore: {str(e)}")

if __name__ == "__main__":
    main()