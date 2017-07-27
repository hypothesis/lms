.PHONY: clean
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	rm -f .pydeps

.PHONY: dev
dev: .pydeps canvas-auth.json
	gunicorn --paste conf/development.ini

.PHONY: shell
shell: .pydeps canvas-auth.json
	pshell conf/development.ini

.PHONY: test
test: canvas-auth.json
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

.pydeps: requirements.txt requirements-dev.in
	@echo installing python dependencies
	@pip install --use-wheel -r requirements-dev.in
	@touch $@

canvas-auth.json:
	echo '{}' > canvas-auth.json
