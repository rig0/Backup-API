#!/bin/bash

cd /home/rambo/backup-api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # Install dependencies
source venv/bin/activate
python api.py