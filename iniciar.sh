#!/bin/bash
cd "$(dirname "$0")"
if [ ! -d "venv" ]; then
    echo "Primera vez: instalando..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --quiet --upgrade pip
    pip install --quiet -r requirements.txt
else
    source venv/bin/activate
fi
python app.py
