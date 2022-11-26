import os
from pathlib import Path

from fabric.api import local, task, lcd, env
env.project = 'django-csv-test'

# dir
wd = Path(os.path.dirname(os.path.dirname(__file__)))
django_dir = wd / 'django_csv_test'


@task
def build():
    with lcd(str(wd)):
        local(f'docker build . -t {env.project}:latest -f docker/Dockerfile')


@task
def flake8():
    local('flake8 --exclude="*migrations/*,venv/*,.venv/*,~*,*node_modules/*" .')  # NOQA: E501


@task
def login():
    with lcd(wd):
        local('docker-compose -f docker/local.docker-compose.yml run '
              f'{env.project} /bin/ash')


@task(name='pypi-build')
def pypi_build():
    with lcd(str(django_dir / 'django_csv')):
        local('rm -rf build/* model_csv.egg-info/* dist/*')
        local('python3 setup.py sdist')

        local('python3 setup.py bdist_wheel')


@task(name='pypi-upload')
def pypi_upload(repository):
    with lcd(str(django_dir / 'django_csv')):
        local(f'twine upload --repository {repository} dist/*')
