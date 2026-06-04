# Makefile — Episia
# Gestion du projet via uv. Lancer `make help` pour la liste des cibles.

# Outil de base
UV       ?= uv
PYTHON   ?= $(UV) run python
PYTEST   ?= $(UV) run pytest
SRC      := src
TESTS    := tests

# Exécute pytest en parallèle par défaut (pytest-xdist)
PYTEST_ARGS ?= -n auto

.DEFAULT_GOAL := help
.PHONY: help install dev sync lock test test-cov test-fast test-one \
        lint format format-check typecheck check build clean publish docs \
        precommit run

## help: Affiche cette aide
help:
	@echo "Cibles disponibles :"
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/## /  /'

## install: Installe le paquet seul (sans extras)
install:
	$(UV) pip install -e .

## dev: Installe le paquet avec les dépendances de développement
dev:
	$(UV) pip install -e ".[dev]"

## sync: Synchronise l'environnement avec les extras dev + docs
sync:
	$(UV) sync --extra dev --extra docs

## lock: Génère/met à jour le lockfile uv.lock
lock:
	$(UV) lock

## test: Lance toute la suite de tests
test:
	$(PYTEST) $(TESTS) $(PYTEST_ARGS)

## test-cov: Lance les tests avec rapport de couverture
test-cov:
	$(PYTEST) $(TESTS) --cov=episia --cov-report=term-missing --cov-report=html $(PYTEST_ARGS)

## test-fast: Lance les tests en s'arrêtant au premier échec
test-fast:
	$(PYTEST) $(TESTS) -x -q

## test-one: Lance un test ciblé — usage: make test-one T=tests/unit/test_stats.py::test_nom
test-one:
	$(PYTEST) $(T) -v

## lint: Vérifie le style (flake8 + isort + black en mode check)
lint: format-check typecheck
	$(UV) run flake8 $(SRC)

## format: Formate le code (black + isort)
format:
	$(UV) run isort $(SRC) $(TESTS)
	$(UV) run black $(SRC) $(TESTS)

## format-check: Vérifie le formatage sans modifier les fichiers
format-check:
	$(UV) run isort --check-only --diff $(SRC) $(TESTS)
	$(UV) run black --check --diff $(SRC) $(TESTS)

## typecheck: Vérifie les types avec mypy
typecheck:
	$(UV) run mypy $(SRC)

## check: Vérification complète (lint + types + tests) — utile en CI
check: lint test

## precommit: Lance tous les hooks pre-commit
precommit:
	$(UV) run pre-commit run --all-files

## docs: Construit la documentation Sphinx (HTML)
docs:
	$(UV) run sphinx-build -b html docs/source docs/source/_build/html

## build: Construit les distributions (sdist + wheel)
build: clean
	$(UV) build

## publish: Publie sur PyPI (nécessite des identifiants)
publish: build
	$(UV) publish

## run: Affiche la référence terminale (python -m episia)
run:
	$(PYTHON) -m episia

## clean: Supprime les artefacts de build, cache et couverture
clean:
	rm -rf build/ dist/ *.egg-info src/*.egg-info
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
