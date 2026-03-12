#!/usr/bin/env bash

# Exit immediately if any command fails
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# ✅ Run migrations here — free alternative to preDeployCommand
python manage.py migrate --noinput