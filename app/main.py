import streamlit as st
import pandas as pd
from src.scraper import scrape_league_data

st.set_page_config(page_title="SofaScore League Scraper", layout="wide")

st.title("🏆 Final League Results")
st.markdown("""
This page scrapes data for all the leagues listed in `websites.txt`.
Click the button below to start scraping. The results will be displayed for each league.
""")

def get_websites():
    """Reads URLs from the websites.txt file."""
    try:
        with open("websites.txt", "r") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        st.error("`websites.txt` not found. Please create it in the root directory.")
        return []

# --- Main Page Logic ---
websites = get_websites()

if not websites:
    st.warning("Please add at least one URL to `websites.txt` to begin.")
else:
    st.info(f"Found {len(websites)} URLs to scrape.")

if st.button("🚀 Scrape All Leagues", type="primary"):
    if not websites:
        st.error("Cannot scrape because no URLs are provided in `websites.txt`.")
    else:
        # Using an expander for each result to keep the UI clean
        for url in websites:
            with st.expander(f"Scraping Results for {url}", expanded=True):
                with st.spinner(f"Fetching data from {url}..."):
                    try:
                        scraped_data = scrape_league_data(url)
                        if scraped_data:
                            st.success(f"Successfully scraped data for **{scraped_data['league_name']}**")

                            # Display the scraped data
                            st.metric("League Name", scraped_data['league_name'])

                            st.subheader("📋 Team Standings")
                            # Create a DataFrame for better display
                            df = pd.DataFrame(scraped_data['teams'])
                            st.dataframe(df, use_container_width=True, hide_index=True)

                        else:
                            st.warning("Could not retrieve any data. The website structure might have changed.")
                    except Exception as e:
                        st.error(f"An error occurred while scraping {url}: {e}")
