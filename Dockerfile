FROM python:3.11.11-slim
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
