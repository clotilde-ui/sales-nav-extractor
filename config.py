import os

# Délais entre actions (en secondes)
MIN_DELAY = 2
MAX_DELAY = 5

# Timeout pour le chargement des pages (en millisecondes)
PAGE_TIMEOUT = 30000

# Chemin du profil navigateur persistant
USER_DATA_DIR = os.path.expanduser("~/.sales-nav-export-profile")

# Chemin de sortie CSV par défaut
DEFAULT_OUTPUT = "leads_export.csv"

# En-têtes CSV
CSV_FIELDS = [
    "prenom",
    "nom",
    "headline",
    "description",
    "titre",
    "entreprise",
    "url_profil",
    "url_entreprise",
    "localisation",
    "tenureAtCompany",
    "tenureAtPosition",
    "startedOn",
    "annee_derniere_education",
    "annee_debut_experience",
    "annee_fin_experience",
    "domaine_entreprise",
]

# User-Agent réaliste
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)
