# Colors for terminal display
RESET   = \033[0m
BOLD    = \033[1m
RED     = \033[1;31m
GREEN   = \033[1;32m
YELLOW  = \033[1;33m
BLUE    = \033[1;34m
PINK    = \033[1;35m

UV      = uv
PYTHON  = $(UV) run python
FILE   ?= my_maps/example.txt
ARGS   ?=


all: install

install:
		@printf "$(BOLD)$(YELLOW)[INSTALL] Syncing project dependencies...$(RESET)\n"
		$(UV) sync
		@printf "$(BOLD)$(PINK)[INSTALL] Complete. Use 'make run' to launch the simulation.$(RESET)\n"

run:
		@if [ ! -d ".venv" ]; then make install; fi
		@printf "$(BOLD)$(GREEN)[RUN] Starting simulation with $(FILE)...$(RESET)\n"
		$(PYTHON) -m main $(FILE) $(ARGS)
		@printf "$(BOLD)$(PINK)[RUN] Simulation finished.$(RESET)\n"

debug:
		@printf "$(BOLD)$(BLUE)[DEBUG] Starting debugger for $(FILE)...$(RESET)\n"
		$(PYTHON) -m pdb main.py $(FILE) $(ARGS)
		@printf "$(BOLD)$(PINK)[DEBUG] Debugger exited.$(RESET)\n"

lint:
		@printf "$(BOLD)$(YELLOW)[LINT] Running flake8 and mypy checks...$(RESET)\n"
		@if [ ! -d ".venv" ]; then $(MAKE) install; fi
		$(UV) run flake8 --exclude=.venv .
		$(UV) run mypy --exclude .venv --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs .
		@printf "$(BOLD)$(PINK)[LINT] All checks passed.$(RESET)\n"

lint-strict:
		@printf "$(BOLD)$(YELLOW)[LINT-STRICT] Running flake8 and strict mypy checks...$(RESET)\n"
		@if [ ! -d ".venv" ]; then $(MAKE) install; fi
		$(UV) run flake8 --exclude=.venv .
		$(UV) run mypy --exclude .venv --strict .
		@printf "$(BOLD)$(PINK)[LINT-STRICT] All checks passed.$(RESET)\n"

clean:
		@printf "$(BOLD)$(RED)[CLEAN] Removing caches and build output...$(RESET)\n"
		rm -rf __pycache__
		rm -rf src/__pycache__
		rm -rf .mypy_cache
		rm -rf .pytest_cache
		rm -rf build/
		rm -rf dist/
		@printf "$(BOLD)$(GREEN)[CLEAN] Complete.$(RESET)\n"

fclean: clean
		@printf "$(BOLD)$(RED)[FCLEAN] Removing the virtual environment and lock file...$(RESET)\n"
		rm -rf .venv
		rm -rf uv.lock
		@printf "$(BOLD)$(GREEN)[FCLEAN] Complete.$(RESET)\n"


.PHONY: all install run debug lint lint-strict clean fclean bonus
