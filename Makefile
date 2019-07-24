.PHONY: default
default: help

.PHONY: help
help:
	@echo "make help              Show this help message"
	@echo 'make services          Run the services that `make dev` requires'
	@echo "                       (Postgres) in Docker"
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
	@echo "make docker-dev        Make the app's Docker image applying the dev configuration"
	@echo "make run-docker        Run the app's Docker image locally"
	@echo "make run-docker-dev    Run the app's Docker image locally and interactively"
	@echo "make run-docker-test   Run the unit tests via the app's Docker image locally"
	@echo "make test-db           Make a test database
	@echo "make clean             Delete development artefacts (cached files, "
	@echo "                       dependencies, etc)"

.PHONY: services
services:
	docker-compose up -d

.PHONY: dev
dev: build/manifest.json
	tox -q -e py36-dev

.PHONY: shell
shell:
	tox -q -e py36-dev -- pshell conf/development.ini

.PHONY: sql
sql:
	docker-compose exec lmspostgres psql --pset expanded=auto -U postgres

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

.PHONY: docker-dev
docker-dev:
	docker build -f Dockerfile-dev -t hypothesis/lms:$(DOCKER_TAG) .

.PHONY: run-docker
run-docker:
	# To run the Docker container locally, first build the Docker image using
	# `make docker` and then set the environment variables below to appropriate
	# values (see conf/development.ini for non-production quality examples).
	docker run \
		--name lms \
		--net h_default \
		-e DATABASE_URL=postgresql://postgres@lmspostgres/postgres \
		-e GOOGLE_CLIENT_ID \
		-e GOOGLE_DEVELOPER_KEY \
		-e GOOGLE_APP_ID \
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
		-e OAUTH2_STATE_SECRET \
		-e NEW_RELIC_LICENSE_KEY \
        -e NEW_RELIC_APP_NAME="lms (dev)" \
        -e SENTRY_ENVIRONMENT="dev" \
        -e SENTRY_DSN \
		-p 8001:8001 \
		hypothesis/lms:$(DOCKER_TAG)

.PHONY: run-docker-dev
run-docker-dev:
	docker run \
		--name lms \
		--net h_default \
		-v $(CURDIR)/lms:/var/lib/lms/lms \
		-it \
		--entrypoint '/bin/sh' \
		-e DATABASE_URL=postgresql://postgres@lmspostgres/postgres \
		-e GOOGLE_CLIENT_ID \
		-e GOOGLE_DEVELOPER_KEY \
		-e GOOGLE_APP_ID \
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
		-e OAUTH2_STATE_SECRET \
		-e NEW_RELIC_LICENSE_KEY \
        -e NEW_RELIC_APP_NAME="lms (dev)" \
        -e SENTRY_ENVIRONMENT="dev" \
        -e SENTRY_DSN \
        -e SENTRY_DSN_FRONTEND \
		-p 8001:8001 \
		hypothesis/lms:$(DOCKER_TAG) \
	    -c "newrelic-admin run-program gunicorn --paste conf/development.ini"

.PHONY: run-docker-test
run-docker-test:
	docker run \
		--name lms \
		--net h_default \
		-v $(CURDIR)/lms:/var/lib/lms/lms \
		-v $(CURDIR)/tests:/var/lib/lms/tests \
		-it \
		--entrypoint '/bin/sh' \
		-e DATABASE_URL=postgresql://postgres@lmspostgres/postgres \
		-e TEST_DATABASE_URL=postgresql://postgres@lmspostgres/lms_test \
		-e GOOGLE_CLIENT_ID \
		-e GOOGLE_DEVELOPER_KEY \
		-e GOOGLE_APP_ID \
		-e H_API_URL_PRIVATE \
		-e H_API_URL_PUBLIC \
		-e H_AUTHORITY \
		-e H_CLIENT_ID \
		-e H_CLIENT_SECRET  \
		-e H_JWT_CLIENT_ID \
		-e H_JWT_CLIENT_SECRET \
		-e JWT_SECRET=test_secret \
		-e LMS_SECRET \
		-e RPC_ALLOWED_ORIGINS \
		-e VIA_URL=https://example.com/ \
		-e SESSION_COOKIE_SECRET \
		-e OAUTH2_STATE_SECRET \
		-p 8001:8001 \
		hypothesis/lms:$(DOCKER_TAG) \
	    -c "pytest -v -p no:cacheprovider tests/lms"

.PHONY: test-db
test-db:
	docker-compose exec lmspostgres psql -U postgres -c "CREATE DATABASE lms_test;"

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
	yarn checkformatting
	yarn lint

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
