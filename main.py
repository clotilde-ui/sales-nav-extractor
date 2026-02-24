import argparse

from config import DEFAULT_OUTPUT
from exporter import export_to_csv
from scraper import open_browser_for_login, scrape_leads


def main():
    parser = argparse.ArgumentParser(
        description="Export des leads LinkedIn Sales Navigator vers CSV"
    )
    parser.add_argument(
        "--url",
        help="URL de la recherche Sales Navigator",
    )
    parser.add_argument(
        "--output", "-o",
        default=DEFAULT_OUTPUT,
        help=f"Chemin du fichier CSV de sortie (défaut : {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Nombre max de pages à scraper (défaut : toutes)",
    )
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Visiter chaque profil pour récupérer éducation/expérience (plus lent)",
    )
    parser.add_argument(
        "--login",
        action="store_true",
        help="Ouvrir le navigateur pour se connecter manuellement",
    )

    args = parser.parse_args()

    if args.login:
        open_browser_for_login()
        if not args.url:
            return

    if not args.url:
        parser.error("--url est obligatoire (sauf avec --login seul)")

    leads = scrape_leads(
        search_url=args.url,
        max_pages=args.max_pages,
        detailed=args.detailed,
    )

    if leads:
        export_to_csv(leads, args.output)
    else:
        print("[!] Aucun lead trouvé.")


if __name__ == "__main__":
    main()
