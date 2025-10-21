import streamlit as st
import pandas as pd
from src.scraper import scrape_league_data

st.set_page_config(page_title="Scraper Test Page", layout="wide")

st.title("🧪 Scraper Test Page")
st.markdown("""
Use this page to test the scraping logic on a single URL. This helps in debugging
the CSS selectors in `scraper.py` without running the full process.
""")

# --- Test Page Logic ---
st.subheader("Test a Single URL")
test_url = st.text_input(
    "Enter a SofaScore League URL to test:",
    placeholder="https://www.sofascore.com/tournament/football/england/premier-league/17"
)

if st.button("🔬 Test Scraper", type="primary"):
    if not test_url:
        st.warning("Please enter a URL to test.")
    else:
        st.info(f"Attempting to scrape: {test_url}")
        with st.spinner("Scraping in progress..."):
            try:
                scraped_data = scrape_league_data(test_url)

                if scraped_data:
                    st.success("Scraping finished successfully!")
                    
                    st.metric("League Name Found", scraped_data.get('league_name', 'Not Found'))

                    st.subheader("Raw Scraped Data")
                    st.json(scraped_data)

                    st.subheader("Data as a Table")
                    if scraped_data.get('teams'):
                         df = pd.DataFrame(scraped_data['teams'])
                         st.dataframe(df, use_container_width=True, hide_index=True)
                    else:
                        st.warning("No team data was returned.")
                else:
                    st.error("Scraping failed. Check the console for errors and verify your CSS selectors in `scraper.py`.")
            except Exception as e:
                st.error(f"A critical error occurred: {e}")
