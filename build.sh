#!/usr/bin/env bash

# Exit immediately if any command fails
set -o errexit

# Install dependencies
pip install -r requirements.txt --no-warn-script-location

# ✅ Create static folder if it doesn't exist
mkdir -p staticfiles

# Collect static files
python manage.py collectstatic --noinput --clear

# Run migrations
python manage.py migrate --noinput