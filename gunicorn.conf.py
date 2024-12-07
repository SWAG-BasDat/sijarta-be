import os

port = os.getenv("PORT", "8080")
bind = f"0.0.0.0:{port}"

workers = 4  
worker_class = 'gthread' 
threads = 2
timeout = 120

errorlog = '-'
loglevel = 'debug'
accesslog = '-'

capture_output = True
enable_stdio_inheritance = True