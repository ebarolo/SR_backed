# Gestione Errori OpenAI - Smart Recipe

## Panoramica

Sistema completo di gestione errori per le API OpenAI (Whisper, GPT-4, DALL-E) con messaggi user-friendly e retry intelligente.

## Modifiche Implementate

### 1. Nuovo Modulo: `utility/openai_errors.py`

Definisce eccezioni custom per errori OpenAI:

- **`OpenAIError`**: Classe base per tutti gli errori OpenAI
- **`QuotaExceededError`**: Quota API esaurita (429 insufficient_quota)
- **`RateLimitError`**: Rate limit superato (429)
- **`InvalidAPIKeyError`**: API key non valida (401)
- **`ServerError`**: Errore server OpenAI (5xx)

Ogni eccezione include:
- ✅ **Messaggio tecnico** per logging
- ✅ **Messaggio user-friendly** per frontend
- ✅ **Flag `should_retry`** per determinare se l'operazione può essere ritentata
- ✅ **Contesto** con informazioni aggiuntive

#### Esempio di Utilizzo

```python
from utility.openai_errors import classify_openai_error, QuotaExceededError

try:
    response = openai_client.audio.transcriptions.create(...)
except Exception as e:
    openai_error = classify_openai_error(e, "whisper_transcription")
    # openai_error.user_message contiene messaggio chiaro per utente
    # openai_error.should_retry indica se ritentare
    raise openai_error
```

### 2. Modifiche a `importRicette/analize.py`

Funzioni modificate:
- `whisper_speech_recognition()`
- `extract_recipe_info()`
- `generateRecipeImages()`

**Cambiamenti:**
- ✅ Importazione modulo `openai_errors`
- ✅ Classificazione automatica errori OpenAI
- ✅ **Retry condizionale**: non ritenta su `QuotaExceededError` o `InvalidAPIKeyError`
- ✅ Propagazione messaggi user-friendly

**Prima:**
```python
@retry(stop=stop_after_attempt(3), wait=wait_exponential(...))
async def whisper_speech_recognition(...):
    # Retry anche su errori di quota (inutile)
    ...
```

**Dopo:**
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(...),
    retry=retry_if_not_exception_type((QuotaExceededError, InvalidAPIKeyError, OpenAIError))
)
async def whisper_speech_recognition(...):
    try:
        ...
    except Exception as e:
        if isinstance(e, (openai.RateLimitError, openai.AuthenticationError, openai.APIError)):
            openai_error = classify_openai_error(e, "whisper_speech_recognition", context)
            error_logger.log_exception("whisper_speech_recognition", openai_error, context)
            raise openai_error
        raise
```

### 3. Modifiche a `importRicette/save.py`

**Cambiamenti:**
- ✅ Cattura specifica di `OpenAIError`
- ✅ Messaggi user-friendly propagati tramite `progress_cb`
- ✅ Gestione non bloccante per generazione immagini (continua senza immagini se fallisce)

**Esempio:**
```python
try:
    ricetta_audio = await whisper_speech_recognition(audio_path, "it")
    _emit_progress("stt", 85.0)
except OpenAIError as openai_err:
    # Propaga messaggio user-friendly
    _emit_progress("error", 50.0, message=openai_err.user_message)
    raise
```

### 4. Modifiche a `importRicette/ingest.py`

**Cambiamenti:**
- ✅ Cattura e gestione specifica `OpenAIError` nel job batch
- ✅ Messaggi chiari nel campo `error` del progresso URL
- ✅ Logging dettagliato con `error_type` e `should_retry`

**Flusso di Gestione Errori:**
```
URL Processing → OpenAIError → Messaggio User-Friendly → Campo "error" nel Progress → Frontend
```

## Messaggi User-Friendly

### Quota Esaurita
```
⚠️ Quota OpenAI esaurita. Verifica il tuo piano su 
https://platform.openai.com/account/billing e ricarica crediti.
```

### Rate Limit
```
⚠️ Troppi request OpenAI. Riprova tra N secondi.
```

### API Key Non Valida
```
❌ API key OpenAI non valida. Verifica la configurazione 
in config.py o nelle variabili d'ambiente.
```

### Errore Server
```
⚠️ Errore server OpenAI. Il servizio potrebbe essere 
temporaneamente non disponibile. Riprova tra qualche minuto.
```

## Comportamento Retry

| Tipo Errore | Retry | Motivo |
|-------------|-------|--------|
| `QuotaExceededError` | ❌ No | Quota esaurita, retry inutile fino a ricarica |
| `InvalidAPIKeyError` | ❌ No | Configurazione errata |
| `RateLimitError` | ✅ Si | Temporaneo, riprova dopo attesa |
| `ServerError` | ✅ Si | Problema temporaneo server |
| `TimeoutError` | ✅ Si | Può essere temporaneo |

## Propagazione Errori al Frontend

Il sistema di progresso URL include ora messaggi chiari:

```json
{
  "urls": [
    {
      "index": 1,
      "url": "https://...",
      "status": "failed",
      "stage": "error",
      "error": "⚠️ Quota OpenAI esaurita. Verifica il tuo piano..."
    }
  ]
}
```

## Testing

### Simula Errore Quota Esaurita

```python
# In config.py, usa API key non valida o esaurita
OPENAI_API_KEY = "sk-expired-key"
```

### Verifica Messaggi

1. Avvia import ricetta da URL
2. Controlla log per vedere classificazione errore
3. Verifica frontend mostra messaggio user-friendly

### Test Completo

```bash
# Avvia server
python main.py

# Importa URL con quota esaurita
curl -X POST http://localhost:8000/recipes/ingest \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://instagram.com/reel/..."]}'

# Controlla job status
curl http://localhost:8000/recipes/ingest/status

# Verifica messaggio errore nel campo "error" dell'URL
```

## Vantaggi Implementazione

1. ✅ **Messaggi chiari**: utente comprende immediatamente il problema
2. ✅ **Retry intelligente**: non spreca tentativi su errori permanenti
3. ✅ **Logging dettagliato**: facilita debugging
4. ✅ **Non bloccante**: generazione immagini fallita non blocca ricetta
5. ✅ **Consistente**: stesso pattern di gestione in tutta l'app
6. ✅ **Estendibile**: facile aggiungere nuovi tipi di errore

## Manutenzione

### Aggiungere Nuovo Tipo Errore

1. Definisci enum in `OpenAIErrorType`
2. Crea classe eccezione in `openai_errors.py`
3. Aggiorna `classify_openai_error()`
4. Aggiorna documentazione

### Debug

Log contengono tutte le informazioni necessarie:
- Tipo errore (`error_type`)
- Contesto operazione
- Flag retry (`should_retry`)
- Stack trace originale

## Note Implementative

- **Preserva stack trace**: `raise` senza argomenti mantiene traccia originale
- **Context manager**: connessioni OpenAI chiuse correttamente
- **Thread-safe**: gestione asincrona corretta
- **Backward compatible**: non modifica API esistenti

---

**Autore**: Smart Recipe Team  
**Data**: 2025-09-30  
**Versione**: 1.0
