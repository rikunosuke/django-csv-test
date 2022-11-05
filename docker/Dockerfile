FROM python:3.10-slim AS django-csv-test-build

COPY django_csv_test/Pipfile /tmp/Pipfile

RUN pip3 install pipenv --ignore-installed six distlib

WORKDIR /tmp
RUN pipenv lock \
    && pipenv sync --system --dev

RUN mkdir /var/app  \
    && chmod 755 /var/app

COPY django_csv_test /var/app/django_csv_test

WORKDIR /var/app/django_csv_test

EXPOSE 8000
