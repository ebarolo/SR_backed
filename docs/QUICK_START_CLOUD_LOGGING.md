# Quick Start - Google Cloud Logging

Guida rapida per iniziare con il nuovo sistema di logging.

## 🚀 Setup in 5 minuti

### 1. Installa Dipendenze

```bash
pip install -r requirements.txt
```

### 2. Configura Environment

Crea file `.env`:

```bash
# === DEVELOPMENT (Locale) ===
LOG_BACKEND=local
LOG_LEVEL=DEBUG

# === PRODUCTION (Cloud) ===
# LOG_BACKEND=cloud
# LOG_LEVEL=INFO
# GCP_PROJECT_ID=your-project-id
# ENVIRONMENT=production
```

### 3. Avvia Applicazione

```bash
uvicorn main:app --reload
```

✅ **Fatto!** I log sono ora configurati.

---

## 🖥️ Deploy su Compute Engine

### Setup VM (1 volta)

```bash
# 1. Crea VM con permessi logging
gcloud compute instances create smart-recipe-vm \
    --zone=europe-west1-b \
    --machine-type=e2-medium \
    --scopes=https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/cloud-platform

# 2. SSH nella VM
gcloud compute ssh smart-recipe-vm --zone=europe-west1-b
```

### Deploy Applicazione

```bash
# 3. Clone e setup
git clone YOUR_REPO_URL
cd smart-recipe/SR_backed
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Configure per production
cat > .env << 'EOF'
LOG_BACKEND=cloud
LOG_LEVEL=INFO
GCP_PROJECT_ID=$(gcloud config get-value project)
ENVIRONMENT=production

# Altri config...
OPENAI_API_KEY=your-key
WCD_URL=your-weaviate-url
WCD_API_KEY=your-weaviate-key
EOF

# 5. Test
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Setup come Service

```bash
# 6. Crea systemd service
sudo tee /etc/systemd/system/smart-recipe.service > /dev/null <<EOF
[Unit]
Description=Smart Recipe API
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/smart-recipe/SR_backed
Environment="PATH=$HOME/smart-recipe/SR_backed/venv/bin"
ExecStart=$HOME/smart-recipe/SR_backed/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 7. Avvia service
sudo systemctl daemon-reload
sudo systemctl enable smart-recipe
sudo systemctl start smart-recipe
```

---

## 📊 Verifica Funzionamento

### Check Logs Console

1. Vai a: https://console.cloud.google.com/logs
2. Seleziona il tuo progetto
3. Filtra per: `logName="projects/YOUR_PROJECT/logs/smart-recipe"`

### Query di Test

```
# Tutti i log dell'applicazione
logName="projects/YOUR_PROJECT/logs/smart-recipe"

# Solo errori
logName="projects/YOUR_PROJECT/logs/smart-recipe"
severity >= ERROR

# Log di una request specifica
jsonPayload.request_id="REQUEST_ID"
```

---

## 🧪 Test Locale

### Test 1: Log Base

```python
import logging
logger = logging.getLogger(__name__)

logger.info("Test log INFO")
logger.warning("Test log WARNING")
logger.error("Test log ERROR")
```

### Test 2: Structured Log

```python
logger.info(
    "Test structured log",
    extra={
        "user_id": "user123",
        "action": "test",
        "duration_ms": 150
    }
)
```

### Test 3: Request (via HTTP)

```bash
curl http://localhost:8000/health
```

Check log per vedere:
- Request ID
- Duration
- Status code

---

## 🔧 Configurazioni Comuni

### Development Locale

```bash
LOG_BACKEND=local
LOG_LEVEL=DEBUG
LOG_FILE_PATH=logs/backend.jsonl
```

### Staging

```bash
LOG_BACKEND=hybrid  # Cloud + file locale
LOG_LEVEL=INFO
GCP_PROJECT_ID=smart-recipe-staging
ENVIRONMENT=staging
```

### Production

```bash
LOG_BACKEND=cloud
LOG_LEVEL=INFO
GCP_PROJECT_ID=smart-recipe-prod
ENVIRONMENT=production
```

---

## 🆘 Troubleshooting Rapido

### ❌ Log non appaiono in Cloud Logging

```bash
# Check 1: Verifica VM scopes
gcloud compute instances describe smart-recipe-vm \
    --zone=europe-west1-b \
    --format="value(serviceAccounts[0].scopes)"

# Deve includere: logging.write

# Check 2: Verifica config
cat .env | grep LOG_BACKEND
# Deve essere: cloud o hybrid

# Check 3: Test metadata server (dalla VM)
curl -H "Metadata-Flavor: Google" \
    http://metadata.google.internal/computeMetadata/v1/instance/id
# Deve restituire un ID
```

### ❌ Errore permessi

```bash
# Aggiungi ruolo logging writer al service account
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
    --role="roles/logging.logWriter"
```

### ❌ Performance lento

```bash
# Aumenta log level
LOG_LEVEL=INFO  # invece di DEBUG

# Escludi path frequenti
# Nel codice (main.py):
exclude_paths=["/health", "/metrics", "/static"]
```

---

## 📚 Documentazione Completa

Per guide dettagliate, vedi:
- **Guida Completa**: `docs/GOOGLE_CLOUD_LOGGING.md`
- **Summary Migrazione**: `docs/LOGGING_MIGRATION_SUMMARY.md`

---

## ✅ Checklist Pre-Production

- [ ] VM creata con scopes corretti
- [ ] Service account ha `roles/logging.logWriter`
- [ ] `.env` configurato con `LOG_BACKEND=cloud`
- [ ] `GCP_PROJECT_ID` impostato correttamente
- [ ] Test request genera log in Cloud Console
- [ ] Systemd service configurato e running
- [ ] Alert configurati per errori critici
- [ ] Team sa accedere a Cloud Logging Console

---

**Pronto per production!** 🎉

Per domande: vedi documentazione completa in `docs/`

