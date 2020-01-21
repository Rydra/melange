CURRENTDIR := ${CURDIR}
PROD_DOCKER_IMAGE := inari/kitsune_web:$(or $(BRANCH_NAME), latest)
DEV_DOCKER_IMAGE := inari/kitsune_web_dev:$(or $(BRANCH_NAME), latest)

clean-pyc:
	-find . -name \*.pyc -delete
	-find . -name \*.pyo -delete
	-find . -name \*~ -delete

# ############
# Global tasks
# ############

download-precommit-hook:
	curl -o config/git/hooks/pre-commit.sh https://raw.githubusercontent.com/21Buttons/backend-pre-commit/master/pre-commit.sh

symlinks-pre-commit-hooks:
	rm -f .git/hooks/pre-commit
	mkdir -p config/git/hooks
	chmod +x config/git/hooks/pre-commit.sh
	ln -s ../../config/git/hooks/pre-commit.sh .git/hooks/pre-commit

# ############
# Flake 8
# ############

flake8:
	docker run --rm --volume $(CURRENTDIR):/melange alpine/flake8 $(or $(files), /melange)
