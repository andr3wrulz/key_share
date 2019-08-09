#!/bin/bash

# Start the gunicorn server
echo Starting Gunicorn.
exec gunicorn key_share.wsgi --bing 0.0.0.0:8000 --workers 3