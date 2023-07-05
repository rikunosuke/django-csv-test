FROM python:3.10-slim AS django-csv-test-build

RUN pip3 install pipenv --ignore-installed six distlib

COPY django_csv_test /var/app/django_csv_test
WORKDIR /var/app/django_csv_test

RUN pipenv lock \
    && pipenv sync --system --dev

RUN chmod 755 /var/app

EXPOSE 8000
