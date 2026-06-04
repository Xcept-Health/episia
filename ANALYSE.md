# Analyse du projet Episia & recommandations

> Revue technique du dépôt `episia` (v0.1.2). État : bibliothèque Python ~18 200 lignes de code source, ~8 600 lignes de tests (≈1390 tests), couverture 80 %. Architecture saine et bien découpée — les remarques ci-dessous portent surtout sur l'**outillage**, la **CI/CD** et quelques **points de finition** avant un passage en v0.2 / v1.0.

## Vue d'ensemble

**Points forts (à conserver)**

- Architecture cohérente autour de deux conventions fortes : objets résultats unifiés (`EpiResult`) et template de modèle compartimental (`CompartmentalModel`). Facile à étendre.
- Séparation nette des responsabilités par module (`stats`, `models`, `viz`, `data`, `dhis2`, `core`, `api`).
- Validation scientifique systématique contre OpenEpi — gage de confiance majeur pour un outil de santé publique.
- Bonne densité de docstrings et de type hints ; suite de tests volumineuse et organisée.
- Contrainte « hors-ligne sauf DHIS2 » claire et respectée.

---

## Recommandations prioritaires

### 🔴 1. La CI ne teste rien

Le seul workflow d'intégration (`python-publish.yml`) **construit et publie sur PyPI** sur release — il ne lance **ni pytest, ni black, ni mypy, ni flake8**. Une régression peut donc être publiée sans filet.

**Action :** ajouter un workflow `ci.yml` déclenché sur `push` / `pull_request` qui exécute la matrice Python 3.9→3.12 :

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: black --check src/ tests/
      - run: isort --check-only src/ tests/
      - run: flake8 src/
      - run: mypy src/
      - run: pytest tests/ --cov=episia --cov-report=xml -n auto
```

Idéalement, faire dépendre le job de publication de la réussite des tests.

### 🔴 2. Configuration d'outillage dispersée / absente

`pyproject.toml` ne contient que `[build-system]` (3 lignes). Conséquences :

- Aucune config centralisée pour `black`, `isort`, `mypy`, `flake8`, `pytest` → comportement dépendant des défauts et des machines.
- `pytest` n'a pas de `testpaths`, de marqueurs ni d'`addopts`.

**Action :** centraliser dans `pyproject.toml` :

```toml
[tool.black]
line-length = 88
target-version = ["py39"]

[tool.isort]
profile = "black"

[tool.mypy]
python_version = "3.9"
warn_unused_ignores = true
ignore_missing_imports = true   # pour plotly/scipy sans stubs

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra"
```

### 🟠 3. Migrer la métadonnée projet vers `pyproject.toml`

Toute la configuration du paquet vit dans `setup.py` (style historique). Les standards actuels (PEP 621) recommandent `[project]` dans `pyproject.toml`. Le `setup.py` contient déjà un contournement révélateur (lecture de `__version__` par regex pour éviter `exec()` qui planterait à cause des imports relatifs) — la migration vers `[project] dynamic = ["version"]` rend ce hack inutile.

> Note : `setup.py` déclare `Cython` comme dépendance de build, mais **aucun fichier `.pyx` n'existe** — le paquet est 100 % Python. À retirer de `build-system.requires` tant qu'il n'y a pas de code Cython (cela évite une dépendance de build inutile).

### 🟠 4. Distribuer les type hints (PEP 561)

Le code est largement typé, mais il n'y a **pas de fichier `py.typed`**. Sans lui, mypy/pyright côté utilisateur **ignorent** vos annotations. Ajouter `src/episia/py.typed` (vide) et le déclarer dans `package_data`.

### 🟠 5. Pas de `CHANGELOG`

Le README annonce que les ruptures d'API seront « documentées dans le changelog », mais aucun fichier n'existe. Pour une lib en pré-1.0 où des breaking changes sont attendus, c'est important. Ajouter un `CHANGELOG.md` au format [Keep a Changelog](https://keepachangelog.com/).

---

## Recommandations secondaires

### 🟡 6. `print()` au lieu de `logging`

~60 appels `print()` dans le code source (hors `utilities.py`/`EpiLoader`, légitime pour l'animation terminal). Une bibliothèque ne devrait pas écrire directement sur stdout : cela pollue la sortie des applications hôtes et n'est pas filtrable. Introduire un logger (`logging.getLogger("episia")`) et y router les messages diagnostiques.

### 🟡 7. `pre-commit` listé mais non configuré

`pre-commit` est dans les dépendances `[dev]` mais il n'y a pas de `.pre-commit-config.yaml`. Ajouter le fichier (hooks black/isort/flake8/trailing-whitespace) pour que la dépendance serve réellement et garantisse le formatage avant commit.

### 🟡 8. Modules placeholder = fichiers vides

`simulation/` et `compatibility/` contiennent des fichiers `.py` **vides** (0 ligne : `networks.py`, `spatial.py`, `outbreak.py`, `openepi.py`, etc.). Importer ces sous-modules échouera silencieusement ou prêtera à confusion. Tant que le contenu n'arrive pas (v0.2+), soit les retirer du paquet, soit y mettre un `raise NotImplementedError` explicite avec un message « prévu pour v0.2 ».

### 🟡 9. Sécurité DHIS2

`DHIS2Client` stocke `self.password` en clair (attendu pour un client HTTP) et l'exemple du README met le mot de passe en dur. C'est acceptable mais : (a) privilégier `api_token` dans la doc, (b) montrer systématiquement la lecture depuis une variable d'environnement, (c) s'assurer que `__repr__`/logs ne révèlent jamais le mot de passe.

### 🟢 10. Refactorisation de gros fichiers

Quelques fichiers dépassent 700–980 lignes (`plotly_plotter.py` 981, `results.py` 781, `regression.py` 777, `sensitivity.py` 732, `utilities.py` 720). Rien de bloquant, mais surveiller `plotly_plotter.py` et `results.py` : si les classes de résultats continuent de croître, envisager de découper `results.py` par domaine (résultats stats vs modèles vs séries temporelles).

---

## Synthèse priorisée

| # | Sujet | Effort | Impact |
|---|-------|--------|--------|
| 1 | Workflow CI (tests + lint sur PR) | Faible | 🔴 Élevé |
| 2 | Config outils dans `pyproject.toml` | Faible | 🔴 Élevé |
| 3 | Migration métadonnée → `pyproject.toml` (PEP 621) | Moyen | 🟠 Moyen |
| 4 | `py.typed` (PEP 561) | Très faible | 🟠 Moyen |
| 5 | `CHANGELOG.md` | Faible | 🟠 Moyen |
| 6 | `logging` au lieu de `print()` | Moyen | 🟡 Moyen |
| 7 | `.pre-commit-config.yaml` | Faible | 🟡 Faible |
| 8 | Placeholders vides → NotImplementedError | Faible | 🟡 Faible |
| 9 | Durcissement secrets DHIS2 (doc + repr) | Faible | 🟡 Faible |
| 10 | Surveiller la taille des gros modules | — | 🟢 Faible |

**À traiter en premier (gros gain / faible coût) : 1, 2, 4, 5.**
