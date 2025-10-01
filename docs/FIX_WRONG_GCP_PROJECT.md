# Fix: Progetto GCP Errato (virtual-inflencer-408818)

## Problema

L'errore indica che l'app sta cercando di usare il progetto `virtual-inflencer-408818` invece di `smart-recipe-445321`.

```
The resource 'projects/virtual-inflencer-408818' was not found
```

## Causa

Le credenziali di default (service account o GOOGLE_APPLICATION_CREDENTIALS) puntano al progetto sbagliato.

## Soluzione 1: Verifica Credenziali sulla VM (GCE)

### 1. Controlla quale service account è configurato

SSH nella VM:
```bash
# Verifica service account attivo
curl -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email

# Verifica progetto del service account
curl -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/project/project-id
```

Se il service account appartiene a `virtual-inflencer-408818`, devi cambiarlo.

### 2. Crea nuovo service account nel progetto corretto

```bash
PROJECT_ID="smart-recipe-445321"
SA_NAME="smart-recipe-logging"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Crea service account
gcloud iam service-accounts create ${SA_NAME} \
    --display-name "Smart Recipe Logging" \
    --project ${PROJECT_ID}

# Assegna ruolo Logging Writer
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/logging.logWriter"
```

### 3. Associa service account alla VM

```bash
VM_NAME="your-vm-name"
ZONE="your-zone"  # es: europe-west1-b

# Ferma VM
gcloud compute instances stop ${VM_NAME} --zone=${ZONE}

# Cambia service account
gcloud compute instances set-service-account ${VM_NAME} \
    --zone=${ZONE} \
    --service-account=${SA_EMAIL} \
    --scopes=https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/cloud-platform

# Riavvia VM
gcloud compute instances start ${VM_NAME} --zone=${ZONE}
```

## Soluzione 2: Verifica GOOGLE_APPLICATION_CREDENTIALS

### 1. Controlla se è impostato

SSH nella VM:
```bash
echo $GOOGLE_APPLICATION_CREDENTIALS
cat $GOOGLE_APPLICATION_CREDENTIALS | grep project_id
```

Se il file JSON contiene `"project_id": "virtual-inflencer-408818"`, devi:

### 2. Opzione A - Rimuovi GOOGLE_APPLICATION_CREDENTIALS

```bash
# Rimuovi da .bashrc o .profile
nano ~/.bashrc
# Commenta o rimuovi: export GOOGLE_APPLICATION_CREDENTIALS=...

# Ricarica
source ~/.bashrc
unset GOOGLE_APPLICATION_CREDENTIALS

# Riavvia app
sudo systemctl restart your-service-name
```

La VM userà il service account di default (se configurato correttamente).

### 2. Opzione B - Crea nuovo JSON key

```bash
PROJECT_ID="smart-recipe-445321"
SA_EMAIL="smart-recipe-logging@${PROJECT_ID}.iam.gserviceaccount.com"

# Crea nuova chiave (in locale)
gcloud iam service-accounts keys create ~/smart-recipe-key.json \
    --iam-account=${SA_EMAIL} \
    --project=${PROJECT_ID}

# Copia sulla VM
gcloud compute scp ~/smart-recipe-key.json ${VM_NAME}:~/key.json --zone=${ZONE}

# SSH nella VM e configura
gcloud compute ssh ${VM_NAME} --zone=${ZONE}
echo 'export GOOGLE_APPLICATION_CREDENTIALS="$HOME/key.json"' >> ~/.bashrc
source ~/.bashrc

# Riavvia app
sudo systemctl restart your-service-name
```

## Soluzione 3: Usa SOLO Logging Locale (Più Semplice)

Se non hai bisogno di Cloud Logging subito:

### 1. Configura `.env`

```bash
LOG_BACKEND=local
LOG_LEVEL=INFO
```

### 2. Riavvia app

```bash
sudo systemctl restart your-service-name
```

I log verranno scritti solo in `logs/backend.jsonl`.

## Verifica Configurazione

Dopo aver applicato una delle soluzioni:

### 1. Verifica progetto usato

```bash
# Controlla quale progetto userà l'app
python3 -c "
import os
os.environ.setdefault('GCP_PROJECT_ID', 'smart-recipe-445321')
from google.cloud import logging
client = logging.Client()
print(f'Project ID: {client.project}')
"
```

### 2. Verifica log di startup

```bash
# Controlla log dell'app
journalctl -u your-service-name -n 50 | grep -i "project\|cloud logging"
```

Dovresti vedere:
```
Info: Using GCP Project ID: smart-recipe-445321
Cloud Logging initialized
```

## Riassunto Rapido

**Problema**: Service account o credenziali appartengono al progetto vecchio

**Soluzione veloce**:
```bash
# 1. Rimuovi credenziali vecchie
unset GOOGLE_APPLICATION_CREDENTIALS
rm -f ~/key.json

# 2. Usa logging locale
echo "LOG_BACKEND=local" >> .env

# 3. Riavvia app
sudo systemctl restart your-service-name
```

**Per configurare Cloud Logging correttamente**, segui `docs/CLOUD_LOGGING_SETUP_GCE.md`.

