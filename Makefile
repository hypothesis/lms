.PHONY: help
help:
	@echo "make help              Show this help message"
	@echo 'make services          Run the services that `make dev` requires'
	@echo "                       (Postgres) in Docker"
	@echo 'make db                Upgrade the DB schema to the latest version'
	@echo "make dev               Run the entire app (web server and other processes)"
	@echo "make supervisor        Launch a supervisorctl shell for managing the processes "
	@echo '                       that `make dev` starts, type `help` for docs'
	@echo "make shell             Launch a Python shell in the dev environment"
	@echo "make sql               Connect to the dev database with a psql shell"
	@echo "make lint              Run the code linter(s) and print any warnings"
	@echo "make format            Correctly format the code"
	@echo "make checkformatting   Crash if the code isn't correctly formatted"
	@echo "make test              Run all unit tests"
	@echo "make backend-tests     Run the backend unit tests"
	@echo "make frontend-tests    Run the frontend unit tests"
	@echo "make functests         Run the functional tests"
	@echo "make bddtests          Run the gherkin tests"
	@echo "make sure              Make sure that the formatter, linter, tests, etc all pass"
	@echo "make docker            Make the app's Docker image"
	@echo "make run-docker        Run the app's Docker image locally"

.PHONY: services
services: args?=up -d
services: python
	@tox -qe dockercompose -- $(args)

.PHONY: db
db: args?=upgrade head
db: python
	@tox -qqe dev --run-command 'python bin/initialize_db.py conf/development.ini'
	@tox -qe dev  --run-command 'alembic -c conf/alembic.ini $(args)'

.PHONY: dev
dev: build/manifest.json python
	@tox -qe dev

.PHONY: supervisor
supervisor: python
	@tox -qe dev --run-command 'supervisorctl -c conf/supervisord-dev.conf $(command)'

.PHONY: devdata
devdata: build/manifest.json  python
	@tox -qe dev --run-command 'python bin/update_dev_data.py conf/development.ini'

.PHONY: shell
shell: build/manifest.json python
	@tox -qe dev --run-command 'pshell conf/development.ini'

.PHONY: sql
sql: python
	@tox -qe dockercompose -- exec postgres psql --pset expanded=auto -U postgres

.PHONY: lint
lint: backend-lint frontend-lint

.PHONY: format
format: backend-format frontend-format

.PHONY: backend-format
backend-format: python
	@tox -qe format

.PHONY: frontend-format
frontend-format: node_modules/.uptodate
	@yarn format

.PHONY: checkformatting
checkformatting: python
	@tox -qe checkformatting

.PHONY: test
test: backend-tests coverage frontend-tests

# Backend and frontend tests are split into separate targets because on Jenkins
# we need to run them with different Docker images, but `make test` runs both.
.PHONY: backend-tests
backend-tests: python
	@tox -qe tests

.PHONY: coverage
coverage: python
	@tox -qe coverage

.PHONY: frontend-tests
frontend-tests: node_modules/.uptodate
ifdef ARGS
	yarn test $(ARGS)
else
	yarn test
endif

.PHONY: functests
functests: build/manifest.json functests-only

.PHONY: functests-only
functests-only: python
	@tox -qe functests

.PHONY: docker
docker:
	@git archive --format=tar.gz HEAD | docker build -t hypothesis/lms:$(DOCKER_TAG) -

.PHONY: run-docker
run-docker:
	# To run the Docker container locally, first build the Docker image using
	# `make docker` and then set the environment variables below to appropriate
	# values (see conf/development.ini for non-production quality examples).
	@docker run \
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
		-e OAUTH2_STATE_SECRET \
		-p 8001:8001 \
		hypothesis/lms:$(DOCKER_TAG)

.PHONY: backend-lint
backend-lint: python
	@tox -qe lint

.PHONY: frontend-lint
frontend-lint: node_modules/.uptodate
	@yarn checkformatting
	@yarn lint
	@yarn typecheck


.PHONY: bddtests
bddtests: python
	@tox -qe bddtests

.PHONY: sure
sure: checkformatting backend-lint frontend-lint backend-tests coverage frontend-tests functests bddtests


DOCKER_TAG = dev

build/manifest.json: node_modules/.uptodate
	@yarn build

node_modules/.uptodate: package.json yarn.lock
	@echo installing javascript dependencies
	@yarn install
	@touch $@

.PHONY: python
python:
	@./bin/install-python
