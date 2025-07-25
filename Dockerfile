FROM python:3.9-slim

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

EXPOSE 8000
CMD ["uvicorn", "API_TEST:app", "--host", "0.0.0.0", "--port", "8000"]
