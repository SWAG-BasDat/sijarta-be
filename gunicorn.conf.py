import os

bind = "0.0.0.0:8080"
workers = 4
worker_class = 'gthread'
threads = 2
timeout = 120

errorlog = '-'
loglevel = 'debug'
accesslog = '-'