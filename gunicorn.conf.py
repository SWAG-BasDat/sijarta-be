import multiprocessing
import os

bind = f"0.0.0.0:{os.getenv('PORT', '8080')}"
backlog = 2048

workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
threads = 2
worker_connections = 1000
timeout = 120
keepalive = 2


errorlog = '-'
loglevel = 'debug'
accesslog = '-'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

proc_name = 'sijarta-api'

daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

keyfile = None
certfile = None

def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def on_exit(server):
    server.log.info("Stopping server")