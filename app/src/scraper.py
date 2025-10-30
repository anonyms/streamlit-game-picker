import requests
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def get_page_source_with_selenium(url):
    """
    Uses Selenium to load a dynamic (JavaScript-heavy) page and returns its HTML source
    or an error message.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = None
    try:
        print("Initializing Selenium WebDriver...")
        driver = webdriver.Chrome(options=chrome_options)
        print("WebDriver initialized.")
    except Exception as e:
        error_msg = f"Error initializing Selenium WebDriver: {e}. Ensure chromedriver is in PATH."
        print(error_msg)
        return None, error_msg

    page_source = None
    try:
        print(f"Getting URL: {url}")
        driver.get(url)
        
        wait_selector = 'div[class*="StandingsTable-module__container"]'
        print(f"Waiting for selector: {wait_selector}")
        
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector))
        )
        print("Selector found. Page is loaded.")
        
        time.sleep(1) 
        page_source = driver.page_source
        
    except TimeoutException:
        error_msg = "Timeout: The page took too long to load or the wait selector 'div[class*=\"StandingsTable-module__container\"]' was not found. The SofaScore layout may have changed."
        print(error_msg)
        return None, error_msg
    except Exception as e:
        error_msg = f"Error loading page with Selenium: {e}"
        print(error_msg)
        return None, error_msg
    finally:
        if driver:
            driver.quit()
        
    return page_source, None


def scrape_league_data(url):
    """
    Scrapes a single SofaScore league page.
    Returns a dictionary with data or an error.
    """
    
    # 1. Get the page source using Selenium
    html_content, error = get_page_source_with_selenium(url)
    
    if error:
        return {"error": error}

    if not html_content:
        return {"error": "Failed to retrieve page source (html_content is empty)."}

    # 2. Parse the rendered HTML with BeautifulSoup
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # --- REAL SELECTORS BASED ON PARTIAL MATCHING ---

        # 1. Scrape League Name (Updated selector)
        league_name_element = soup.select_one('h2[class*="TournamentHeader-module__title"]')
        league_name = league_name_element.text.strip() if league_name_element else "League Name Not Found"

        # 2. Scrape Team Data
        teams_data = []
        
        # Find the main table container
        table = soup.select_one('div[class*="StandingsTable-module__container"]')
        
        if not table:
            return {
                "error": "Could not find standings table. Selectors may be outdated.",
                "league_name": league_name,
                "teams": []
            }

        # Find all team rows using a partial class match
        team_rows = table.select('a[class*="Standings-module__rowWrapper"]')

        if not team_rows:
            return {
                "error": "Found table but no team rows. Selectors are outdated.",
                "league_name": league_name,
                "teams": []
            }

        for row in team_rows:
            # Get Position
            position_el = row.select_one('div[class*="Standings-module__position"]')
            position = position_el.text.strip() if position_el else 'N/A'

            # Get Team Name
            team_name_el = row.select_one('div[class*="Standings-module__teamName"]')
            team_name = team_name_el.text.strip() if team_name_el else 'N/A'
            
            # --- Get Form Data ---
            form_nodes = row.select('div[class*="Form-module__form"] > div[class*="Form-module__event"]')
            form = []
            for node in form_nodes:
                node_class = str(node)
                if 'Form-module__win' in node_class:
                    form.append('W')
                elif 'Form-module__loss' in node_class:
                    form.append('L')
                elif 'Form-module__draw' in node_class:
                    form.append('D')
                else:
                    form.append('?')

            # --- Find Wins ---
            stats = row.select('div[class*="Standings-module__cell--value"]')
            
            # 0=Played, 1=W, 2=D, 3=L, 4=Goals, 5=Points
            # **ADJUST THIS INDEX AS NEEDED**
            wins = stats[1].text.strip() if len(stats) > 1 else 'N/A'
            
            # Next Game (This is not in the main table and must be scraped separately)
            next_game = 'N/A' 
            
            teams_data.append({
                "Position": position,
                "Team": team_name,
                "Wins": wins,
                "Form": ' '.join(form),
                "Next Game": next_game
            })
            
        if not teams_data:
             return {
                "error": "No team data could be scraped. Selectors may be outdated.",
                "league_name": league_name,
                "teams": []
            }

        return {
            "league_name": league_name,
            "teams": teams_data,
            "error": None # Explicitly state no error
        }

    except Exception as e:
        print(f"An error occurred during scraping: {e}")
        return {"error": f"A critical error occurred during parsing: {e}"}

