# 🧪 Unit Test per SR_backend

Questa guida descrive come eseguire e comprendere i test unitari per il sistema di ricette SR_backend.

## 📁 File di Test

### `test_unit_simplified.py`
Test semplificati che **NON** richiedono dipendenze ML pesanti:
- ✅ Test dei modelli Pydantic (`RecipeDBSchema`, `Ingredient`)
- ✅ Test logica core di embedding (mockata)
- ✅ Test logica core database (mockata)
- ✅ Test workflow integrato (mockato)

### `test_unit_embedding_database.py`
Test completi che richiedono dipendenze ML:
- 🔧 Test completi di `RecipeEmbeddingEngine`
- 🔧 Test completi di `RecipeDatabase`
- ❗ **Richiede**: FlagEmbedding, sentence-transformers, chromadb, torch

## 🚀 Come Eseguire i Test

### Metodo 1: Script Automatico (Raccomandato)
```bash
# Test base senza coverage
python run_tests.py

# Test con output verboso
python run_tests.py --verbose

# Test con coverage report (richiede coverage.py)
python run_tests.py --coverage --verbose
```

### Metodo 2: Unittest Diretto
```bash
# Test semplificati (sempre funzionano)
python -m unittest test_unit_simplified.py -v

# Test completi (richiedono dipendenze ML)
python -m unittest test_unit_embedding_database.py -v
```

### Metodo 3: Test Singolo
```bash
# Test specifico
python -m unittest test_unit_simplified.TestRecipeModels.test_ingredient_creation -v
```

## 🔍 Struttura dei Test

### TestRecipeModels
Test per i modelli base Pydantic:
- `test_ingredient_creation()` - Validazione ingredienti
- `test_recipe_schema_creation()` - Schema ricetta completo  
- `test_recipe_schema_minimal()` - Schema ricetta minimale

### TestEmbeddingEngineCore
Test logica embedding (mockata):
- `test_create_recipe_text_structure()` - Generazione testo per embedding
- `test_preprocess_query_expansions()` - Espansione query culinarie

### TestDatabaseCore
Test logica database (mockata):
- `test_metadata_preparation()` - Preparazione metadati ChromaDB
- `test_search_filters_construction()` - Costruzione filtri di ricerca
- `test_search_results_formatting()` - Formattazione risultati

### TestIntegrationMocked
Test integrazione con mock:
- `test_full_recipe_workflow_mocked()` - Workflow completo simulato

## 📊 Output Esempio

```
🧪 Caricamento test...
✅ Caricato: test_unit_simplified

============================================================
🚀 ESECUZIONE TEST
============================================================

test_ingredient_creation ... ok
test_recipe_schema_creation ... ok
test_recipe_schema_minimal ... ok
test_create_recipe_text_structure ... ok
test_preprocess_query_expansions ... ok
test_metadata_preparation ... ok
test_search_filters_construction ... ok
test_search_results_formatting ... ok
test_full_recipe_workflow_mocked ... ok

----------------------------------------------------------------------
Ran 9 tests in 0.002s

============================================================
📋 RIASSUNTO ESECUZIONE
============================================================
Test eseguiti: 9
Successi: 9
Fallimenti: 0
Errori: 0
Saltati: 0
🎉 TUTTI I TEST SONO PASSATI!
```

## 🔧 Test con Dipendenze ML

Per eseguire i test completi che includono le librerie di Machine Learning:

### Installazione Dipendenze
```bash
# Installa dipendenze ML (richiede molto spazio)
pip install sentence-transformers
pip install FlagEmbedding
pip install chromadb
pip install torch
```

### Esecuzione Test Completi
```bash
# Una volta installate le dipendenze
python -m unittest test_unit_embedding_database.py -v
```

## 🎯 Copertura Test

### Funzionalità Coperte ✅
- Modelli Pydantic e validazione
- Logica di preparazione testi per embedding
- Espansione query culinarie italiane
- Preparazione metadati database
- Costruzione filtri di ricerca
- Formattazione risultati
- Gestione errori base

### Funzionalità da Testare 🔄
- Integrazione reale con modelli ML
- Performance embedding su dataset grandi
- Persistenza ChromaDB
- Gestione fallback tra modelli
- Cache LRU in condizioni reali

## 🐛 Risoluzione Problemi

### Errore "No module named 'FlagEmbedding'"
```bash
# Esegui solo i test semplificati
python -m unittest test_unit_simplified.py -v
```

### Errore validazione Pydantic
I test sono aggiornati per includere tutti i campi richiesti dal modello `RecipeDBSchema`.

### Errore import models
Assicurati di essere nella directory root del progetto:
```bash
cd /Users/eb/Documents/GitHub/SR_backed
```

## 📈 Metriche Test

### Test Semplificati
- **9 test cases**
- **Tempo esecuzione**: ~0.002s
- **Copertura**: Logica core business
- **Dipendenze**: Solo Python standard + Pydantic

### Test Completi
- **30+ test cases**
- **Tempo esecuzione**: ~2-5s (caricamento modelli)
- **Copertura**: Sistema completo
- **Dipendenze**: Full ML stack

## 🎓 Best Practices

1. **Esegui sempre i test semplificati** prima di fare commit
2. **Usa i test completi** per validazione finale
3. **Aggiungi test** per nuove funzionalità
4. **Mantieni i mock** aggiornati con l'implementazione reale
5. **Documenta comportamenti** edge case

## 🤝 Contribuire

Per aggiungere nuovi test:

1. **Test semplici**: Aggiungi a `test_unit_simplified.py`
2. **Test ML**: Aggiungi a `test_unit_embedding_database.py`
3. **Usa mock appropriati** per dipendenze esterne
4. **Segui le convenzioni** di naming esistenti
5. **Documenta test complessi** con commenti
