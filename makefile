


# ============================================================
# 📚 Commande HELP - Affiche toutes les commandes disponibles
# ============================================================
help: ## Afficher la liste des commandes disponibles et leur usage
	@echo "📚 Liste des commandes disponibles :"
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'



auto-setup: ## Installer les dépendances uv
	@echo "[INFO] Installation dépendances (dev + docs)"
	@uv install --with dev,docs || { \
		if [ "$(STRICT)" = "1" ]; then \
			echo "[ERR ] Echec auto-setup"; exit 1; \
		else \
			echo "[WARN] Echec ignoré (STRICT=0): auto-setup"; \
		fi; \
	}

auto-tests: ## Lancer les tests unitaires
	@echo "[INFO] Tests unitaires (pytest)"
	@uv run pytest -q || { \
		if [ "$(STRICT)" = "1" ]; then \
			echo "[ERR ] Echec tests unitaires"; exit 1; \
		else \
			echo "[WARN] Echec ignoré (STRICT=0): tests unitaires"; \
		fi; \
	}

auto-security: ## Audit sécurité (Bandit) avec rapports dans REPORT_DIR
	@mkdir -p "$(REPORT_DIR)"
	@echo "[INFO] Audit sécurité Bandit (JSON)"
	@uv run bandit -r "$(CURDIR)/xcore" -f json -o "$(REPORT_DIR)/security-bandit.json" 2> "$(REPORT_DIR)/security-bandit.stderr.log" || { \
		if grep -q "ast' has no attribute 'Num'" "$(REPORT_DIR)/security-bandit.stderr.log"; then \
			echo "[WARN] Bandit a crashé (incompatibilité ast.Num)"; \
			echo '{"status":"failed","reason":"Bandit internal error: ast.Num incompatibility","tool":"bandit"}' > "$(REPORT_DIR)/security-bandit.json"; \
			echo "Bandit failed due to internal compatibility error (ast.Num)." > "$(REPORT_DIR)/security-bandit.txt"; \
			exit 0; \
		fi; \
		if [ "$(STRICT)" = "1" ]; then \
			echo "[ERR ] Echec audit Bandit JSON"; exit 1; \
		else \
			echo "[WARN] Echec ignoré (STRICT=0): audit Bandit JSON"; \
		fi; \
	}
	@echo "[INFO] Audit sécurité Bandit (TXT)"
	@uv run bandit -r "$(CURDIR)/xcore" -f txt -o "$(REPORT_DIR)/security-bandit.txt" 2>> "$(REPORT_DIR)/security-bandit.stderr.log" || { \
		if [ "$(STRICT)" = "1" ]; then \
			echo "[ERR ] Echec audit Bandit TXT"; exit 1; \
		else \
			echo "[WARN] Echec ignoré (STRICT=0): audit Bandit TXT"; \
		fi; \
	}
	@echo "[INFO] Rapports sécurité:"
	@echo "[INFO] - $(REPORT_DIR)/security-bandit.json"
	@echo "[INFO] - $(REPORT_DIR)/security-bandit.txt"
	@echo "[INFO] - $(REPORT_DIR)/security-bandit.stderr.log"


auto-all: auto-setup auto-tests auto-security auto-docs ## Exécuter toute la chaîne auto


# ============================================================
# 🧹 Nettoyage fichiers Python compilés
# ============================================================

clean: ## Supprimer __pycache__ et fichiers *.pyc, *.pyo
	@clear
	@echo "🧹 Nettoyage des fichiers inutiles..."
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f \( -name "*.backup" -o -name "*.backup" \) -exec rm -f {} +
	@find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -exec rm -f {} +

# ============================================================
# 📦 Installation & initialisation projet
# ============================================================

install: ## Installer les dépendances Python via uv
	@uv lock

# ============================================================
# 📌 Cibles "PHONY" - éviter conflits avec fichiers du même nom
# ============================================================

.PHONY: help automate auto-all auto-env auto-setup auto-tests auto-security auto-docs add-plugin link unlink clean install init run-dev run-st pip-Noa deploy remove-app repaire-ng start stop restart status uv-ri pre-commit logs logs-live logs-debug logs-info logs-warning logs-error logs-critical logs-auth logs-db logs-api logs-plugins logs-tasks logs-email logs-clean logs-stats logs-search logs-today logs-last-hour logs-test logs-demo

