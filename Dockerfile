FROM python:3.9-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 7860

CMD ["gunicorn", "-k", "gevent", "-w", "1", "-b", "0.0.0.0:7860", "app:app"]