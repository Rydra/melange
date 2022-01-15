FROM python:3.8.2

# Followed this guide to be able to run tests from docker-compose and pycharm:
# https://www.jetbrains.com/help/pycharm/using-docker-compose-as-a-remote-interpreter.html#docker-compose-remote
# I did some tweaks to this dockerfile since this is not a django project

WORKDIR /app

# By copying over requirements first, we make sure that Docker will cache
# our installed requirements rather than reinstall them on every build
COPY poetry.lock pyproject.toml /app/
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | POETRY_VERSION=1.1.8 python -
RUN POETRY_VIRTUALENVS_CREATE=false "/root/.local/bin/poetry" install $(if [ "$POETRY_ENV" = 'production' ]; then echo '--no-dev'; fi)

# Now copy in our code, and run it
COPY . /app
# EXPOSE 8000
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
