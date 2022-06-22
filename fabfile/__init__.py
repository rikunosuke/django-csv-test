import os

from fabric.api import local, task, lcd, env
env.project = 'django-csv-test'

# dir
wd = os.path.dirname(os.path.dirname(__file__))
django_dir = os.path.join(wd, 'django_csv_test')


@task
def build():
    with lcd(wd):
        local(f'docker build . -t {env.project}:latest -f docker/Dockerfile')


@task
def flake8():
    local('flake8 --exclude="*migrations/*,venv/*,.venv/*,~*,*node_modules/*" .')  # NOQA: E501


@task
def login():
    with lcd(wd):
        local('docker-compose -f docker/local.docker-compose.yml run '
              f'{env.project} /bin/ash')
