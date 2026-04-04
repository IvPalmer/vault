#!/bin/bash
cd "$(dirname "$0")"
pip install -r requirements.txt -q
uvicorn server:app --host 0.0.0.0 --port 5178
