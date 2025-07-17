
# Neper-Data – Analyse intelligente d'articles web

Neper-Data est une application Flask avec interface HTML+JS qui permet d’analyser automatiquement **un ou plusieurs articles en ligne** à partir de leurs URL. L’application utilise l’API **Google Cloud Natural Language v1** pour :

- Extraire les **entités** du titre (avec **saillance**)
- Classer le contenu (avec une **confiance** sur la catégorisation)
- **Filtrer** les résultats selon deux seuils paramétrables
- **Exporter** les résultats en `.CSV` ou `.XLSX`

---

## Fonctionnalités principales

- Analyse **d’un seul article** avec résultats affichés dans une modale
- Analyse **de plusieurs articles à la fois**
-  **Filtrage par seuil** :
  - `threshold` → niveau de confiance pour les catégories (`0.0` à `1.0`)
  - `salience` → importance des entités extraites du titre (`0.0` à `1.0`)
-  Export des résultats :
  -  CSV (`.csv`)
  - Excel (`.xlsx`)
-  Supporte les nombres à virgule **française** (`0,3` devient `0.3`)
-  Authentification basique (`admin/secret`)
-  API Search Console prête à l’emploi pour analyse SEO avancée

---

## Structure des fichiers

| Fichier | Rôle |
|--------|------|
| `app.py` | Backend Flask : routes `/submit_url`, `/submit_urls`, exports... |
| `article_processor.py` | Traitement des articles (Google API, filtrage, export) |
| `templates/index.html` | Formulaire utilisateur (un ou plusieurs articles) |
| `static/script.js` | JS : gestion formulaire, modale, exports |
| `static/style.css` | Style principal |
| `lifespan_processor.py` | (Optionnel) Analyse durée de vie via Search Console |

---

##  Installation & Lancement

1. **Clone** ce dépôt ou copie les fichiers
2. Installe les dépendances :

```bash
pip install -r requirements.txt
