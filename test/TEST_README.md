# Test Suite per WeaviateSemanticEngine

## Panoramica

Questa suite di test copre tutte le funzionalità della classe `WeaviateSemanticEngine` per la gestione delle collection Weaviate e la ricerca semantica delle ricette.

## Struttura dei Test

### TestWeaviateSemanticEngine
Testa la classe principale con tutti i suoi metodi:

- **Inizializzazione**: Test di connessione e configurazione
- **Ricerca semantica**: Test delle funzioni di ricerca
- **Gestione collection**: Test di creazione e aggiornamento
- **Gestione ricette**: Test di aggiunta, eliminazione e recupero
- **Statistiche**: Test di monitoraggio collection

### TestQuickSemanticSearch
Testa la funzione di utilità per ricerca rapida.

### TestRecipeDBSchemaIntegration
Testa l'integrazione con lo schema Pydantic delle ricette.

## Esecuzione dei Test

### Esecuzione base
```bash
# Attiva virtual environment
source venv/bin/activate

# Esegui tutti i test
python -m pytest test_weaviate_engine.py -v

# Esegui con coverage
python -m pytest test_weaviate_engine.py --cov=RAG._weaviate --cov-report=html
```

### Esecuzione con filtri
```bash
# Solo test unitari
python -m pytest -m unit

# Solo test di integrazione
python -m pytest -m integration

# Escludi test lenti
python -m pytest -m "not slow"
```

## Coverage

Il test suite attuale copre **63%** del codice della classe `WeaviateSemanticEngine`.

### Aree coperte:
- ✅ Inizializzazione e connessione
- ✅ Ricerca semantica, per vettore e ibrida
- ✅ Creazione e gestione collection
- ✅ Aggiunta, aggiornamento e eliminazione ricette
- ✅ Recupero statistiche e info collection
- ✅ Gestione errori e eccezioni

### Aree da migliorare:
- 🔄 Test di integrazione con Weaviate reale
- 🔄 Test di performance con grandi dataset
- 🔄 Test di edge cases per validazione dati

## Mock e Fixtures

I test utilizzano mock completi per:
- Client Weaviate
- Collection Weaviate
- Risposte API Weaviate
- Oggetti RecipeDBSchema di esempio

## Dipendenze

- `pytest`: Framework di testing
- `pytest-cov`: Coverage reporting
- `unittest.mock`: Mocking framework
- `pydantic`: Validazione dati

## Note

- I test sono completamente isolati e non richiedono connessione Weaviate reale
- Tutti i mock sono configurati per simulare comportamenti realistici
- I test includono validazione di errori e edge cases
- Coverage report HTML generato in `htmlcov/`
