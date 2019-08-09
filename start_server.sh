#!/bin/bash

# Execute the migrations
echo Migrating database.
python manage.py migrate --noinput

# Start the gunicorn server
echo Starting Gunicorn.
exec gunicorn key_share.wsgi --bind 0.0.0.0:8000 --workers 3
