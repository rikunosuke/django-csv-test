FROM --platform=linux/x86_64 alpine:3.14 AS django-csv-test-build

COPY django_csv_test/Pipfile /tmp/Pipfile

RUN apk --no-cache add \
    python3 \
    python3-dev \
    py3-pip \
    && pip3 install pipenv --ignore-installed six distlib

WORKDIR /tmp
RUN pipenv lock \
    && pipenv sync --system --dev

FROM --platform=linux/x86_64 alpine:3.14

COPY --from=django-csv-test-build /usr/lib/python3.9/site-packages /usr/lib/python3.9/

RUN apk --no-cache add \
    python3

RUN mkdir /var/django  \
    && chmod 755 /var/django

COPY django_csv_test /var/django/django_csv_test

WORKDIR /var/django/django_csv_test

EXPOSE 8000
