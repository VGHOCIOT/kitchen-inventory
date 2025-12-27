FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./
COPY tests/ ./tests/
RUN chmod +x ./start.sh
CMD ["./start.sh"]