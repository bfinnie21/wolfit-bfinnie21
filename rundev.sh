#!/bin/bash
export FLASK_ENV=development
export FLASK_DEBUG=0
export WOLFIT_SETTINGS=$(pwd)/dev.settings
export LOG_URL="http://localhost:8080"
flask run --host=0.0.0.0 --port=8082
