FROM python:3.11-slim
RUN pip install flask pyyaml gunicorn
WORKDIR /app
COPY . /app
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