# ============================================================
# 📊 Commandes de gestion des logs
# ============================================================

build: ## Build complet du projet (clean + install + lint-fix + format)
	@echo "🏗️  CONSTRUCTION DU PROJET"
	@echo "==========================="
	@echo ""
	@echo "🧹 1. Nettoyage des fichiers compilés..."
	@$(MAKE) clean
	@echo ""
	@echo "📦 2. Installation des dépendances..."
	@$(MAKE) install
	@echo ""
	@echo "🔧 3. Correction automatique du code..."
	@$(MAKE) lint-fix
	@echo ""
	@echo "✅ Build terminé avec succès!"

build-prod: ## Build pour production (build + tests + validation)
	@echo "🚀 BUILD PRODUCTION"
	@echo "=================="
	@echo ""
	@$(MAKE) build
	@echo ""
	@echo "🧪 5. Exécution des tests..."
	@$(MAKE) test
	@echo ""
	@echo "🔒 6. Validation sécurité..."
	@$(MAKE) security-check
	@echo ""
	@uv build --no-cache
	@echo "🎉 Build production prêt!"


build-fast: ## Build rapide (clean + install uniquement)
	@echo "⚡ BUILD RAPIDE"
	@echo "=============="
	@$(MAKE) clean
	@$(MAKE) install
	@echo "✅ Build rapide terminé!"

lint-fix: ## Correction automatique des erreurs de linting (SAFE - préserve imports)
	@echo "🔧 Correction automatique du code (mode SAFE)..."
	@echo "📋 1. Correction autopep8 (lignes longues, espaces)..."
	@uv run autopep8 --in-place --recursive --exclude=alembic,static,__pycache__ .
	@echo "📋 2. Tri des imports avec isort..."
	@uv run isort . --skip=alembic --skip=static --skip=__pycache__
	@echo "📋 3. Formatage avec black..."
	@uv run black . --exclude="(alembic|static|__pycache__)"
	@echo "📋 4. Suppression CONSERVATIVE des variables inutiles (préserve imports)..."
	@uv run autoflake --in-place --recursive --remove-unused-variables --ignore-init-module-imports --exclude=alembic,static,__pycache__ .
	@echo "✅ Correction automatique terminée (imports préservés)!"

lint-check: ## Vérifier le linting sans modifier les fichiers (pour le CI)
	@echo "🔍 Vérification du code (mode CHECK)..."
	@echo "📋 1. Vérification black..."
	@uv run black . --check --exclude="(alembic|static|__pycache__)"
	@echo "📋 2. Vérification isort..."
	@uv run isort . --check-only --skip=alembic --skip=static --skip=__pycache__
	@echo "📋 3. Vérification flake8..."
	@uv run flake8 .
	@echo "✅ Vérification terminée!"

pre-commit-install: ## Installer les hooks de pre-commit
	@echo "📥 Installation des hooks pre-commit..."
	@uv run pre-commit install

pre-commit-run: ## Lancer manuellement les hooks sur tous les fichiers
	@echo "🚀 Lancement de pre-commit sur tous les fichiers..."
	@uv run pre-commit run --all-files

pre-commit: pre-commit-run ## Alias pour pre-commit-run


auto-fix: ## Alias pour lint-fix (correction automatique sécurisée)
	@$(MAKE) lint-fix

lint-preview: ## Prévisualiser les corrections sans les appliquer
	@echo "👀 Prévisualisation des corrections autopep8:"
	@uv run autopep8 --diff --recursive --exclude=alembic,static,__pycache__ . | head -50
	@echo ""
	@echo "👀 Prévisualisation du formatage black:"
	@uv run black --diff . --exclude="(alembic|static|__pycache__)" | head -30

lint-safe: ## Linting avec configuration adaptée à FastHTML
	@echo "🔍 Vérification du code (compatible FastHTML)..."
	@uv run flake8 .

test: ## Exécution des tests
	@echo "🧪 Exécution des tests..."
	@if [ -d "tests" ]; then \
		uv run pytest tests/ --cov --cov-branch --cov=src --cov-report=xml; \
	else \
		echo "⚠️  Dossier tests/ non trouvé"; \
		echo "💡 Créez des tests pour améliorer la qualité"; \
		fi
