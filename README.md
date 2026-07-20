
# Metropole Rafraichissante

## Contexte
Projet TER 2024-2025 realise avec Bordeaux Metropole dans le cadre du programme "Metropole rafraichissante".

Auteurs:
- Ahina DURRIEU
- Enzo QUATTROCHI
- Paul-Henri LEPLOMB

Objectif du projet:
- identifier des implantations d'espaces de fraicheur a moins de 300 m des habitants
- prioriser les habitants thermiquement vulnerables (classes 5 et 6)
- comparer couverture, cout et surface amenagee

## Structure du depot

- `scripts/` : pipeline principal Python
- `apps/` : applications Streamlit d'exploration
- `data/raw/` : donnees sources open data brutes
- `data/processed/` : donnees transformees essentielles au pipeline
- `data/outputs/` : sorties utiles a conserver (cartes, figures, logs)
- `docs/` : documentation projet, pipeline, sources et resultats
- `docs/reference/` : rapport TER, slides et documents de cadrage
- `legacy_cpp/` : prototype C++/Gurobi, hors pipeline principal
- `archive/` : scripts et restitutions historiques non retenus dans le flux principal

## Pipeline principal

Scripts principaux:
1. `python scripts/01_extract_fraicheur_geojson.py`
2. `python scripts/02_extract_habitants.py`
3. `python scripts/03_extract_emplacements.py`
4. `python scripts/04_filter_emplacements.py`
5. `python scripts/05_build_j_options.py`
6. `python scripts/06_build_aijc_dijc.py`
7. `python scripts/07_run_glouton.py`
8. `python scripts/08_analyze_results.py`

Applications:
- `c`
- `streamlit run apps/app_installation_viewer.py`

## Donnees processed essentielles

Les fichiers suivants sont centraux:
- `data/processed/habitants/habitants.csv`
- `data/processed/emplacements/emplacements_final.csv`
- `data/processed/matrices/j_options.csv`
- `data/processed/matrices/a_ijc.csv`
- `data/processed/matrices/d_ijc.csv`
- `data/processed/resultats/resultats_glouton.csv`
- `data/processed/resultats/resultats_glouton_all.csv`

## Resultats cles

Chiffres repris du rapport TER:
- 462829 habitants modelises
- 144757 habitants en classes 5-6
- 71.60% de couverture actuelle globale
- 83.39% de couverture actuelle des classes 5-6

Scenario glouton cible classes 5-6:
- 248 nouvelles installations
- 271016550 EUR de cout estime
- 492757 m2 de surface amenagee

## Documentation

- `docs/pipeline.md` : pipeline reel et dependances fichiers
- `docs/results.md` : sorties et chiffres a conserver
- `docs/data_sources.md` : sources de donnees et politique de versionnement

## Recommended entry point

Point d'entree recommande pour un tiers:
1. partir des donnees deja preparees dans `data/processed/`
2. lancer `python scripts/07_run_glouton.py`
3. lancer `python scripts/08_analyze_results.py`
4. consulter `data/processed/resultats/` puis `data/outputs/`

## Reproduction scope

Le scope de reproduction recommande pour partage data scientist est:
- reproduction du pipeline principal a partir de `data/processed/`
- execution du glouton et de l'analyse
- exploration via `apps/app.py` et `apps/app_installation_viewer.py`

La regeneration complete depuis toutes les donnees brutes (`data/raw/`) est possible, mais n'est pas le chemin prioritaire pour une premiere prise en main.

## Known limitations

- La regeneration complete de certaines matrices volumineuses (notamment via `scripts/06_build_aijc_dijc.py`) est couteuse en temps de calcul.
- Certaines etapes amont geospatiales sont plus exploratoires et moins garanties que le pipeline principal, en particulier l'enrichissement complet des emplacements avec `iris_code`.
- Le bloc C++ dans `legacy_cpp/` est conserve pour reference historique et est hors perimetre principal de reproduction.

## Remarques importantes

- Le depot a ete restructure pour separer le pipeline principal du legacy et des brouillons.
- Le bloc C++ est conserve comme archive technique et n'est pas necessaire pour reproduire les resultats Python.
- Certaines etapes amont restent a valider finement vis-a-vis du rapport, en particulier l'enrichissement complet des emplacements avec `iris_code`.
