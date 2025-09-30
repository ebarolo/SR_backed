# Migrazione a Google Cloud Logging - Summary

## 📋 Cosa è stato fatto

### ✅ Nuovi File Creati

1. **`utility/cloud_logging_config.py`**
   - Sistema di logging completo per Google Cloud
   - Auto-detection di Compute Engine VM resources
   - Structured logging con jsonPayload
   - Trace context per request correlation
   - Error chain tracking
   - Backward compatible con sistema legacy

2. **`utility/cloud_logging_middleware.py`**
   - Middleware FastAPI per request tracking
   - Automatic request_id e trace_id generation
   - Integration con Cloud Trace
   - Performance monitoring
   - JobContextMiddleware per background tasks

3. **`docs/GOOGLE_CLOUD_LOGGING.md`**
   - Documentazione completa
   - Guide deployment su Compute Engine
   - Best practices
   - Troubleshooting
   - Query examples

### ✅ File Aggiornati

#### Configurazione
- **`config.py`**: Aggiunte variabili per Cloud Logging
- **`requirements.txt`**: Aggiunte dipendenze Google Cloud

#### Core Application
- **`main.py`**: 
  - Setup Cloud Logging al startup
  - Middleware per request tracking
  - Import aggiornati

#### Moduli Aggiornati (import)
- `importRicette/ingest.py`
- `importRicette/save.py`
- `importRicette/analize.py`
- `importRicette/scrape/instaLoader.py`
- `importRicette/scrape/yt_dlp.py`
- `rag/_elysia.py`
- `utility/utility.py`
- `utility/error_handler.py`

## 🎯 Funzionalità Principali

### 1. Multi-Backend Support
```python
# Production: Solo Cloud Logging
LOG_BACKEND=cloud

# Development: Solo file locale
LOG_BACKEND=local

# Testing/Debugging: Entrambi
LOG_BACKEND=hybrid
```

### 2. Automatic Resource Detection
Il sistema rileva automaticamente se l'app gira su:
- Compute Engine VM (con metadata completi)
- Container (generic_node resource)
- Locale (generic_node con hostname)

### 3. Request Correlation
Ogni request HTTP ha automaticamente:
- **request_id**: UUID univoco
- **trace_id**: Compatible con Cloud Trace
- Entrambi propagati attraverso async contexts

### 4. Structured Logging
```python
logger.info(
    "Recipe indexed successfully",
    extra={
        "recipe_id": "ABC123",
        "duration_ms": 450,
        "ingredients_count": 12,
        "operation": "indexing"
    }
)
```

### 5. Error Chain Tracking
Traccia cascate di errori attraverso retry e fallback:
```
error_chain: "download_video: ConnectionError -> retry_download: Timeout -> fallback_local: FileNotFound"
```

### 6. Labels per Filtering
Ogni log include automaticamente:
- `environment` (production/staging/development)
- `application` (smart-recipe)
- `version` (0.9)
- `request_id` / `job_id` (quando disponibili)
- `logger` (module name)

## 📊 Miglioramenti Rispetto al Sistema Precedente

### Leggibilità ✅
- **Prima**: Log JSON flat in file locale
- **Dopo**: Structured logs in Cloud Console con filtering avanzato

### Consistenza ✅
- **Prima**: Format inconsistenti tra moduli
- **Dopo**: Schema uniforme con labels e severity standard

### Rilevanza ✅
- **Prima**: Difficile trovare log correlati
- **Dopo**: Trace context collega tutti i log di una request

### Query ✅
- **Prima**: grep/jq su file locale
- **Dopo**: Log Explorer con query language potente

### Monitoring ✅
- **Prima**: Nessun alerting automatico
- **Dopo**: Integration con Cloud Monitoring e Error Reporting

### Scalabilità ✅
- **Prima**: File log crescono indefinitamente
- **Dopo**: Retention automatica, aggregation, sampling

## 🔧 Configurazione Rapida

### Development (Locale)
```bash
# .env
LOG_BACKEND=local
LOG_LEVEL=DEBUG
```

