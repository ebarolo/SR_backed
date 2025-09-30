# Google Cloud Logging - Guida Completa

## Indice
1. [Panoramica](#panoramica)
2. [Configurazione](#configurazione)
3. [Deployment su Compute Engine](#deployment-su-compute-engine)
4. [Utilizzo](#utilizzo)
5. [Best Practices](#best-practices)
6. [Monitoraggio e Query](#monitoraggio-e-query)
7. [Troubleshooting](#troubleshooting)

---

## Panoramica

Smart Recipe utilizza Google Cloud Logging per centralizzare e gestire i log dell'applicazione. Il sistema è progettato per:

- ✅ **Auto-detection** delle risorse Compute Engine VM
- ✅ **Structured logging** con jsonPayload per query avanzate
- ✅ **Trace context** per correlazione request end-to-end
- ✅ **Error Reporting** integration per tracking errori
- ✅ **Fallback locale** per sviluppo e test
- ✅ **Compatibilità** con sistema legacy

### Architettura

```
FastAPI Request
    ↓
CloudLoggingMiddleware (request_id, trace_id)
    ↓
Application Logic (con context propagation)
    ↓
CloudLoggingHandler → Google Cloud Logging
    ↓
Logs Console / Cloud Monitoring
```

---

## Configurazione

### 1. Variabili d'Ambiente

Crea un file `.env` nella root del progetto:

```bash
# === Logging Configuration ===
# Backend: "cloud", "local", o "hybrid"
LOG_BACKEND=hybrid           # Production: cloud, Development: local, Testing: hybrid
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_NAME=smart-recipe       # Nome log in Cloud Logging
LOG_FILE_PATH=logs/backend.jsonl  # Path per log locale (modalità local/hybrid)

# === Google Cloud Configuration ===
GCP_PROJECT_ID=your-project-id
ENVIRONMENT=production      # development, staging, production

# === Optional: Cloud Logging Tuning ===
# GCP_REGION=europe-west1
```

### 2. Backend Modes

#### Cloud Mode (Production)
```bash
LOG_BACKEND=cloud
```
- Tutti i log vanno solo a Google Cloud Logging
- Performance ottimale
- Nessun file locale
- **Raccomandato per production**

#### Local Mode (Development)
```bash
LOG_BACKEND=local
```
- Log salvati solo su file locale JSONL
- Non richiede configurazione GCP
- Ideale per sviluppo locale
- File in `logs/backend.jsonl`

#### Hybrid Mode (Testing/Staging)
```bash
LOG_BACKEND=hybrid
```
- Log inviati sia a Cloud che file locale
- Utile per testing e debug
- Maggior overhead

### 3. Installazione Dipendenze

```bash
pip install -r requirements.txt
```

Le dipendenze chiave aggiunte:
- `google-cloud-logging==3.11.3` - Client Google Cloud Logging
- `google-cloud-error-reporting==1.10.4` - Error Reporting integration
- `python-json-logger==3.3.0` - Structured logging locale

---

## Deployment su Compute Engine

### 1. Setup VM Compute Engine

#### Creare VM con accesso Cloud Logging

```bash
gcloud compute instances create smart-recipe-vm \
    --zone=europe-west1-b \
    --machine-type=e2-medium \
    --scopes=https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/cloud-platform \
    --image-family=debian-11 \
    --image-project=debian-cloud
```

**⚠️ IMPORTANTE**: Lo scope `logging.write` è essenziale per scrivere log.

#### VM Esistenti: Modificare Scopes

Se la VM esiste già senza gli scopes corretti:

```bash
# 1. Stoppa VM
gcloud compute instances stop smart-recipe-vm --zone=europe-west1-b

# 2. Aggiorna scopes
gcloud compute instances set-service-account smart-recipe-vm \
    --zone=europe-west1-b \
    --scopes=https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/cloud-platform

# 3. Riavvia VM
gcloud compute instances start smart-recipe-vm --zone=europe-west1-b
```

### 2. Configurazione Service Account

#### Opzione A: Default Compute Engine SA (Raccomandato)

Il service account di default della VM ha già i permessi necessari se configurato con gli scopes corretti.

#### Opzione B: Custom Service Account

Crea un SA dedicato con permessi minimi:

```bash
# 1. Crea Service Account
gcloud iam service-accounts create smart-recipe-logger \
    --display-name="Smart Recipe Logger"

# 2. Assegna ruoli
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:smart-recipe-logger@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/logging.logWriter"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:smart-recipe-logger@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/errorreporting.writer"

# 3. Associa SA alla VM
gcloud compute instances set-service-account smart-recipe-vm \
    --zone=europe-west1-b \
    --service-account=smart-recipe-logger@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    --scopes=https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/cloud-platform
```

### 3. Deploy Applicazione

```bash
# SSH nella VM
gcloud compute ssh smart-recipe-vm --zone=europe-west1-b

# Clone repository
git clone https://github.com/your-org/smart-recipe.git
cd smart-recipe/SR_backed

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configura environment
cat > .env << EOF
LOG_BACKEND=cloud
LOG_LEVEL=INFO
LOG_NAME=smart-recipe
GCP_PROJECT_ID=$(gcloud config get-value project)
ENVIRONMENT=production
EOF

# Avvia applicazione
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 4. Setup Systemd Service (Production)

```bash
sudo tee /etc/systemd/system/smart-recipe.service > /dev/null <<EOF
[Unit]
Description=Smart Recipe API
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER/smart-recipe/SR_backed
Environment="PATH=/home/$USER/smart-recipe/SR_backed/venv/bin"
ExecStart=/home/$USER/smart-recipe/SR_backed/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Abilita e avvia service
sudo systemctl daemon-reload
sudo systemctl enable smart-recipe
sudo systemctl start smart-recipe
sudo systemctl status smart-recipe
```

---

## Utilizzo

### 1. Logging Base

```python
import logging

logger = logging.getLogger(__name__)

# Log standard
logger.info("Operazione completata")
logger.warning("Attenzione: risorsa limitata")
logger.error("Errore durante elaborazione")

# Con extra context
logger.info(
    "Ricetta indicizzata",
    extra={
        "recipe_id": "ABC123",
        "duration_ms": 450,
        "ingredients_count": 12
    }
)
```

### 2. Error Logging con Context

```python
from utility.cloud_logging_config import get_error_logger

error_logger = get_error_logger(__name__)

try:
    process_recipe(recipe_id)
except Exception as exc:
    error_logger.log_exception(
        operation="process_recipe",
        exc=exc,
        extra={"recipe_id": recipe_id, "user_id": user_id}
    )
```

### 3. Request Context in Route Handlers

```python
from fastapi import Request
from utility.cloud_logging_middleware import get_request_context

@app.get("/recipes/{recipe_id}")
async def get_recipe(recipe_id: str, request: Request):
    context = get_request_context(request)
    logger.info(
        f"Fetching recipe {recipe_id}",
        extra=context  # Automaticamente include request_id e trace_id
    )
    return recipe
```

### 4. Background Jobs con Context

```python
from utility.cloud_logging_middleware import JobContextMiddleware

async def process_batch(job_id: str, items: list):
    async with JobContextMiddleware(job_id):
        # Tutti i log qui avranno il job_id
        logger.info(f"Processing {len(items)} items")
        for item in items:
            process_item(item)
        logger.info("Batch completed")
```

### 5. Error Chain Tracking

```python
from utility.cloud_logging_config import log_error_chain, clear_error_chain

# Inizio operazione complessa
clear_error_chain()

try:
    step1()
except Exception as e:
    log_error_chain(f"step1: {type(e).__name__}")
    try:
        fallback_step1()
    except Exception as e2:
        log_error_chain(f"fallback_step1: {type(e2).__name__}")
        # L'ultimo log conterrà: error_chain: "step1: ValueError -> fallback_step1: ConnectionError"
        raise
```

---

## Best Practices

### 1. Structured Logging

❌ **Male**:
```python
logger.info(f"User {user_id} processed {count} recipes in {duration}ms")
```

✅ **Bene**:
```python
logger.info(
    "User processed recipes",
    extra={
        "user_id": user_id,
        "recipe_count": count,
        "duration_ms": duration,
        "operation": "batch_process"
    }
)
```

### 2. Log Levels

- **DEBUG**: Informazioni dettagliate per debugging (disabilitato in production)
- **INFO**: Eventi normali dell'applicazione (startup, requests, operazioni completate)
- **WARNING**: Situazioni anomale ma gestibili (retry, fallback, risorse limitate)
- **ERROR**: Errori che impediscono operazioni specifiche
- **CRITICAL**: Errori che richiedono attenzione immediata

### 3. Sensitive Data

❌ **NON loggare**:
- Password, API keys, tokens
- Dati personali (PII) senza anonimizzazione
- Dati di pagamento

✅ **Sicuro**:
```python
logger.info(
    "User authenticated",
    extra={
        "user_id": hash_sensitive(user_id),  # Hash o ID anonimo
        "method": "oauth2"
    }
)
```

### 4. Performance

```python
# Lazy evaluation per log debug costosi
if logger.isEnabledFor(logging.DEBUG):
    expensive_data = compute_expensive_debug_info()
    logger.debug("Debug info", extra={"data": expensive_data})
```

### 5. Labels per Filtering

Usa labels consistenti per facilitare query:

```python
logger.info(
    "Recipe indexed",
    extra={
        "operation_type": "indexing",  # Consistente in tutta l'app
        "resource_type": "recipe",
        "status": "success"
    }
)
```

---

## Monitoraggio e Query

### 1. Cloud Logging Console

#### Filtrare per Request ID
```
jsonPayload.request_id="abc-123-def-456"
```

#### Filtrare per Job ID
```
labels.job_id="job-789"
```

#### Errori ultimi 24h
```
severity >= ERROR
timestamp >= "2024-01-01T00:00:00Z"
```

#### Ricerche Lente (>1s)
```
jsonPayload.duration_ms > 1000
httpRequest.latency > "1s"
```

### 2. Log-based Metrics

Crea metriche custom per monitoring:

```bash
gcloud logging metrics create recipe_indexing_errors \
    --description="Errori durante indicizzazione ricette" \
    --log-filter='severity >= ERROR
                   jsonPayload.operation="index_recipe"'
```

### 3. Alert Policies

Esempio: Alert su error rate alto

```bash
gcloud alpha monitoring policies create \
    --notification-channels=CHANNEL_ID \
    --display-name="High Error Rate" \
    --condition-display-name="Error rate > 10/min" \
    --condition-threshold-value=10 \
    --condition-threshold-duration=60s
```

### 4. Query Avanzate

#### Performance Analysis
```
resource.type="gce_instance"
jsonPayload.http_request.status >= 200
jsonPayload.http_request.status < 300
| stats
    avg(jsonPayload.duration_ms) as avg_latency,
    percentile(jsonPayload.duration_ms, 95) as p95_latency,
    count() as request_count
  by jsonPayload.http_request.requestMethod
```

#### Error Pattern Analysis
```
severity >= ERROR
| extract jsonPayload.exception.type as error_type
| stats count() by error_type
| sort by count desc
| limit 10
```

---

## Troubleshooting

### ⚠️ Log non appaiono in Cloud Logging

#### Verifica 1: Service Account e Scopes
```bash
# Check scopes VM
gcloud compute instances describe smart-recipe-vm \
    --zone=europe-west1-b \
    --format="value(serviceAccounts[0].scopes)"

# Deve includere:
# - https://www.googleapis.com/auth/logging.write
# - https://www.googleapis.com/auth/cloud-platform
```

#### Verifica 2: Permessi IAM
```bash
# Verifica ruoli SA
gcloud projects get-iam-policy YOUR_PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:*@*.iam.gserviceaccount.com"

# Deve avere roles/logging.logWriter
```

#### Verifica 3: Metadata Server
```bash
# Dalla VM, verifica accesso a metadata server
curl -H "Metadata-Flavor: Google" \
    http://metadata.google.internal/computeMetadata/v1/instance/id

# Deve restituire instance ID
```

#### Verifica 4: Application Logs
```bash
# Check log applicazione per errori setup
journalctl -u smart-recipe -n 100 | grep -i "cloud logging"
```

### ⚠️ Errore: "google.auth.exceptions.DefaultCredentialsError"

**Causa**: Credenziali GCP non trovate

**Soluzione**:
```bash
# Opzione 1: Su Compute Engine, verifica metadata server
curl -H "Metadata-Flavor: Google" http://metadata.google.internal/

# Opzione 2: Locale, usa Application Default Credentials
gcloud auth application-default login

# Opzione 3: Service Account Key (NON raccomandato in production)
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
```

### ⚠️ Log duplicati

**Causa**: Logging configurato multiple volte

**Soluzione**:
```python
# In main.py, assicurati di chiamare setup_cloud_logging() solo una volta
# Rimuovi eventuali setup_logging() legacy
```

### ⚠️ Performance degradato

**Causa**: Troppi log o handler bloccanti

**Soluzione**:
```bash
# 1. Aumenta LOG_LEVEL in production
LOG_LEVEL=INFO  # invece di DEBUG

# 2. Escludi path frequenti da logging
# In main.py:
app.add_middleware(
    CloudLoggingMiddleware,
    exclude_paths=["/health", "/metrics", "/static"]
)

# 3. Usa async logging (già implementato in CloudLoggingHandler)
```

### ⚠️ Log non strutturati correttamente

**Causa**: Extra fields non passati correttamente

**Verifica**:
```python
# ✅ Corretto
logger.info("message", extra={"key": "value"})

# ❌ Sbagliato
logger.info(f"message {key}")  # Perdi struttura
```

---

## Migrazione da Sistema Legacy

Il nuovo sistema è **retrocompatibile** con il codice esistente:

### 1. Imports Aggiornati Automaticamente

Tutti i file sono stati aggiornati da:
```python
from utility.logging_config import get_error_logger
```

A:
```python
from utility.cloud_logging_config import get_error_logger
```

### 2. API Identica

```python
# Funziona identico a prima
error_logger = get_error_logger(__name__)
error_logger.log_exception("operation", exc)
error_logger.log_error("operation", "message")
```

### 3. Context Variables

```python
# Funzionano identici
from utility.cloud_logging_config import (
    request_id_var,
    job_id_var,
    log_error_chain,
    clear_error_chain
)
```

### 4. Rollback

Se necessario tornare al sistema precedente:

```bash
# Imposta modalità local
LOG_BACKEND=local

# Oppure usa file legacy (mantenuto per compatibilità)
from utility.logging_config import setup_logging
setup_logging()
```

---

## Costi e Ottimizzazione

### Prezzi Google Cloud Logging

- **Primi 50 GB/mese**: Gratuiti
- **Oltre 50 GB**: $0.50/GB
- **Retention default**: 30 giorni (gratuito)
- **Retention esteso**: $0.01/GB/mese

### Stima Consumo

Applicazione media Smart Recipe:
- ~1000 request/ora → ~10 MB/ora → ~7 GB/mese
- Batch jobs → ~5 GB/mese
- **Totale stimato: ~12 GB/mese (gratis)**

### Ottimizzazione Costi

1. **Esclusione Path Statici**
```python
exclude_paths=["/health", "/static", "/asset"]
```

2. **Log Sampling per High Volume**
```python
# In cloud_logging_config.py, aggiungi sampling
if random.random() < 0.1:  # Sample 10%
    logger.debug("high frequency event")
```

3. **Retention Policy**
```bash
# Riduci retention per log DEBUG
gcloud logging sinks create debug-logs-sink \
    storage.googleapis.com/your-bucket \
    --log-filter='severity < INFO'
```

---

## Resources

- [Google Cloud Logging Docs](https://cloud.google.com/logging/docs)
- [Python Client Library](https://googleapis.dev/python/logging/latest/)
- [Log Explorer](https://console.cloud.google.com/logs)
- [Best Practices](https://cloud.google.com/logging/docs/best-practices)
- [Pricing Calculator](https://cloud.google.com/products/calculator)

---

## Support

Per problemi o domande:
1. Controlla questa documentazione
2. Verifica [Troubleshooting](#troubleshooting)
3. Check application logs: `journalctl -u smart-recipe -f`
4. Contatta team di sviluppo

---

**Versione**: 1.0  
**Ultimo aggiornamento**: 2025-01-30  
**Autore**: Smart Recipe Team

