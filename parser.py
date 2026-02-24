import re


# Pattern pour supprimer les emojis
_EMOJI_RE = re.compile(
    "["
    "\U0001f600-\U0001f64f"  # emoticons
    "\U0001f300-\U0001f5ff"  # symbols & pictographs
    "\U0001f680-\U0001f6ff"  # transport & map
    "\U0001f1e0-\U0001f1ff"  # flags
    "\U0001f900-\U0001f9ff"  # supplemental symbols
    "\U0001fa00-\U0001fa6f"  # chess symbols
    "\U0001fa70-\U0001faff"  # symbols extended-A
    "\U00002702-\U000027b0"  # dingbats
    "\U0000fe00-\U0000fe0f"  # variation selectors
    "\U0000200d"             # zero width joiner
    "\U000020e3"             # combining enclosing keycap
    "\U00002600-\U000026ff"  # misc symbols
    "\U0000231a-\U0000231b"
    "\U00002934-\U00002935"
    "\U000025aa-\U000025ab"
    "\U000025fb-\U000025fe"
    "\U00002b05-\U00002b07"
    "\U00002b1b-\U00002b1c"
    "\U00002b50"
    "\U00002b55"
    "\U00003030"
    "\U0000303d"
    "\U00003297"
    "\U00003299"
    "]+",
    flags=re.UNICODE,
)


def _clean_emojis(text: str) -> str:
    """Supprime les emojis et espaces superflus."""
    return _EMOJI_RE.sub("", text).strip()


def parse_lead_card(card) -> dict:
    """Extrait les champs d'une carte de lead sur la page de résultats."""
    lead = {}

    # Nom complet (nettoyé des emojis)
    try:
        name_span = card.query_selector("span[data-anonymize='person-name']")
        if name_span:
            full_name = name_span.inner_text().strip()
            parts = full_name.split(" ", 1)
            lead["prenom"] = _clean_emojis(parts[0]) if parts else ""
            lead["nom"] = _clean_emojis(parts[1]) if len(parts) > 1 else ""
    except Exception:
        pass

    # URL profil (lien parent du nom)
    try:
        profile_link = card.query_selector(
            "a[data-control-name='view_lead_panel_via_search_lead_name']"
        )
        if profile_link:
            href = profile_link.get_attribute("href")
            if href:
                lead["url_profil"] = _to_absolute(href)
    except Exception:
        pass

    # Headline (ligne sous le nom = subtitle complet)
    try:
        subtitle_el = card.query_selector(".artdeco-entity-lockup__subtitle")
        if subtitle_el:
            lead["headline"] = subtitle_el.inner_text().strip()
    except Exception:
        pass

    # Description (section "À propos")
    try:
        blurb_el = card.query_selector("[data-anonymize='person-blurb']")
        if blurb_el:
            lead["description"] = blurb_el.inner_text().strip()
    except Exception:
        pass

    # Titre / Poste + Entreprise
    try:
        title_el = card.query_selector("[data-anonymize='title']")
        if title_el:
            raw = title_el.inner_text().strip()
            for sep in [" at ", " chez ", " @ "]:
                if sep in raw:
                    parts = raw.split(sep, 1)
                    lead["titre"] = parts[0].strip()
                    lead["entreprise"] = parts[1].strip()
                    break
            else:
                lead["titre"] = raw
    except Exception:
        pass

    # Entreprise (sélecteur dédié, si pas déjà trouvée)
    if "entreprise" not in lead:
        try:
            company_el = card.query_selector(
                "a[data-anonymize='company-name'], [data-anonymize='company-name']"
            )
            if company_el:
                lead["entreprise"] = company_el.inner_text().strip()
        except Exception:
            pass

    # URL entreprise (format linkedin.com/company/{id})
    try:
        company_link = card.query_selector("a[data-anonymize='company-name']")
        if company_link:
            href = company_link.get_attribute("href") or ""
            match = re.search(r"/company/(\d+)", href)
            if match:
                lead["url_entreprise"] = f"https://www.linkedin.com/company/{match.group(1)}"
    except Exception:
        pass

    # Localisation
    try:
        loc_el = card.query_selector("[data-anonymize='location']")
        if loc_el:
            lead["localisation"] = loc_el.inner_text().strip()
    except Exception:
        pass

    # Tenure et startedOn (depuis le metadata "X ans à ce poste / dans l'entreprise")
    try:
        metadata_el = card.query_selector(".artdeco-entity-lockup__metadata")
        if metadata_el:
            raw = metadata_el.inner_text()
            # Extraire tenure at position (ex: "2 ans 3 mois" ou "3 mois")
            pos_match = re.search(
                r"((?:\d+\s*ans?)?\s*(?:\d+\s*mois)?)\s*à ce poste", raw
            )
            if pos_match and pos_match.group(1).strip():
                lead["tenureAtPosition"] = pos_match.group(1).strip()
            # Extraire tenure at company
            comp_match = re.search(
                r"((?:\d+\s*ans?)?\s*(?:\d+\s*mois)?)\s*dans l.entreprise", raw
            )
            if comp_match and comp_match.group(1).strip():
                lead["tenureAtCompany"] = comp_match.group(1).strip()
            # startedOn : extraire la date si présente (format "depuis mois année")
            start_match = re.search(
                r"depuis\s+([\w]+\s+\d{4})", raw
            )
            if start_match:
                lead["startedOn"] = start_match.group(1)
    except Exception:
        pass

    return lead


def parse_lead_detail(page) -> dict:
    """Extrait les infos détaillées depuis la page profil d'un lead."""
    detail = {}

    # Dernière éducation — année
    try:
        edu_section = page.query_selector(
            "section.education, [data-x--education-history]"
        )
        if edu_section:
            date_els = edu_section.query_selector_all(".date-range span, .pv-entity__dates span")
            years = _extract_years_from_elements(date_els)
            if years:
                detail["annee_derniere_education"] = str(max(years))
    except Exception:
        pass

    # Expérience — première et dernière année
    try:
        exp_section = page.query_selector(
            "section.experience, [data-x--experience]"
        )
        if exp_section:
            date_els = exp_section.query_selector_all(".date-range span, .pv-entity__dates span")
            years = _extract_years_from_elements(date_els)
            if years:
                detail["annee_debut_experience"] = str(min(years))
                detail["annee_fin_experience"] = str(max(years))
    except Exception:
        pass

    # Domaine entreprise
    try:
        industry_el = page.query_selector(
            "[data-anonymize='industry'], .industry, .top-card-layout__entity-info-container .industry"
        )
        if industry_el:
            detail["domaine_entreprise"] = industry_el.inner_text().strip()
    except Exception:
        pass

    return detail


def _extract_years_from_elements(elements) -> list[int]:
    """Extrait les années (4 chiffres) depuis une liste d'éléments DOM."""
    years = []
    for el in elements:
        try:
            text = el.inner_text()
            found = re.findall(r"\b(19|20)\d{2}\b", text)
            years.extend(int(y) for y in found)
        except Exception:
            pass
    return years


def _to_absolute(href: str) -> str:
    """Convertit un href relatif en URL absolue LinkedIn."""
    if href.startswith("http"):
        return href
    return f"https://www.linkedin.com{href}"
