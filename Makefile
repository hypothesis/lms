.PHONY: help
help:
	@echo "make help              Show this help message"
	@echo 'make services          Run the services that `make dev` requires'
	@echo "                       (Postgres) in Docker"
	@echo "make dev               Run the entire app (web server and other processes)"
	@echo "make web               Run the web server on its own (useful for debugging the "
	@echo "                       Python code with pdb)"
	@echo "make assets            Run the assets build on its own, with live reloading "
	@echo '                       (goes well with `make web` and useful for debugging '
	@echo "                       gulp)"
	@echo "make shell             Launch a Python shell in the dev environment"
	@echo "make sql               Connect to the dev database with a psql shell"
	@echo "make lint              Run the code linter(s) and print any warnings"
	@echo "make format            Correctly format the code"
	@echo "make checkformatting   Crash if the code isn't correctly formatted"
	@echo "make test              Run the unit tests"
	@echo "make functests         Run the functional tests"
	@echo "make bddtests          Run the gherkin tests"
	@echo "make sure              Make sure that the formatter, linter, tests, etc all pass"
	@echo "make pip-compile       Compile requirements.in to requirements.txt"
	@echo "make upgrade-package   Upgrade the version of a package in requirements.txt."
	@echo '                       Usage: `make upgrade-package name=some-package`.'
	@echo "make docker            Make the app's Docker image"
	@echo "make run-docker        Run the app's Docker image locally"
	@echo "make clean             Delete development artefacts (cached files, "
	@echo "                       dependencies, etc)"

.PHONY: services
services: args?=up -d
services: python
	@tox -qe docker-compose -- $(args)

.PHONY: dev
dev: build/manifest.json python
	@tox -qe dev -- honcho start ${processes}

.PHONY: devdata
devdata: python
	@tox -qe dev -- devdata conf/development.ini

.PHONY: web
web: python
	@tox -qe dev

GULP := node_modules/.bin/gulp

.PHONY: assets
assets:
	@$(GULP) watch

.PHONY: shell
shell: python
	@tox -qe dev -- pshell conf/development.ini

.PHONY: sql
sql: python
	@tox -qe docker-compose -- exec postgres psql --pset expanded=auto -U postgres

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
test: backend-tests frontend-tests

.PHONY: functests
functests: build/manifest.json functests-only

.PHONY: functests-only
functests-only: python
	@tox -qe functests

.PHONY: pip-compile
pip-compile: python
	@tox -qe pip-compile

.PHONY: upgrade-package
upgrade-package: python
	@tox -qe pip-compile -- --upgrade-package $(name)

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

.PHONY: clean
clean:
	@find . -type f -name "*.py[co]" -delete
	@find . -type d -name "__pycache__" -delete
	@rm -f node_modules/.uptodate
	@rm -rf build

.PHONY: backend-lint
backend-lint: python
	@tox -qe lint

.PHONY: frontend-lint
frontend-lint: node_modules/.uptodate
	@yarn checkformatting
	@yarn lint

# Backend and frontend tests are split into separate targets because on Jenkins
# we need to run them with different Docker images, but `make test` runs both.
.PHONY: backend-tests
backend-tests: python
	@tox -qe tests

.PHONY: bddtests
bddtests: python
	@tox -qe bddtests

.PHONY: sure
sure: checkformatting backend-lint frontend-lint backend-tests frontend-tests functests bddtests

.PHONY: frontend-tests
frontend-tests: node_modules/.uptodate
	@$(GULP) test

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
