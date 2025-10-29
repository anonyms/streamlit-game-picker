import requests
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_page_source_with_selenium(url):
    """
    Uses Selenium to load a dynamic (JavaScript-heavy) page and returns its HTML source.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run browser in the background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # You will need to have chromedriver installed and accessible in your PATH.
    # Or, you can specify the path to chromedriver executable:
    # service = Service(executable_path='/path/to/chromedriver')
    # driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # This simpler setup works if chromedriver is in your system's PATH
    try:
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        print(f"Error initializing Selenium WebDriver: {e}")
        print("Please ensure 'chromedriver' is installed and in your system's PATH.")
        return None

    page_source = None
    try:
        driver.get(url)
        
        # --- THIS IS THE CRITICAL PART ---
        # This selector is updated to match the real page.
        # It waits for the main table "container" to load.
        wait_selector = 'div[class*="StandingsTable-module__container"]'
        
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector))
        )
        
        # Give it an extra second just in case
        time.sleep(1) 
        
        page_source = driver.page_source
        
    except Exception as e:
        print(f"Error loading page with Selenium: {e}")
    finally:
        driver.quit()
        
    return page_source