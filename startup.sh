#!/bin/bash
export PORT=8080
gunicorn app:app --bind 0.0.0.0:$PORT