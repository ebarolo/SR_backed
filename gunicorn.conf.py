workers = 1
bind = '127.0.0.1:7040'
timeout = 9000
max_requests = 1000
max_requests_jitter = 50
worker_class = 'sync'
worker_tmp_dir = '/dev/shm'
preload_app = True