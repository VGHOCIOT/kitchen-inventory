#!/bin/bash
set -e

# Wait for DB to ready up
echo "Waiting for Postgres..."
until pg_isready -h db -p 5432; do
  sleep 1
done
echo "Postgres is ready."

# Initialize alembic if it doesn't exist
if [ ! -d "/app/alembic" ]; then
    echo "🔧 Alembic not found. Initializing..."
    alembic init alembic
    echo "✅ Alembic initialized!"
    echo "📝 Please configure /app/alembic/env.py with your models"
    echo "🔄 Restart the container after configuration"
    exit 0
fi

# Check if alembic/env.py has been configured
if grep -q "target_metadata = None" /app/alembic/env.py; then
    echo "⚠️  Alembic env.py needs configuration!"
    echo "📝 Please update /app/alembic/env.py with your database models"
    echo "🔄 Restart the container after configuration"
    exit 0
fi

# Run migrations 
echo "Running Alembic migrations..."
alembic upgrade head


# Start API
echo "Starting API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000