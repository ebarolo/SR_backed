# gunicorn.conf.py

import os
import tempfile
import torch

# Configurazione base
workers = 1
worker_class = 'sync'
worker_connections = 1000
timeout = 900
keepalive = 2

# Usa una directory temporanea di sistema invece di /dev/shm
worker_tmp_dir = tempfile.gettempdir()

# Configurazione di riavvio e memoria
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# Binding
bind = '127.0.0.1:9040'

# Logging
accesslog = 'access.log'
errorlog = 'error.log'
loglevel = 'info'

# Limiti delle richieste
limit_request_line = 0
limit_request_fields = 100
limit_request_field_size = 0

# Timeout per graceful shutdown
graceful_timeout = 30

# Directory del progetto
chdir = os.path.dirname(os.path.abspath(__file__))
'''
def get_device():
    if torch.backends.mps.is_available():
        try:
            # Tenta di utilizzare MPS
            return torch.device("mps")
        except:
            print("MPS non disponibile, uso CPU")
            return torch.device("cpu")
    else:
        return torch.device("cpu")

# Quando inizializzi SentenceTransformer
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('sentence-transformers/distiluse-base-multilingual-cased-v2', 
                           device=get_device())
'''