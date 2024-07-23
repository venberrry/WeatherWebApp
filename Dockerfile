FROM python:3.12
ENV PYTHONUNBUFFERED 1

WORKDIR /app
COPY requirements.txt /app/

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /app/

ENV DJANGO_SETTINGS_MODULE=WeatherProject.settings
ENV PYTHONPATH=/app

CMD ["python", "WeatherProject/manage.py", "runserver", "0.0.0.0:8000"]
