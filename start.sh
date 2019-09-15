#!/usr/bin/env bash

if [[ "$1" == "test" ]]; then
    echo "Running the tests only."
    pip install -r requirements_test.txt
    # Ignore Jinja warnings, as it didn't catch up to Python 3.7 yet
    pytest -W ignore::DeprecationWarning
else
    echo "Starting up server"
    gunicorn --bind "0.0.0.0:${PORT=8000}" wsgi:app
fi