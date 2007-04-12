all: test doc
	@echo "If the tests pass and the docs are created you should be fine" 


doc: 
	@${MAKE} -C docs all

test: 
	@python tests/runalltests.py

clean: 
	@find . -name "*.pyc" -exec rm {} \;
	@find . -name "*~" -exec rm {} \;
	@${MAKE} -C docs clean
