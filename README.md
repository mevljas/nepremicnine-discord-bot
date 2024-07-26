# nepremicnine-discord-bot
A discord bot for notifying about new listings on the [nepremicnine.net](https://nepremicnine.net) website using [Playwright](https://playwright.dev/python/).

## Project setup

### Setup environment variables

```bash
cp .env.example .env
```

Edit **.env** file if necessary. Number of threads can be set using the *N_THREADS* parameter.

### Run Docker Postgres database

```bash
docker-compose up -d nepremicnine-db
```

### Create and use virtual env

```bash
pip install virtualenv
python<version> -m venv <virtual-environment-name>
source env/bin/activate
```

Alternatively you can set it up using Pycharm.

### Install requirements

```bash
poetry install
```

### Install the [Pytest plugin](https://pypi.org/project/pytest-playwright/):

```bash
pip install pytest-playwright
```

### Install Playwright browsers (chromium, firefox, webkit)

```bash
playwright install
```

### Run database migrations

```bash
python migrate.py
```

## Run the crawler

```bash
python main.py
```

## PgAdmin (optional)

You can run PgAdmin Docker container with the following command:

```bash
docker-compose up -d pgadmin
```

Access the pgadmin4 via your favorite web browser by visiting the [URL](http://localhost:5050/).
Use the admin@admin.com as the email address and root as the password to log in.
