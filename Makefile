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
	@echo "make docker            Make the app's Docker image"
	@echo "make clean             Delete development artefacts (cached files, "
	@echo "                       dependencies, etc)"

.PHONY: dev
dev: build/manifest.json
	tox -e py36-dev

.PHONY: shell
shell:
	tox -e py36-dev -- pshell conf/development.ini

# FIXME: This requires psql to be installed locally.
# It should use psql from docker / docker-compose.
.PHONY: sql
sql:
	psql postgresql://postgres@localhost:5433/postgres

.PHONY: lint
lint:
	tox -e py36-lint
	$(GULP) lint

.PHONY: format
format:
	tox -e py36-format

.PHONY: checkformatting
checkformatting:
	tox -e py36-checkformatting

.PHONY: test
test: node_modules/.uptodate
	tox -e py36-tests
	$(GULP) test

.PHONY: coverage
coverage:
	tox -e py36-coverage

.PHONY: codecov
codecov:
	tox -e py36-codecov

.PHONY: docstrings
docstrings:
	tox -e py36-docstrings

.PHONY: checkdocstrings
checkdocstrings:
	tox -e py36-checkdocstrings

.PHONY: docker
docker:
	git archive --format=tar.gz HEAD | docker build -t hypothesis/lms:$(DOCKER_TAG) -

.PHONY: clean
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	rm -f node_modules/.uptodate
	rm -rf build

DOCKER_TAG = dev

GULP := node_modules/.bin/gulp

build/manifest.json: node_modules/.uptodate
	$(GULP) build

node_modules/.uptodate: package.json
	@echo installing javascript dependencies
	@node_modules/.bin/check-dependencies 2>/dev/null || yarn --ignore-engines install
	@touch $@
