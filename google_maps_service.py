import os
import urllib.parse
from typing import Dict, Optional, Union

from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

load_dotenv()
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
CHROME_BINARY = os.getenv("CHROME_BINARY", "/usr/bin/chromium")


def fetch_google_maps_review(
        name: str,
        city: str,
        timeout: int = 20,
        headless: bool = True,
) -> Dict[str, Optional[Union[float, int, str]]]:
    """
    Search Google Maps for "<name> <city>", wait for the review widget, then scrape.
    Handles Google consent page if encountered.
    """
    query = f"{name} {city}"
    search_url = "https://www.google.com/maps/search/" + urllib.parse.quote_plus(query)

    print(f"Searching for: {query}")

    # set up Chrome
    chrome_opts = Options()
    if headless:
        chrome_opts.add_argument("--headless=new")
    chrome_opts.add_argument("--disable-gpu")
    chrome_opts.add_argument("--no-sandbox")
    chrome_opts.add_argument("--disable-dev-shm-usage")
    chrome_opts.add_argument("--window-size=1920,1080")
    chrome_opts.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
    chrome_opts.binary_location = CHROME_BINARY
    service = Service(executable_path=CHROMEDRIVER_PATH)

    driver = webdriver.Chrome(service=service, options=chrome_opts)
    import time

    try:
        driver.get(search_url)
        wait = WebDriverWait(driver, timeout)

        # Check if redirected to consent page
        if "consent.google.com" in driver.current_url:
            print("Detected consent page, accepting cookies...")

            try:
                # Try different selectors for the "Accept all" button
                consent_selectors = [
                    "button[aria-label='Accept all']",
                    "button.UywwFc-LgbsSe[jsname='b3VHJd']",
                    "button.XWZjwc",
                    "//button[contains(text(), 'Accept all')]"
                ]

                for selector in consent_selectors:
                    try:
                        if selector.startswith("//"):
                            accept_button = wait.until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                        else:
                            accept_button = wait.until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                        print(f"Found consent button with selector: {selector}")
                        accept_button.click()
                        print("Clicked consent button")

                        # Wait for navigation to complete
                        wait.until(lambda d: "consent.google.com" not in d.current_url)
                        time.sleep(3)  # Additional wait for page to stabilize
                        break
                    except Exception as e:
                        print(f"Consent selector {selector} failed: {str(e)}")
                        continue
            except Exception as e:
                print(f"Failed to handle consent page: {str(e)}")

        print(f"Current URL: {driver.current_url}")

        # Wait for page to fully load
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        time.sleep(3)  # Let the page stabilize

        # Try multiple selectors for the review container
        selectors = [
            "div.F7nice",
            "div[jslog*='76333']",
            "div.F7nice[jslog*='76333']",
            "span[role='img'][aria-label*='stars']"
        ]

        container = None
        for selector in selectors:
            try:
                print(f"Trying selector: {selector}")
                container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                if container:
                    print(f"Found container with selector: {selector}")
                    break
            except Exception as e:
                print(f"Selector {selector} failed: {str(e)}")
                continue

        if not container:
            print("No review container found, returning default values")
            return {
                "google_review_score": None,
                "google_reviews_count": None,
                "google_maps_url": search_url,  # Just return the search URL
            }

        # Extract review score and count using multiple methods
        review_score = None
        reviews_count = None

        try:
            # First try getting the score from aria-hidden span
            score_el = driver.find_element(By.CSS_SELECTOR, "span span[aria-hidden='true']")
            review_score = float(score_el.text.replace(",", "."))
        except Exception:
            # Try getting score from aria-label on the role="img" element
            try:
                img_el = driver.find_element(By.CSS_SELECTOR, "span[role='img'][aria-label*='stars']")
                label = img_el.get_attribute("aria-label")
                if label and "stars" in label:
                    review_score = float(label.split()[0].replace(",", "."))
            except Exception:
                pass

        try:
            # Try to get count from aria-label containing reviews
            count_elements = driver.find_elements(By.CSS_SELECTOR, "span[aria-label*='review']")
            for el in count_elements:
                label = el.get_attribute("aria-label")
                if label and "review" in label:
                    import re
                    match = re.search(r'(\d[\d,\.]+)', label)
                    if match:
                        raw_count = match.group(1)
                        reviews_count = int(raw_count.replace(",", "").replace(".", ""))
                        break
        except Exception:
            # Try getting count from parentheses text
            try:
                parenthesis_texts = driver.find_elements(By.XPATH, "//span[contains(text(), '(')]")
                for el in parenthesis_texts:
                    text = el.text
                    import re
                    match = re.search(r'\(([0-9,\.]+)\)', text)
                    if match:
                        raw_count = match.group(1)
                        reviews_count = int(raw_count.replace(",", "").replace(".", ""))
                        break
            except Exception:
                pass

        # Get the URL
        google_maps_url = driver.current_url

        return {
            "google_review_score": review_score,
            "google_reviews_count": reviews_count,
            "google_maps_url": google_maps_url,
        }

    except Exception as e:
        print(f"Error scraping Google Maps: {e}")
        # Take screenshot for debugging
        try:
            screenshot_path = f"error_screenshot_{name.replace(' ', '_')}_{int(time.time())}.png"
            driver.save_screenshot(screenshot_path)
            print(f"Error screenshot saved to {screenshot_path}")
        except:
            pass

        return {
            "google_review_score": None,
            "google_reviews_count": None,
            "google_maps_url": search_url,
        }
    finally:
        driver.quit()
