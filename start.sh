#!/bin/bash
# THE VAULT - Dev Startup Script
# Starts Django backend (port 8001) and Vite frontend (port 5175)

echo "Starting THE VAULT dev servers..."

# Backend
echo "→ Django on http://localhost:8001"
cd backend && \
  POSTGRES_USER=palmer POSTGRES_PASSWORD= POSTGRES_DB=vault POSTGRES_HOST=localhost \
  CORS_ALLOWED_ORIGINS="http://localhost:5175,http://127.0.0.1:5175" \
  ./venv/bin/python manage.py runserver 8001 &
BACKEND_PID=$!

# Frontend
echo "→ React on http://localhost:5175"
cd .. && npx vite --port 5175 --strictPort &
FRONTEND_PID=$!

echo ""
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo "Press Ctrl+C to stop both servers"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
