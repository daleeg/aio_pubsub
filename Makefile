PYTHON ?= python3
PYTEST ?= pytest
MYPY ?= mypy

# Python implementation
PYTHON_IMPL = $(shell $(PYTHON) -c "import sys; print(sys.implementation.name)")

EXAMPLES = $(sort $(wildcard docs/examples/*.py docs/examples/*/*.py))

.PHONY: all lint init-hooks doc spelling test cov dist devel clean mypy
all: aioredis.egg-info lint doc cov

doc: spelling
	mkdocs build
spelling:
	@echo "Running spelling check"
	$(MAKE) -C docs spelling

mypy:
	$(MYPY)

test:
	$(PYTEST)

cov coverage:
	$(PYTEST) --cov

dist: clean
	$(PYTHON) setup.py sdist bdist_wheel

clean:
	-rm -r build dist aiopubsub_py3.egg-info
