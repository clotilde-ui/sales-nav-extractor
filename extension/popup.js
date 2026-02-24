const CSV_FIELDS = [
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
];

let exportedLeads = [];

function $(id) {
  return document.getElementById(id);
}

function show(id) {
  $(id).classList.remove("hidden");
}

function hide(id) {
  $(id).classList.add("hidden");
}

function escapeCsvField(value) {
  if (value == null) return "";
  const str = String(value);
  if (str.includes('"') || str.includes(",") || str.includes("\n")) {
    return '"' + str.replace(/"/g, '""') + '"';
  }
  return str;
}

function leadsToCSV(leads) {
  const header = CSV_FIELDS.join(",");
  const rows = leads.map((lead) =>
    CSV_FIELDS.map((f) => escapeCsvField(lead[f])).join(",")
  );
  return header + "\n" + rows.join("\n");
}

function downloadCSV(csv, filename) {
  const blob = new Blob(["\uFEFF" + csv], {
    type: "text/csv;charset=utf-8;",
  });
  const url = URL.createObjectURL(blob);
  chrome.downloads.download({
    url,
    filename,
    saveAs: true,
  });
}

async function getCurrentTab() {
  const [tab] = await chrome.tabs.query({
    active: true,
    currentWindow: true,
  });
  return tab;
}

async function checkPage(tab) {
  try {
    const [result] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => ({
        isSalesNav: window.location.href.includes("/sales/"),
        isSearch: window.location.href.includes("/sales/search/"),
      }),
    });
    return result.result;
  } catch {
    return { isSalesNav: false, isSearch: false };
  }
}

// Listen for progress messages from content script
chrome.runtime.onMessage.addListener((message) => {
  if (message.type === "progress") {
    const progressText = $("progress-text");
    const progressFill = $("progress-fill");
    const maxLabel = message.maxPages ? `/${message.maxPages}` : "";
    progressText.textContent = `Page ${message.page}${maxLabel} — ${message.totalLeads} leads`;

    if (message.maxPages) {
      const pct = (message.page / message.maxPages) * 100;
      progressFill.style.width = pct + "%";
    } else {
      progressFill.style.width = "100%";
      progressFill.classList.add("indeterminate");
    }
  }
});

document.addEventListener("DOMContentLoaded", async () => {
  const tab = await getCurrentTab();
  const { isSearch } = await checkPage(tab);

  if (!isSearch) {
    show("not-sales-nav");
    hide("controls");
    return;
  }

  $("btn-export").addEventListener("click", async () => {
    const maxPagesInput = $("max-pages").value;
    const maxPages = maxPagesInput ? parseInt(maxPagesInput, 10) : null;

    hide("controls");
    hide("results");
    show("progress");
    $("progress-fill").style.width = "0%";
    $("progress-fill").classList.remove("indeterminate");

    try {
      const response = await chrome.tabs.sendMessage(tab.id, {
        action: maxPages ? "scrape_all_pages" : "scrape_current_page",
        maxPages,
      });

      hide("progress");

      if (response.success || (response.leads && response.leads.length > 0)) {
        exportedLeads = response.leads;
        $("results-count").textContent = `${exportedLeads.length} leads exportés`;
        show("results");
      } else {
        $("progress-text").textContent =
          "Erreur : " + (response.error || "aucun lead trouvé");
        show("progress");
      }
    } catch (err) {
      hide("progress");
      $("progress-text").textContent = "Erreur : " + err.message;
      show("progress");
    }

    show("controls");
  });

  $("btn-download").addEventListener("click", () => {
    if (!exportedLeads.length) return;
    const csv = leadsToCSV(exportedLeads);
    const date = new Date().toISOString().slice(0, 10);
    downloadCSV(csv, `leads_export_${date}.csv`);
  });
});
