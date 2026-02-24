import io
import threading

import pandas as pd
import streamlit as st

from config import CSV_FIELDS, DEFAULT_OUTPUT
from exporter import export_to_csv
from scraper import open_browser_for_login, scrape_leads

st.set_page_config(page_title="Sales Navigator Export", layout="centered")
st.title("Sales Navigator Export")

# --- Connexion LinkedIn ---
st.sidebar.header("Connexion LinkedIn")
if st.sidebar.button("Se connecter a LinkedIn"):
    with st.sidebar:
        with st.spinner("Navigateur ouvert, connectez-vous puis fermez-le..."):
            thread = threading.Thread(target=open_browser_for_login, daemon=True)
            thread.start()
            thread.join()
        st.success("Session sauvegardee.")

# --- Parametres ---
st.header("Parametres")

search_url = st.text_input("URL de recherche Sales Navigator")
output_file = st.text_input("Nom du fichier de sortie", value=DEFAULT_OUTPUT)
max_pages = st.slider("Nombre max de pages (0 = toutes)", 0, 50, 0)
detailed = st.checkbox("Mode detaille (education / experience)")

# --- Lancement ---
if st.button("Lancer l'export", type="primary"):
    if not search_url:
        st.error("Veuillez entrer une URL de recherche.")
    else:
        progress_bar = st.progress(0, text="Demarrage...")
        status_text = st.empty()

        def update_progress(current_page, total_pages):
            if total_pages:
                pct = current_page / total_pages
                progress_bar.progress(
                    min(pct, 1.0),
                    text=f"Page {current_page} / {total_pages}",
                )
            else:
                status_text.text(f"Page {current_page} scrapee...")

        pages = max_pages if max_pages > 0 else None

        with st.spinner("Scraping en cours..."):
            leads = scrape_leads(
                search_url=search_url,
                max_pages=pages,
                detailed=detailed,
                on_progress=update_progress,
            )

        progress_bar.progress(1.0, text="Termine !")

        if not leads:
            st.warning("Aucun lead trouve.")
        else:
            st.success(f"{len(leads)} leads recuperes.")

            # Export CSV sur disque
            export_to_csv(leads, output_file)

            # Affichage du tableau
            df = pd.DataFrame(leads, columns=CSV_FIELDS)
            st.dataframe(df, use_container_width=True)

            # Bouton de telechargement
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            st.download_button(
                label="Telecharger le CSV",
                data=csv_buffer.getvalue(),
                file_name=output_file,
                mime="text/csv",
            )
