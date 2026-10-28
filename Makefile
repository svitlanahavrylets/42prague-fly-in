# Colors for terminal display
RED = \\033[0;31m
GREEN = \\033[0;32m
RESET = \\033[0m

UV      = uv
PYTHON  = $(UV) run python

all: install

install:
		$(UV) sync

run:
		@if [ ! -d ".venv" ]; then make install; fi
		$(PYTHON) main.py

debug:
		$(UV) run python -m pdb main.py 

lint:
		@if [ ! -d ".venv" ]; then $(MAKE) install; fi
		$(UV) run flake8 --exclude=.venv .
		$(UV) run mypy --exclude .venv --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs .

lint-strict:
		@if [ ! -d ".venv" ]; then $(MAKE) install; fi
		$(UV) run flake8 --exclude=.venv .
		$(UV) run mypy --exclude .venv --strict .

clean:
		rm -rf __pycache__
		rm -rf src/__pycache__
		rm -rf .mypy_cache
		rm -rf .pytest_cache
		rm -rf build/
		rm -rf dist/

fclean: clean
		rm -rf .venv
		rm -rf uv.lock

bonus:
		@echo "No bonus part in this project."


.PHONY: all install run debug lint lint-strict clean fclean bonus