# Manual-CoT-Prompt-for-Text-to-SQL
## **Prompt chaining + CoT zero shot + db examples + steps + output format + rules**

This tecnique split the reasoning into *2 prompts*:
1. the first one provides the model with: a commented schema and a natural language question.
2. the second one provides the model with: the model's previous answer, real examples of data stored in the database and the same natural language question.
       
### **How the script *prompt1.py* works**
This script asks to manually select the path of the file containing the commented schema and to digit the question. It automatically generates the final prompt.

### **How the script *prompt2.py* works**
This script asks to manually select the path of the database (.sqlite), to digit the model's schema analysis, the question and text file's path for output. It automatically generates the final prompt in the text file selected.

### **How the script *SQLite_commentedSchema.py* works**
This script asks to manually select a text file containing the database schema and the folder (in the trainset folder) containing files .csv regarding the specific database i want to query.

## **Prompt chaining + CoT few shot + db examples + steps + riferimenti**

La tecnica comprende due prompt, entrambi interamente generati con gli script caricati nella cartella CoTFewShot+PromptChaining.
       
### **How the script *prompt1Generator.py* works**

Questo script, una volta runnato, chiederà di selezionare la cartella contenente i file CSV chiamata per ogni db "database_description". Successivamente chiederà di selezionare il file SQlite del database al quale ci stiamo riferendo. A questo punto verrà generato l'intero prompt al quale alla fine andranno solo inserite le due domande di esempio con i riferimenti ( esempio di riferimento: "VEHICULAR HIJACKING" refers to IUCR.secondary_description).

### **How the script *prompt2Generator.py* works**
Questo script chiederà di selezionare esattamente le stesse cose del prompt precedente. Va inserita la domanda riferita alla SQL GOLD sempre con i riferimenti come fatto vedere del paragrafo precedente. Una volta runnato e inserita la domanda, il prompt andra copiato e incollato inserendo sotto la voce {EXAMPLES} l'intera risposta al prompt1.

