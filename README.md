# Sales Navigator Export Tool

Outil Python qui automatise l'export des résultats de recherche de leads depuis LinkedIn Sales Navigator vers un fichier CSV via Playwright.

## Installation

```bash
pip install -r requirements.txt
playwright install chromium
```

## Utilisation

### 1. Connexion initiale

Ouvrir le navigateur pour se connecter manuellement à Sales Navigator (la session est persistée) :

```bash
python main.py --login
```

### 2. Export des leads

Lancer une recherche dans Sales Navigator, copier l'URL, puis :

```bash
python main.py --url "https://www.linkedin.com/sales/search/people?..." -o leads.csv
```

### 3. Export détaillé

Visite chaque profil pour récupérer éducation et expérience (plus lent) :

```bash
python main.py --url "..." --detailed -o leads.csv
```

## Options

| Option | Description | Défaut |
|---|---|---|
| `--url` | URL de la recherche Sales Navigator | obligatoire |
| `--output`, `-o` | Chemin du fichier CSV de sortie | `leads_export.csv` |
| `--max-pages` | Nombre max de pages à scraper | toutes |
| `--detailed` | Visiter chaque profil (éducation, expérience) | non |
| `--login` | Ouvrir le navigateur pour se connecter | non |

## Champs exportés

| Champ | Source |
|---|---|
| `prenom` | Carte de lead |
| `nom` | Carte de lead |
| `headline` | Carte de lead |
| `description` | Carte de lead (section "À propos") |
| `titre` | Carte de lead |
| `entreprise` | Carte de lead |
| `url_profil` | Carte de lead |
| `url_entreprise` | Carte de lead (`linkedin.com/company/{id}`) |
| `localisation` | Carte de lead |
| `tenureAtCompany` | Carte de lead |
| `tenureAtPosition` | Carte de lead |
| `startedOn` | Carte de lead |
| `annee_derniere_education` | Page profil (`--detailed`) |
| `annee_debut_experience` | Page profil (`--detailed`) |
| `annee_fin_experience` | Page profil (`--detailed`) |
| `domaine_entreprise` | Page profil (`--detailed`) |

## Interface web (Streamlit)

Une interface web est aussi disponible pour lancer les exports sans passer par le terminal :

```bash
streamlit run app.py
```

L'interface permet de :
- Se connecter a LinkedIn (bouton dans la sidebar)
- Coller l'URL de recherche Sales Navigator
- Configurer le nombre de pages et le mode detaille
- Visualiser les resultats dans un tableau
- Telecharger le CSV directement depuis le navigateur

## Structure du projet

```
config.py       # Configuration (délais, champs CSV, chemins)
main.py         # Point d'entrée CLI
app.py          # Interface web Streamlit
scraper.py      # Logique de scraping Playwright
parser.py       # Extraction des champs depuis le DOM
exporter.py     # Export CSV
```
