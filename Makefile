CURRENTDIR := ${CURDIR}
PROD_DOCKER_IMAGE := inari/kitsune_web:$(or $(BRANCH_NAME), latest)
DEV_DOCKER_IMAGE := inari/kitsune_web_dev:$(or $(BRANCH_NAME), latest)

clean-pyc:
	-find . -name \*.pyc -delete
	-find . -name \*.pyo -delete
	-find . -name \*~ -delete

# ############
# Flake 8
# ############

flake8:
	docker run --rm --volume $(CURRENTDIR):/melange alpine/flake8 $(or $(files), /melange)


build-dev:
	docker-compose -f docker-compose.yml build --parallel --force-rm --compress --build-arg POETRY_ENV=dev


run-tests:
	docker-compose run --rm app pytest


run-coverage:
	docker-compose run --rm app pytest --cov=melange --cov-report html:cov_html


run-example-app:
	docker-compose run --rm app python melange/examples/payment_service/init_queues.py
	docker-compose run --rm app python melange/examples/payment_service/app.py


run-example-triggerer:
	docker-compose run --rm app python melange/examples/payment_service/triggerer.py $(reference)
