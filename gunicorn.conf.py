
import os
import tempfile

# Configurazione base
workers = 1
worker_class = 'sync'
worker_connections = 10000
timeout = 9000
keepalive = 2

# Usa una directory temporanea di sistema invece di /dev/shm
worker_tmp_dir = tempfile.gettempdir()

# Configurazione di riavvio e memoria
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# Binding
bind = '127.0.0.1:3040'

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