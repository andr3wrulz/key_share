#!/bin/bash

# Execute the migrations
echo Migrating database.
python manage.py migrate --noinput

# Start the web server
echo Starting Django Server.
exec python manage.py runserver 0.0.0.0:8000
