# Configurazione Cloud Logging su Google Compute Engine

## Problema
Se vedi l'errore:
```
google.auth.exceptions.RefreshError: Failed to retrieve http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/
```

Significa che la VM non ha un service account configurato o non ha i permessi necessari.

## Soluzione 1: Aggiungi Service Account alla VM (Raccomandato)

### 1. Crea un Service Account con i permessi necessari

```bash
# Imposta variabili
PROJECT_ID="smart-recipe-445321"
SA_NAME="smart-recipe-logging"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Crea service account
gcloud iam service-accounts create ${SA_NAME} \
    --display-name "Smart Recipe Logging Service Account" \
    --project ${PROJECT_ID}

# Assegna ruolo Logging Writer
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/logging.logWriter"
```

### 2. Associa il Service Account alla VM

**Opzione A: VM esistente (richiede restart)**
```bash
VM_NAME="your-vm-name"
ZONE="your-zone"  # es: europe-west1-b

gcloud compute instances stop ${VM_NAME} --zone=${ZONE}

gcloud compute instances set-service-account ${VM_NAME} \
    --zone=${ZONE} \
    --service-account=${SA_EMAIL} \
    --scopes=https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/cloud-platform

gcloud compute instances start ${VM_NAME} --zone=${ZONE}
```

**Opzione B: Nuova VM**
```bash
gcloud compute instances create ${VM_NAME} \
    --zone=${ZONE} \
    --service-account=${SA_EMAIL} \
    --scopes=https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/cloud-platform
```

### 3. Verifica configurazione

SSH nella VM e verifica:
```bash
# Verifica service account
curl -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email

# Dovrebbe restituire: smart-recipe-logging@smart-recipe-445321.iam.gserviceaccount.com
```

## Soluzione 2: Usa Service Account Key (Alternativa)

Se non puoi modificare la VM, usa una chiave JSON:

### 1. Genera chiave JSON

```bash
gcloud iam service-accounts keys create ~/smart-recipe-logging-key.json \
    --iam-account=${SA_EMAIL}
```

### 2. Carica sulla VM e configura

```bash
# Copia sulla VM
gcloud compute scp ~/smart-recipe-logging-key.json ${VM_NAME}:~/key.json --zone=${ZONE}

# SSH nella VM
gcloud compute ssh ${VM_NAME} --zone=${ZONE}

# Configura environment variable
echo 'export GOOGLE_APPLICATION_CREDENTIALS="$HOME/key.json"' >> ~/.bashrc
source ~/.bashrc
```

### 3. Restart applicazione

```bash
# Riavvia il servizio
sudo systemctl restart your-service-name
```

## Soluzione 3: Usa solo Local Logging (Più semplice)

Se non hai bisogno di Cloud Logging, usa solo logging locale:

### 1. Modifica `.env`

```bash
LOG_BACKEND=local
LOG_LEVEL=INFO
```

### 2. Restart applicazione

I log verranno scritti in `logs/backend.jsonl` invece che su Cloud Logging.

## Verifica

Dopo la configurazione, l'applicazione dovrebbe avviarsi senza errori. Verifica i log:

```bash
# Se usi Cloud Logging
gcloud logging read "resource.type=generic_node AND logName=projects/${PROJECT_ID}/logs/smart-recipe" \
    --limit 10 \
    --format json

# Se usi Local Logging
tail -f logs/backend.jsonl
```

## Rollback in caso di problemi

L'applicazione ora fa automaticamente fallback a logging locale se Cloud Logging non è disponibile. Non dovrebbe più bloccarsi al startup.

Per debug, controlla:
```bash
# Verifica LOG_BACKEND in .env
cat .env | grep LOG_BACKEND

# Controlla log di startup
journalctl -u your-service-name -n 50
```

## Best Practices

1. **Production**: Usa Service Account su VM con `LOG_BACKEND=cloud`
2. **Staging**: Usa `LOG_BACKEND=hybrid` (entrambi cloud e local)
3. **Development**: Usa `LOG_BACKEND=local`

## Permessi IAM necessari

Il service account ha bisogno di:
- `roles/logging.logWriter` - per scrivere log
- `roles/cloudtrace.agent` - (opzionale) per trace integration

Non servono permessi aggiuntivi se usi solo logging.


