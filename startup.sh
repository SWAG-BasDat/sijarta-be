#!/bin/bash
gunicorn app:app --bind 0.0.0.0:8080 --config gunicorn.conf.py