#!/bin/bash

export FLASK_APP=app.py
export FLASK_ENV=development
which flask
echo "Starting mycelium gui"
flask run
