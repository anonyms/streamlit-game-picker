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
import base64 # Import for screenshot

def get_page_source_with_selenium(url):
    """
    Uses Selenium to load a dynamic (JavaScript-heavy) page and returns its HTML source
    or an error message.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # --- NEW: FAKE DESKTOP RESOLUTION AND USER AGENT ---
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    # --- END OF NEW OPTIONS ---

    # --- NEW: SET BROWSER LANGUAGE / LOCALE ---
    # This tells the browser to request US English, which should prevent
    # the "confirm language" pop-up.
    chrome_options.add_argument("--lang=en-US")
    chrome_options.add_argument("accept-language=en-US,en;q=0.9")
    # --- END OF NEW LANGUAGE OPTIONS ---
    
    driver = None
    try:
        print("Initializing Selenium WebDriver...")
        driver = webdriver.Chrome(options=chrome_options)
        print("WebDriver initialized.")
    except Exception as e:
        error_msg = f"Error initializing Selenium WebDriver: {e}. Ensure chromedriver is in PATH."
        print(error_msg)
        return None, {"error_message": error_msg} # Return as dict

    page_source = None
    try:
        print(f"Getting URL: {url}")
        driver.get(url)
        
        # --- NEW: ATTEMPT TO CLICK COOKIE CONSENT BUTTON ---
        try:
            # Wait a max of 7 seconds for a common cookie button to appear
            # This selector targets a button with a class like 'fc-cta-consent'
            cookie_selector_css = "button.fc-cta-consent" 
            print(f"Waiting for cookie button: {cookie_selector_css}")
            
            cookie_button = WebDriverWait(driver, 7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, cookie_selector_css))
            )
            
            # Use JavaScript click, which is often more reliable
            driver.execute_script("arguments[0].click();", cookie_button)
            print("Cookie consent button found and clicked via JavaScript.")
            
            # Give the page a moment to react after closing the modal
            time.sleep(1.5)
            
        except TimeoutException:
            print("Cookie consent button not found or not needed.")
            pass # It's fine, just continue
        except Exception as e:
            print(f"An error occurred while trying to click the cookie button: {e}")
            pass # Continue anyway
        # --- END OF COOKIE LOGIC ---
            
        except TimeoutException:
            print("Modal close button not found or not needed.")
            pass # It's fine, just continue
        except Exception as e:
            print(f"An error occurred while trying to click the modal close button: {e}")
            pass # Continue anyway
        # --- END OF MODAL CLOSE LOGIC ---

        wait_selector = 'div[class*="StandingsTable-module__container"]'
        print(f"Waiting for selector: {wait_selector}")
        
        # --- CHANGE: Increased wait time ---
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector))
        )
        print("Selector found. Page is loaded.")
        
        # --- CHANGE: Increased sleep time just in case ---
        time.sleep(2) 
        page_source = driver.page_source
        
    except TimeoutException:
        # --- NEW DEBUGGING FEATURES ---
        print("TimeoutException: Taking screenshot and saving page source.")
        
        # 1. Get screenshot as base64
        try:
            screenshot_base64 = driver.get_screenshot_as_base64()
        except Exception as e:
            screenshot_base64 = f"Screenshot failed: {e}"
            
        # 2. Get current page source
        try:
            debug_page_source = driver.page_source
        except Exception as e:
            debug_page_source = f"Page source capture failed: {e}"

        error_msg = ("Timeout 4: The page took too long (30s) or the selector 'div[class*=\"StandSofaScore.comStandingsTable-module__container\"]' was not found. "
                     "This likely means the SofaScore layout changed OR the cookie consent logic failed. "
                     "A debug screenshot and the page source (HTML) are included in the error.")
        
        print(error_msg)
        
        # Return a dictionary with debug info
        debug_info = {
            "error_message": error_msg,
            "debug_screenshot_base64": screenshot_base64,
            "debug_page_source": debug_page_source
        }
        return None, debug_info # Return the debug info dictionary as the "error"
    
    except Exception as e:
        error_msg = f"Error loading page with Selenium: {e}"
        print(error_msg)
        return None, {"error_message": error_msg} # Return as dict for consistency
    finally:
        if driver:
            driver.quit()
        
    # --- CHANGE: Return as dict for consistency ---
    return page_source, {"error_message": None}


def scrape_league_data(url):
    """
    Scrapes a single SofaScore league page.
    Returns a dictionary with data or an error.
    """
    
    # 1. Get the page source using Selenium
    html_content, error_info = get_page_source_with_selenium(url)
    
    # --- CHANGE: Handle new error dictionary ---
    if error_info and error_info.get("error_message"):
        # Pass the whole debug dictionary forward as the error
        return {"error": error_info.get("error_message"), "debug_info": error_info}

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

