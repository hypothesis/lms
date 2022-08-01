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
	@echo "make coverage          Print the unit test coverage report"
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
test: backend-tests frontend-tests

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
functests: build/manifest.json
	@tox -qe functests

.PHONY: docker
docker:
	@git archive --format=tar.gz HEAD | docker build -t hypothesis/lms:$(DOCKER_TAG) -

.PHONY: run-docker
run-docker:
	# To run the Docker container locally:
	# 1. make devdata
	# 2. make docker
	# 3. make run-docker
	@docker run \
		--add-host host.docker.internal:host-gateway \
		--net lms_default \
		-e DATABASE_URL=postgresql://postgres@postgres/postgres \
		-e BROKER_URL=amqp://guest:guest@localhost:5674// \
		-e FEATURE_FLAGS_COOKIE_SECRET=notasecret \
		-e H_API_URL_PRIVATE=http://host.docker.internal:5000/api/ \
		-e H_API_URL_PUBLIC=http://localhost:5000/api/ \
		-e H_AUTHORITY=lms.hypothes.is \
		-e RPC_ALLOWED_ORIGINS=http://localhost:5000 \
		-e VIA_URL=http://localhost:9083 \
		-e VIA_SECRET=not_a_secret \
		-e SESSION_COOKIE_SECRET=notasecret \
		-e OAUTH2_STATE_SECRET=notasecret \
		--env-file .devdata.env \
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

# Tell make how to compile requirements/*.txt files.
#
# `touch` is used to pre-create an empty requirements/%.txt file if none
# exists, otherwise tox crashes.
#
# $(subst) is used because in the special case of making requirements.txt we
# actually need to touch dev.txt not requirements.txt and we need to run
# `tox -e dev ...` not `tox -e requirements ...`
#
# $(basename $(notdir $@))) gets just the environment name from the
# requirements/%.txt filename, for example requirements/foo.txt -> foo.
requirements/%.txt: requirements/%.in
	@touch -a $(subst requirements.txt,dev.txt,$@)
	@tox -qe $(subst requirements,dev,$(basename $(notdir $@))) --run-command 'pip --quiet --disable-pip-version-check install pip-tools'
	@tox -qe $(subst requirements,dev,$(basename $(notdir $@))) --run-command 'pip-compile --allow-unsafe --generate-hashes --quiet $(args) $<'

# Inform make of the dependencies between our requirements files so that it
# knows what order to re-compile them in and knows to re-compile a file if a
# file that it depends on has been changed.
requirements/checkformatting.txt: requirements/format.txt
requirements/dev.txt: requirements/requirements.txt
requirements/tests.txt: requirements/requirements.txt
requirements/functests.txt: requirements/requirements.txt
requirements/bddtests.txt: requirements/requirements.txt
requirements/lint.txt: requirements/tests.txt requirements/functests.txt requirements/bddtests.txt

# Add a requirements target so you can just run `make requirements` to
# re-compile *all* the requirements files at once.
#
# This needs to be able to re-create requirements/*.txt files that don't exist
# yet or that have been deleted so it can't just depend on all the
# requirements/*.txt files that exist on disk $(wildcard requirements/*.txt).
#
# Instead we generate the list of requirements/*.txt files by getting all the
# requirements/*.in files from disk ($(wildcard requirements/*.in)) and replace
# the .in's with .txt's.
.PHONY: requirements requirements/
requirements requirements/: $(foreach file,$(wildcard requirements/*.in),$(basename $(file)).txt)

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
