FROM python:3.11-slim
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt gunicorn
COPY app /app
WORKDIR /app
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "-b", "0.0.0.0:5000", "app:app"]
