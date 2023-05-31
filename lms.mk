requirements/bddtests.txt: requirements/prod.txt
requirements/lint.txt: requirements/bddtests.txt

.PHONY: bddtests
$(call help,make bddtests,"run the BDD tests")
bddtests: python
	@pyenv exec tox -qe bddtests

sure: bddtests
