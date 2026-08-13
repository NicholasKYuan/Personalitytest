FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (cache layer)
COPY webapp/backend/requirements.txt /app/webapp/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/webapp/backend/requirements.txt

# Copy project files (maintains path structure expected by app.py)
COPY webapp/ /app/webapp/
COPY question-bank/ /app/question-bank/
COPY selector/ /app/selector/

# Create runtime directories
RUN mkdir -p /app/webapp/backend/sessions /data/sessions

WORKDIR /app/webapp/backend

EXPOSE 80

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80"]
