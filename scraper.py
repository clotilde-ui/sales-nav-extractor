import random
import time

from playwright.sync_api import sync_playwright

from config import (
    MAX_DELAY,
    MIN_DELAY,
    PAGE_TIMEOUT,
    USER_AGENT,
    USER_DATA_DIR,
)
from parser import parse_lead_card, parse_lead_detail


def random_delay():
    """Pause aléatoire entre actions."""
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))


def open_browser_for_login():
    """Ouvre le navigateur pour permettre la connexion manuelle."""
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            user_agent=USER_AGENT,
            viewport={"width": 1280, "height": 900},
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto("https://www.linkedin.com/sales/", timeout=PAGE_TIMEOUT)
        print("[*] Connectez-vous à LinkedIn Sales Navigator dans le navigateur.")
        print("[*] Fermez le navigateur une fois connecté pour sauvegarder la session.")
        try:
            # Attend que l'utilisateur ferme le navigateur
            page.wait_for_event("close", timeout=0)
        except Exception:
            pass
        try:
            context.close()
        except Exception:
            pass
        print("[+] Session sauvegardée.")


def scrape_leads(
    search_url: str,
    max_pages: int | None = None,
    detailed: bool = False,
    on_progress: callable = None,
) -> list[dict]:
    """Scrape les leads depuis une recherche Sales Navigator."""
    leads = []

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            user_agent=USER_AGENT,
            viewport={"width": 1280, "height": 900},
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.set_default_timeout(PAGE_TIMEOUT)

        page_num = 1
        current_url = search_url

        while True:
            if max_pages and page_num > max_pages:
                break

            print(f"[*] Page {page_num}...")
            page.goto(current_url, wait_until="domcontentloaded")
            random_delay()

            # Attendre le chargement des cartes de leads
            page.wait_for_selector(
                "li.artdeco-list__item, ol.search-results__result-list > li",
                timeout=PAGE_TIMEOUT,
            )

            # Scroller progressivement pour déclencher le lazy-loading
            _scroll_to_load_cards(page)

            cards = page.query_selector_all(
                "li.artdeco-list__item, ol.search-results__result-list > li"
            )
            print(f"    {len(cards)} cartes trouvées sur cette page")

            page_leads = 0
            for card in cards:
                lead = parse_lead_card(card)
                if not lead.get("prenom") and not lead.get("titre"):
                    continue
                page_leads += 1

                if detailed and lead.get("url_profil"):
                    detail = _visit_profile(page, lead["url_profil"])
                    lead.update(detail)

                leads.append(lead)

            print(f"    {page_leads} leads extraits")

            if on_progress:
                on_progress(page_num, max_pages)

            # Pagination — chercher le bouton "Next"
            next_btn = page.query_selector(
                "button.artdeco-pagination__button--next, "
                "button[aria-label='Next'], "
                "button[aria-label='Suivant']"
            )
            if next_btn and next_btn.is_enabled():
                next_btn.click()
                random_delay()
                current_url = page.url
                page_num += 1
            else:
                print("[*] Dernière page atteinte.")
                break

        context.close()

    print(f"[+] Total : {len(leads)} leads récupérés.")
    return leads


def _scroll_to_load_cards(page):
    """Scrolle chaque carte dans le viewport pour déclencher le lazy-loading."""
    cards = page.query_selector_all(
        "li.artdeco-list__item, ol.search-results__result-list > li"
    )
    for card in cards:
        card.scroll_into_view_if_needed()
        time.sleep(random.uniform(0.2, 0.4))
    # Revenir en haut pour la pagination
    page.evaluate("window.scrollTo(0, 0)")
    time.sleep(0.5)


def _visit_profile(page, profile_url: str) -> dict:
    """Visite le profil d'un lead et extrait les données détaillées."""
    original_url = page.url
    try:
        page.goto(profile_url, wait_until="domcontentloaded")
        random_delay()
        detail = parse_lead_detail(page)
    except Exception as e:
        print(f"    [!] Erreur profil {profile_url}: {e}")
        detail = {}
    finally:
        page.goto(original_url, wait_until="domcontentloaded")
        random_delay()
    return detail
