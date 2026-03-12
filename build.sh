#!/usr/bin/env bash

# Stop script if any command fails
set -o errexit

echo "Updating pip..."
python -m pip install --upgrade pip

echo "Installing dependencies..."
python -m pip install -r requirements.txt

echo "Cleaning old static files..."
if [ -d "staticfiles" ]; then
    rm -rf staticfiles
fi

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Running migrations..."
python manage.py migrate --noinput

echo "Build completed successfully."