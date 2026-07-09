PYTHON ?= ../FXCarry/.venv/bin/python
FXCARRY_ROOT ?= $(abspath ../FXCarry)

.PHONY: test-tp

test-tp:
	PYTHONPATH="src:$(FXCARRY_ROOT)/src" $(PYTHON) -m pytest tests/tp_sleeve -q
