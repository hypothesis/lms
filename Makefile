.PHONY: default
default: help

.PHONY: help
help:
	@echo "make help              Show this help message"
	@echo "make dev               Run the app in the development server"
	@echo "make shell             Launch a Python shell in the dev environment"
	@echo "make sql               Connect to the dev database with a psql shell"
	@echo "make lint              Run the code linter(s) and print any warnings"
	@echo "make format            Correctly format the code"
	@echo "make checkformatting   Crash if the code isn't correctly formatted"
	@echo "make test              Run the unit tests"
	@echo "make coverage          Print the unit test coverage report"
	@echo "make codecov           Upload the coverage report to codecov.io"
	@echo "make docstrings        View all the docstrings locally as HTML"
	@echo "make checkdocstrings   Crash if building the docstrings fails"
	@echo "make pip-compile       Compile requirements.in to requirements.txt"
	@echo "make docker            Make the app's Docker image"
	@echo "make run-docker        Run the app's Docker image locally"
	@echo "make clean             Delete development artefacts (cached files, "
	@echo "                       dependencies, etc)"

.PHONY: dev
dev: build/manifest.json
	tox -q -e py36-dev

.PHONY: shell
shell:
	tox -q -e py36-dev -- pshell conf/development.ini

# FIXME: This requires psql to be installed locally.
# It should use psql from docker / docker-compose.
.PHONY: sql
sql:
	psql --pset expanded=auto postgresql://postgres@localhost:5433/postgres

.PHONY: lint
lint: backend-lint frontend-lint

.PHONY: format
format:
	tox -q -e py36-format

.PHONY: checkformatting
checkformatting:
	tox -q -e py36-checkformatting

.PHONY: test
test: backend-tests frontend-tests

.PHONY: coverage
coverage:
	tox -q -e py36-coverage

.PHONY: codecov
codecov:
	tox -q -e py36-codecov

.PHONY: docstrings
docstrings:
	tox -q -e py36-docstrings

.PHONY: checkdocstrings
checkdocstrings:
	tox -q -e py36-checkdocstrings

.PHONY: pip-compile
pip-compile:
	tox -q -e py36-dev -- pip-compile --output-file requirements.txt requirements.in

.PHONY: docker
docker:
	git archive --format=tar.gz HEAD | docker build -t hypothesis/lms:$(DOCKER_TAG) -

.PHONY: run-docker
run-docker:
	# To run the Docker container locally, first build the Docker image using
	# `make docker` and then set the environment variables below to appropriate
	# values (see conf/development.ini for non-production quality examples).
	docker run \
		--net lms_default \
		-e DATABASE_URL=postgresql://postgres@postgres/postgres \
		-e FEATURE_FLAGS_COOKIE_SECRET \
		-e H_API_URL_PRIVATE \
		-e H_API_URL_PUBLIC \
		-e H_AUTHORITY \
		-e H_CLIENT_ID \
		-e H_CLIENT_SECRET  \
		-e H_JWT_CLIENT_ID \
		-e H_JWT_CLIENT_SECRET \
		-e JWT_SECRET \
		-e LMS_SECRET \
		-e RPC_ALLOWED_ORIGINS \
		-e VIA_URL \
		-e SESSION_COOKIE_SECRET \
		-p 8001:8001 \
		hypothesis/lms:$(DOCKER_TAG)

.PHONY: clean
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	rm -f node_modules/.uptodate
	rm -rf build

.PHONY: backend-lint
backend-lint:
	tox -q -e py36-lint

.PHONY: frontend-lint
frontend-lint: node_modules/.uptodate
	$(GULP) lint

# Backend and frontend tests are split into separate targets because on Jenkins
# we need to run them with different Docker images, but `make test` runs both.
.PHONY: backend-tests
backend-tests:
	tox -q -e py36-tests

.PHONY: frontend-tests
frontend-tests: node_modules/.uptodate
	$(GULP) test

DOCKER_TAG = dev

GULP := node_modules/.bin/gulp

build/manifest.json: node_modules/.uptodate
	$(GULP) build

node_modules/.uptodate: package.json yarn.lock
	@echo installing javascript dependencies
	yarn install
	@touch $@
