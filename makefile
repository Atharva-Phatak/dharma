PYTHON ?= python3.13

VENV_BASE  = .venv-base
VENV_INFRA = .venv-infra
VENV_DATA  = .venv-data
VENV_ALL   = .venv-all
VENV_LINT = .venv-lint

.PHONY: activate-base activate-infra activate-data activate-all clean

# -------------------------------------------------
# Macro: Ensure virtualenv exists
# -------------------------------------------------
define ENSURE_VENV
@if [ ! -d "$(1)" ]; then \
	echo "🔧 Creating virtual environment: $(1)"; \
	uv venv $(1) --python $(PYTHON); \
else \
	echo "✅ Virtual environment exists: $(1)"; \
fi
endef

# -------------------------------------------------
# Macro: Activate environment and sync deps
# $(1) = venv path
# $(2) = uv sync args (dependency groups)
# -------------------------------------------------
define ACTIVATE_ENV
	$(call ENSURE_VENV,$(1))
	@echo "source $(1)/bin/activate" > .venv_tmp_rc
	@echo "uv sync $(2) --active" >> .venv_tmp_rc
	@echo "echo '🐍 Activated $(1)'" >> .venv_tmp_rc
	@echo "rm -f .venv_tmp_rc" >> .venv_tmp_rc
	@bash --rcfile .venv_tmp_rc
endef

# -------------------------------------------------
# Public Targets
# -------------------------------------------------
activate-base:
	$(call ACTIVATE_ENV,$(VENV_BASE),)

activate-infra:
	$(call ACTIVATE_ENV,$(VENV_INFRA),--group infrastructure)

activate-data:
	$(call ACTIVATE_ENV,$(VENV_DATA),--group data-collection)

activate-lint:
	$(call ACTIVATE_ENV,$(VENV_LINT),--group lint)

activate-all:
	$(call ACTIVATE_ENV,$(VENV_ALL),--group infrastructure --group data-collection)

# -------------------------------------------------
# Cleanup
# -------------------------------------------------
clean:
	rm -rf $(VENV_BASE) $(VENV_INFRA) $(VENV_DATA) $(VENV_ALL)