### Staging (Hybrid)
```bash
# .env
LOG_BACKEND=hybrid
LOG_LEVEL=INFO
GCP_PROJECT_ID=smart-recipe-staging
ENVIRONMENT=staging
```

### Production (Cloud)
```bash
# .env
LOG_BACKEND=cloud
LOG_LEVEL=INFO
GCP_PROJECT_ID=smart-recipe-prod
ENVIRONMENT=production
```

## 🚀 Deploy su Compute Engine

### Quick Start
```bash
# 1. Crea VM con scopes corretti
gcloud compute instances create smart-recipe-vm \
    --scopes=https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/cloud-platform

# 2. SSH e deploy
gcloud compute ssh smart-recipe-vm
git clone https://github.com/your-org/smart-recipe.git
cd smart-recipe/SR_backed

# 3. Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Configure
cat > .env << EOF
LOG_BACKEND=cloud
LOG_LEVEL=INFO
GCP_PROJECT_ID=$(gcloud config get-value project)
ENVIRONMENT=production
EOF

# 5. Run
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 📈 Best Practices Implementate

### ✅ Structured Logging
Tutti i log usano `extra={}` per dati strutturati invece di string formatting

### ✅ Context Propagation
Request ID e Trace ID propagati automaticamente attraverso async contexts

### ✅ Severity Mapping
Mapping corretto tra Python logging levels e Cloud Logging severity

### ✅ Resource Detection
Automatic detection di Compute Engine instance con metadata completi

### ✅ Error Reporting
Integration con Cloud Error Reporting per tracking automatico

### ✅ Performance
- Async logging non-blocking
- Batch writes quando possibile
- Path exclusion per endpoints ad alto volume

### ✅ Security
- No sensitive data in logs
- Service Account con minimal permissions
- Secure credential handling

## 🔍 Query Utili

### Tutti i log di una request
```
jsonPayload.request_id="abc-123-def-456"
```

### Errori ultimi 24h
```
severity >= ERROR
timestamp >= "2024-01-01T00:00:00Z"
```

### Performance lente (>1s)
```
jsonPayload.duration_ms > 1000
```

### Job specifico
```
labels.job_id="job-789"
```

### Error pattern analysis
```
severity >= ERROR
| extract jsonPayload.exception.type as error_type
| stats count() by error_type
```

## 🛡️ Backward Compatibility

Il sistema è **100% compatibile** con codice esistente:

- ✅ API identiche (`get_error_logger`, `log_exception`, ecc.)
- ✅ Context variables identici (`request_id_var`, `job_id_var`)
- ✅ Error chain tracking identico
- ✅ File `utility/logging_config.py` mantenuto per legacy code

## 📚 Documentazione

- **Guida Completa**: `docs/GOOGLE_CLOUD_LOGGING.md`
- **Questo Summary**: `docs/LOGGING_MIGRATION_SUMMARY.md`
- **Example Config**: `.env.example` (da creare)

## 🆘 Troubleshooting

### Log non appaiono in Cloud Logging
1. Verifica `LOG_BACKEND=cloud` in `.env`
2. Check service account scopes: `gcloud compute instances describe`
3. Verifica permessi IAM: `roles/logging.logWriter`

### Performance degradato
1. Aumenta `LOG_LEVEL` a INFO in production
2. Aggiungi path a `exclude_paths` nel middleware
3. Verifica Cloud Logging quota

### Credenziali error
1. Su Compute Engine: verifica metadata server
2. Locale: `gcloud auth application-default login`

**Per dettagli completi**: Vedi `docs/GOOGLE_CLOUD_LOGGING.md`

## 📞 Support

- **Documentazione**: `docs/GOOGLE_CLOUD_LOGGING.md`
- **Issues**: GitHub repository
- **Team**: Smart Recipe Development Team

---

**Migrazione completata**: ✅  
**Status**: Production Ready  
**Versione**: 1.0  
**Data**: 2025-01-30

