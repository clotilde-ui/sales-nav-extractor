// Content script — injecté sur les pages Sales Navigator

const MIN_DELAY = 2000;
const MAX_DELAY = 5000;

function randomDelay() {
  const ms = Math.random() * (MAX_DELAY - MIN_DELAY) + MIN_DELAY;
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function scrollToLoadCards() {
  // Scroll progressif vers le bas pour déclencher le lazy-loading
  // Répète jusqu'à ce que le nombre de cartes se stabilise
  let previousCount = 0;
  let stableRounds = 0;

  while (stableRounds < 3) {
    const cards = document.querySelectorAll(
      "li.artdeco-list__item, ol.search-results__result-list > li"
    );
    const currentCount = cards.length;

    if (currentCount === previousCount) {
      stableRounds++;
    } else {
      stableRounds = 0;
      previousCount = currentCount;
    }

    // Scroll chaque carte visible dans le viewport
    for (const card of cards) {
      card.scrollIntoView({ behavior: "smooth", block: "center" });
      await sleep(150 + Math.random() * 150);
    }

    // Scroll aussi vers le bas de la page pour forcer le chargement
    window.scrollTo(0, document.body.scrollHeight);
    await sleep(800);
  }

  window.scrollTo(0, 0);
  await sleep(500);
}

function getLeadCards() {
  return document.querySelectorAll(
    "li.artdeco-list__item, ol.search-results__result-list > li"
  );
}

function scrapeCurrentPage() {
  const cards = getLeadCards();
  const leads = [];
  for (const card of cards) {
    const lead = parseLeadCard(card);
    if (lead.prenom || lead.titre) {
      leads.push(lead);
    }
  }
  return leads;
}

function clickNextPage() {
  const nextBtn = document.querySelector(
    "button.artdeco-pagination__button--next, " +
      "button[aria-label='Next'], " +
      "button[aria-label='Suivant']"
  );
  if (nextBtn && !nextBtn.disabled) {
    nextBtn.click();
    return true;
  }
  return false;
}

function waitForCards(timeout = 30000) {
  return new Promise((resolve, reject) => {
    const start = Date.now();
    const check = () => {
      const cards = getLeadCards();
      if (cards.length > 0) {
        resolve(cards.length);
      } else if (Date.now() - start > timeout) {
        reject(new Error("Timeout: aucune carte trouvée"));
      } else {
        setTimeout(check, 500);
      }
    };
    check();
  });
}

function waitForNewPage(previousCount, timeout = 30000) {
  // Attend que le DOM change après un clic sur "Suivant"
  // Détecte soit un nombre de cartes différent, soit un changement d'URL
  const startUrl = window.location.href;
  return new Promise((resolve, reject) => {
    const start = Date.now();
    const check = () => {
      const urlChanged = window.location.href !== startUrl;
      const cards = getLeadCards();
      if (urlChanged || cards.length !== previousCount) {
        // Petite pause pour laisser le rendu se stabiliser
        setTimeout(() => resolve(cards.length), 1000);
      } else if (Date.now() - start > timeout) {
        reject(new Error("Timeout: la page n'a pas changé"));
      } else {
        setTimeout(check, 500);
      }
    };
    check();
  });
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.action === "scrape_current_page") {
    (async () => {
      try {
        await scrollToLoadCards();
        const leads = scrapeCurrentPage();
        sendResponse({ success: true, leads });
      } catch (err) {
        sendResponse({ success: false, error: err.message });
      }
    })();
    return true; // keep channel open for async response
  }

  if (message.action === "scrape_all_pages") {
    const maxPages = message.maxPages || Infinity;
    (async () => {
      const allLeads = [];
      let pageNum = 1;

      try {
        while (pageNum <= maxPages) {
          await waitForCards();
          await scrollToLoadCards();
          const leads = scrapeCurrentPage();
          allLeads.push(...leads);

          // Send progress update
          chrome.runtime.sendMessage({
            type: "progress",
            page: pageNum,
            maxPages: maxPages === Infinity ? null : maxPages,
            totalLeads: allLeads.length,
            pageLeads: leads.length,
          });

          if (pageNum >= maxPages) break;

          const countBefore = getLeadCards().length;
          const hasNext = clickNextPage();
          if (!hasNext) break;

          await randomDelay();
          pageNum++;

          // Attendre que la page change (nouvelles cartes chargées)
          try {
            await waitForNewPage(countBefore);
          } catch (_) {
            break;
          }
        }

        sendResponse({ success: true, leads: allLeads, pages: pageNum });
      } catch (err) {
        sendResponse({
          success: false,
          error: err.message,
          leads: allLeads,
          pages: pageNum,
        });
      }
    })();
    return true;
  }

  if (message.action === "check_page") {
    const isSalesNav = window.location.href.includes("/sales/");
    const isSearch = window.location.href.includes("/sales/search/");
    sendResponse({ isSalesNav, isSearch });
    return true;
  }
});
