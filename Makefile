.PHONY: clean
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	rm .pydeps

.PHONY: dev
dev: .pydeps
	python lti.py

.pydeps: requirements.txt
	@echo installing python dependencies
	@pip install --use-wheel -r requirements-dev.in
	@touch $@
