#!/usr/bin/env bash

# Exit immediately if any command fails
set -o errexit

# Install dependencies
pip install -r requirements.txt --no-warn-script-location

# ✅ Wipe old staticfiles and collect fresh
rm -rf staticfiles
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate --noinput