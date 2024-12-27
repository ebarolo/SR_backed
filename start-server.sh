#!/bin/bash

# Directory del progetto
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Attiva l'ambiente virtuale se esiste
if [ -d ".env" ]; then
    source .env/bin/activate
fi

# Imposta le variabili d'ambiente
export PYTHONUNBUFFERED=1
export PYTHONMALLOC=malloc

# Pulisci i file di log se esistono
[ -f access.log ] && > access.log
[ -f error.log ] && > error.log

# Avvia Gunicorn con la nuova configurazione
exec gunicorn -c gunicorn.conf.py main:app
