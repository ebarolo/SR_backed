# 🍳 Sistema di Ricerca Ricette con OpenAI Function Calling

Questo progetto implementa un sistema intelligente per cercare ricette in MongoDB Atlas utilizzando l'agentic function calling di OpenAI GPT-4o-mini.

## 📋 Funzionalità

- **Ricerca multi-criterio**: cerca per categoria, ingredienti, titolo, descrizione, tempo di cottura, etc.
- **Ricerca semantica**: utilizza embeddings per trovare ricette simili basandosi sul significato
- **Agent intelligente**: interpreta query in linguaggio naturale e sceglie automaticamente i parametri di ricerca ottimali
- **Dettagli completi**: recupera tutti i dettagli di una ricetta inclusi passi, consigli dello chef e info nutrizionali

## 🚀 Setup

### 1. Prerequisiti

- Python 3.8+
- Account MongoDB Atlas con un database di ricette
- API Key di OpenAI

### 2. Installazione

```bash
# Clona il repository
git clone <repository-url>
cd <repository-name>

# Installa le dipendenze
pip install -r requirements.txt
```

### 3. Configurazione

Crea un file `.env` nella directory principale:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# MongoDB Atlas Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
DB_NAME=your_database_name
COLLECTION_NAME=your_collection_name
```

### 4. Configurazione MongoDB Atlas (per ricerca vettoriale)

Per abilitare la ricerca semantica, crea un indice vettoriale su MongoDB Atlas:

1. Vai su MongoDB Atlas → Browse Collections → Search Indexes
2. Crea un nuovo Search Index di tipo "Vector Search"
3. Usa questa configurazione:

```json
{
  "mappings": {
    "dynamic": true,
    "fields": {
      "embedding": {
        "dimensions": 1536,
        "similarity": "cosine",
        "type": "knnVector"
      }
    }
  }
}
```

## 💻 Utilizzo

### Esempio Base

```python
from recipe_search_agent import search_with_agent

# Cerca antipasti con rana pescatrice
result = search_with_agent("antipasto con rana pescatrice")
print(result)
```

### Esempi di Query

Il sistema comprende query in linguaggio naturale come:

- "antipasto con rana pescatrice"
- "primi piatti vegetariani veloci" 
- "dolci senza glutine"
- "ricette con pomodori e basilico"
- "piatto elegante per una cena romantica"
- "qualcosa di veloce per pranzo, massimo 30 minuti"

### Utilizzo Avanzato

```python
from recipe_search_agent_advanced import (
    search_recipes, 
    semantic_search_recipes,
    get_recipe_details
)

# Ricerca diretta per categoria e ingredienti
results = search_recipes(
    category="antipasto",
    ingredients=["rana pescatrice", "pomodorini"],
    max_total_time=45
)

# Ricerca semantica
semantic_results = semantic_search_recipes(
    "piatto di pesce raffinato per occasioni speciali",
    limit=5
)

# Dettagli completi di una ricetta
details = get_recipe_details("recipe_id_here", include_audio=True)
```

## 📁 Struttura dei File

- `recipe_search_agent.py` - Implementazione base con function calling
- `recipe_search_agent_advanced.py` - Versione avanzata con ricerca semantica
- `env.example` - Esempio di configurazione
- `requirements.txt` - Dipendenze Python
- `DB/schemaCollection.json` - Schema della collection MongoDB

## 🔧 Come Funziona

1. **Interpretazione Query**: L'agent OpenAI analizza la richiesta dell'utente
2. **Selezione Funzione**: Sceglie automaticamente la funzione più appropriata:
   - `search_recipes` per ricerche specifiche
   - `semantic_search_recipes` per ricerche più complesse
   - `get_recipe_details` per dettagli specifici
3. **Esecuzione Query**: La funzione esegue la query su MongoDB
4. **Formattazione Risposta**: L'agent formatta i risultati in modo user-friendly

## 🎯 Function Calling di OpenAI

Il sistema utilizza le seguenti funzioni:

### search_recipes
Cerca ricette basandosi su criteri specifici:
- `category`: categoria della ricetta (antipasto, primo, secondo, dolce)
- `ingredients`: lista di ingredienti richiesti
- `title_contains`: testo da cercare nel titolo
- `max_total_time`: tempo massimo di preparazione + cottura

### semantic_search_recipes
Ricerca semantica usando embeddings:
- `query`: query in linguaggio naturale
- `limit`: numero massimo di risultati

### get_recipe_details
Recupera tutti i dettagli di una ricetta:
- `recipe_id`: ID della ricetta
- `include_audio`: se includere link audio e caption

## 🐛 Troubleshooting

### Errore di connessione MongoDB
- Verifica che l'URI di MongoDB sia corretto
- Controlla che il tuo IP sia nella whitelist di MongoDB Atlas

### Errore API OpenAI
- Verifica che l'API key sia valida
- Controlla di avere crediti sufficienti

### Ricerca vettoriale non funziona
- Assicurati di aver creato l'indice vettoriale su MongoDB Atlas
- Verifica che il campo `embedding` contenga vettori validi

## 📝 Note

- Il sistema rimuove automaticamente i campi `embedding` dalle risposte per ridurre la dimensione
- La ricerca vettoriale richiede che le ricette abbiano embeddings pre-calcolati
- Per migliori performance, indicizza i campi più utilizzati nelle ricerche

## 🤝 Contributi

Sentiti libero di aprire issue o pull request per migliorare il sistema! 