import os

bind = "0.0.0.0:5000"
workers = 4
worker_class = "gthread"
threads = 4
timeout = 120

errorlog = '-'
loglevel = 'debug'
accesslog = '-'