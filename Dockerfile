FROM python:3.12-slim
WORKDIR /app
COPY moduleAI /app/moduleAI
COPY ai_service.py /app/ai_service.py
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
ENV PYTHONUNBUFFERED=1
EXPOSE 8001
CMD ["python", "ai_service.py"]
