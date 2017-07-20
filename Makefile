.PHONY: clean
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	rm .pydeps

.PHONY: dev
dev: .pydeps
	@PYRAMID_RELOAD_TEMPLATES=1 gunicorn --reload --bind 'localhost:8001' 'lti.app:app()'

.PHONY: test
test:
	@pip install -q tox
	tox

.PHONY: coverage
coverage: .coverage
	@pip install -q tox
	tox -e coverage

.PHONY: codecov
codecov:
	@pip install -q tox
	tox -e codecov

.pydeps: requirements.txt
	@echo installing python dependencies
	@pip install --use-wheel -r requirements-dev.in
	@touch $@
