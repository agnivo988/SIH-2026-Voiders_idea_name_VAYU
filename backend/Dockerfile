FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
COPY scripts ./scripts
COPY backend/start.sh ./start.sh
RUN chmod +x ./start.sh
ENV PYTHONPATH=/app
CMD ["./start.sh"]
