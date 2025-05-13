# scraper.py
"""
Booking.com scraper via Selenium with robust waits and retries.

Flow:
1) Launch headless Chrome with a real User-Agent & large viewport.
2) GET your share-URL (follows redirect to /searchresults…).
3) Explicitly wait for the first property-card and its sub-elements.
4) Extract name, address, distance, review score/count, unit details, price, etc.
5) Quit the driver in all cases to free resources.
"""

import re
from datetime import datetime, timezone
from typing import Dict

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def fetch_listing(url: str) -> Dict:
    chrome_opts = Options()
    chrome_opts.add_argument("--headless")
    chrome_opts.add_argument("--disable-gpu")
    chrome_opts.add_argument("--no-sandbox")
    chrome_opts.add_argument("--disable-extensions")
    chrome_opts.add_argument("--disable-dev-shm-usage")
    # mimic a real browser
    chrome_opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=chrome_opts)
    driver.set_window_size(1920, 1080)

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 20)

        # 1) wait for the main property card container
        card = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='property-card']"))
        )

        def _text(sel: str) -> str:
            return card.find_element(By.CSS_SELECTOR, sel).text.strip()

        # 2) name + direct link
        title_el = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div[data-testid='property-card'] [data-testid='title-link']")
        ))
        name = title_el.find_element(By.CSS_SELECTOR, "[data-testid='title']").text.strip()
        link = title_el.get_attribute("href").split("?", 1)[0]

        # 3) address & distance
        address = _text("[data-testid='address']")
        distance = _text("[data-testid='distance']")

        # 4) review score & count
        score_block = card.find_element(By.CSS_SELECTOR, "[data-testid='review-score-link']")
        review_score = float(
            score_block.find_element(By.CSS_SELECTOR, "div[aria-hidden='true']").text.replace(",", ".")
        )
        extra = score_block.find_element(By.CSS_SELECTOR, ".aa225776f2").text
        # extract the first integer (e.g. "Very good 29 reviews" → 29)
        m = re.search(r"(\d+)", extra)
        reviews_count = int(m.group(1)) if m else 0

        # 5) unit type / bed info / cancellation
        unit = _text("[data-testid='recommended-units'] h4")
        bed_info = card.find_element(By.CSS_SELECTOR, "ul li .fff1944c52").text.strip()
        cancellation = ""
        try:
            card.find_element(By.CSS_SELECTOR, "[data-testid='cancellation-policy-icon']")
            cancellation = "Free cancellation"
        except:
            pass

        # 6) nights/adults & price
        nights_adults = _text("[data-testid='price-for-x-nights']")
        raw_price = _text("[data-testid='price-and-discounted-price']")
        price = "".join(ch for ch in raw_price if ch.isdigit() or ch in ",.")

        # 7) timestamp + final URL
        now = datetime.now(timezone.utc).isoformat()
        final_url = driver.current_url

        return {
            "hotel_id": None,
            "name": name,
            "link": link,
            "address": address,
            "distance": distance,
            "review_score": review_score,
            "reviews_count": reviews_count,
            "unit": unit,
            "bed_info": bed_info,
            "cancellation": cancellation,
            "nights_adults": nights_adults,
            "price": price,
            "scraped_at": now,
            "source_url": final_url,
        }

    except (TimeoutException, WebDriverException) as e:
        raise RuntimeError(f"Selenium failed to load or parse Booking.com page: {e}")

    finally:
        driver.quit()
