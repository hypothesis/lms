DOCKER_TAG = dev

.PHONY: clean
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	rm -f .pydeps

.PHONY: dev
dev: .pydeps
	gunicorn --paste conf/development.ini

.PHONY: shell
shell: .pydeps
	pshell conf/development.ini

.PHONY: test
test:
	$(GULP) test
	@pip install -q tox
	tox

.PHONY: coverage
coverage: .coverage
	@pip install -q tox
	tox -e coverage

.PHONY: codecov
codecov: .coverage
	@pip install -q tox
	tox -e codecov

.PHONY: lint
lint:
	@pip install -q tox
	tox -e lint

.PHONY: docker
docker:
	git archive HEAD | docker build -t hypothesis/lms:$(DOCKER_TAG) -

.pydeps: requirements.txt requirements-dev.in
	@echo installing python dependencies
	@pip install --use-wheel -r requirements-dev.in
	@touch $@

GULP := node_modules/.bin/gulp

build:
	$(GULP) build

watch:
	$(GULP) watch

client_test:
	$(GULP) test