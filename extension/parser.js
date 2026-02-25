// Port de parser.py — extraction DOM des leads Sales Navigator

const _EMOJI_RE = new RegExp(
  "[" +
    "\u{1F600}-\u{1F64F}" + // emoticons
    "\u{1F300}-\u{1F5FF}" + // symbols & pictographs
    "\u{1F680}-\u{1F6FF}" + // transport & map
    "\u{1F1E0}-\u{1F1FF}" + // flags
    "\u{1F900}-\u{1F9FF}" + // supplemental symbols
    "\u{1FA00}-\u{1FA6F}" + // chess symbols
    "\u{1FA70}-\u{1FAFF}" + // symbols extended-A
    "\u{2702}-\u{27B0}" + // dingbats
    "\u{FE00}-\u{FE0F}" + // variation selectors
    "\u{200D}" + // zero width joiner
    "\u{20E3}" + // combining enclosing keycap
    "\u{2600}-\u{26FF}" + // misc symbols
    "\u{231A}-\u{231B}" +
    "\u{2934}-\u{2935}" +
    "\u{25AA}-\u{25AB}" +
    "\u{25FB}-\u{25FE}" +
    "\u{2B05}-\u{2B07}" +
    "\u{2B1B}-\u{2B1C}" +
    "\u{2B50}" +
    "\u{2B55}" +
    "\u{3030}" +
    "\u{303D}" +
    "\u{3297}" +
    "\u{3299}" +
    "]+",
  "gu"
);

function cleanEmojis(text) {
  return text.replace(_EMOJI_RE, "").trim();
}

function toAbsolute(href) {
  if (href.startsWith("http")) return href;
  return "https://www.linkedin.com" + href;
}

function salesNavToLinkedinUrl(url) {
  // Convertit une URL Sales Navigator en URL profil LinkedIn classique
  // Ex: /sales/lead/ACwAACpkZ6QB...,NAME_SEARCH,kNOb?_ntb=... → https://www.linkedin.com/in/ACwAACpkZ6QB...
  const match = url.match(/\/sales\/lead\/([A-Za-z0-9_-]+)/);
  if (match) {
    return "https://www.linkedin.com/in/" + match[1];
  }
  return url.split("?")[0];
}

function extractYearsFromElements(elements) {
  const years = [];
  for (const el of elements) {
    try {
      const text = el.textContent || "";
      const found = text.match(/\b(19|20)\d{2}\b/g);
      if (found) {
        years.push(...found.map(Number));
      }
    } catch (_) {}
  }
  return years;
}

function parseLeadCard(card) {
  const lead = {};

  // Nom complet
  try {
    const nameSpan = card.querySelector("span[data-anonymize='person-name']");
    if (nameSpan) {
      const fullName = nameSpan.textContent.trim();
      const parts = fullName.split(" ", 2);
      lead.prenom = cleanEmojis(parts[0] || "");
      lead.nom = cleanEmojis(parts.slice(1).join(" ") || "");
    }
  } catch (_) {}

  // URL profil
  try {
    const profileLink = card.querySelector(
      "a[data-control-name='view_lead_panel_via_search_lead_name']"
    );
    if (profileLink) {
      const href = profileLink.getAttribute("href");
      if (href) lead.url_profil = salesNavToLinkedinUrl(toAbsolute(href));
    }
  } catch (_) {}

  // Headline
  try {
    const subtitleEl = card.querySelector(".artdeco-entity-lockup__subtitle");
    if (subtitleEl) {
      lead.headline = subtitleEl.textContent.trim();
    }
  } catch (_) {}

  // Description
  try {
    const blurbEl = card.querySelector("[data-anonymize='person-blurb']");
    if (blurbEl) {
      lead.description = blurbEl.textContent.trim();
    }
  } catch (_) {}

  // Titre / Poste + Entreprise
  try {
    const titleEl = card.querySelector("[data-anonymize='title']");
    if (titleEl) {
      const raw = titleEl.textContent.trim();
      let matched = false;
      for (const sep of [" at ", " chez ", " @ "]) {
        if (raw.includes(sep)) {
          const parts = raw.split(sep, 2);
          lead.titre = parts[0].trim();
          lead.entreprise = parts[1].trim();
          matched = true;
          break;
        }
      }
      if (!matched) {
        lead.titre = raw;
      }
    }
  } catch (_) {}

  // Entreprise (sélecteur dédié, si pas déjà trouvée)
  if (!lead.entreprise) {
    try {
      const companyEl = card.querySelector(
        "a[data-anonymize='company-name'], [data-anonymize='company-name']"
      );
      if (companyEl) {
        lead.entreprise = companyEl.textContent.trim();
      }
    } catch (_) {}
  }

  // URL entreprise
  try {
    const companyLink = card.querySelector("a[data-anonymize='company-name']");
    if (companyLink) {
      const href = companyLink.getAttribute("href") || "";
      const match = href.match(/\/company\/(\d+)/);
      if (match) {
        lead.url_entreprise =
          "https://www.linkedin.com/company/" + match[1];
      }
    }
  } catch (_) {}

  // Localisation
  try {
    const locEl = card.querySelector("[data-anonymize='location']");
    if (locEl) {
      lead.localisation = locEl.textContent.trim();
    }
  } catch (_) {}

  // Tenure et startedOn
  try {
    const metadataEl = card.querySelector(
      ".artdeco-entity-lockup__metadata"
    );
    if (metadataEl) {
      const raw = metadataEl.textContent;
      const posMatch = raw.match(
        /((?:\d+\s*ans?)?\s*(?:\d+\s*mois)?)\s*à ce poste/
      );
      if (posMatch && posMatch[1].trim()) {
        lead.tenureAtPosition = posMatch[1].trim();
      }
      const compMatch = raw.match(
        /((?:\d+\s*ans?)?\s*(?:\d+\s*mois)?)\s*dans l.entreprise/
      );
      if (compMatch && compMatch[1].trim()) {
        lead.tenureAtCompany = compMatch[1].trim();
      }
      const startMatch = raw.match(/depuis\s+([\w]+\s+\d{4})/);
      if (startMatch) {
        lead.startedOn = startMatch[1];
      }
    }
  } catch (_) {}

  return lead;
}

function parseLeadDetail(doc) {
  const detail = {};

  // Dernière éducation — année
  try {
    const eduSection = doc.querySelector(
      "section.education, [data-x--education-history]"
    );
    if (eduSection) {
      const dateEls = eduSection.querySelectorAll(
        ".date-range span, .pv-entity__dates span"
      );
      const years = extractYearsFromElements(dateEls);
      if (years.length) {
        detail.annee_derniere_education = String(Math.max(...years));
      }
    }
  } catch (_) {}

  // Expérience — première et dernière année
  try {
    const expSection = doc.querySelector(
      "section.experience, [data-x--experience]"
    );
    if (expSection) {
      const dateEls = expSection.querySelectorAll(
        ".date-range span, .pv-entity__dates span"
      );
      const years = extractYearsFromElements(dateEls);
      if (years.length) {
        detail.annee_debut_experience = String(Math.min(...years));
        detail.annee_fin_experience = String(Math.max(...years));
      }
    }
  } catch (_) {}

  // Domaine entreprise
  try {
    const industryEl = doc.querySelector(
      "[data-anonymize='industry'], .industry, .top-card-layout__entity-info-container .industry"
    );
    if (industryEl) {
      detail.domaine_entreprise = industryEl.textContent.trim();
    }
  } catch (_) {}

  return detail;
}
