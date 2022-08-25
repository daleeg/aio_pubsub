PYTHON ?= python3
PYTEST ?= pytest
MYPY ?= mypy

dist: clean
	$(PYTHON) setup.py sdist bdist_wheel

clean:
	-rm -r build dist aiopubsub_py3.egg-info

pypi:
	twine upload  dist/*