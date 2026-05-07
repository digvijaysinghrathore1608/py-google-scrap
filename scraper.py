import time
import random
import re
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from webdriver_manager.chrome import ChromeDriverManager

# ==================================================
# CONFIG
# ==================================================

INPUT_FILE = "rajasthan_chokhat_keywords.xlsx"
OUTPUT_FILE = "google_maps_data.xlsx"

MAX_RESULTS_PER_KEYWORD = 100

# Delay between keywords
MIN_DELAY = 15
MAX_DELAY = 40

# ==================================================
# CHROME OPTIONS
# ==================================================

options = Options()

options.add_argument("--start-maximized")

# Anti Detection
options.add_argument("--disable-blink-features=AutomationControlled")

options.add_experimental_option(
    "excludeSwitches",
    ["enable-automation"]
)

options.add_experimental_option(
    "useAutomationExtension",
    False
)

# Disable Images = Faster
prefs = {
    "profile.managed_default_content_settings.images": 2
}

options.add_experimental_option("prefs", prefs)

# Optional Headless
# options.add_argument("--headless=new")

# ==================================================
# DRIVER
# ==================================================

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

wait = WebDriverWait(driver, 10)

# ==================================================
# READ EXCEL
# ==================================================

df = pd.read_excel(INPUT_FILE)

keywords = df["Keyword"].dropna().tolist()

print(f"\nTotal Keywords: {len(keywords)}")

# ==================================================
# STORAGE
# ==================================================

results = []

visited_names = set()

# ==================================================
# LOOP
# ==================================================

for keyword in keywords:

    print("\n==================================================")
    print(f"Searching: {keyword}")
    print("==================================================")

    try:

        url = f"https://www.google.com/maps/search/{keyword}"

        driver.get(url)

        time.sleep(random.randint(4, 7))

        # ==================================================
        # WAIT FOR FEED
        # ==================================================

        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//div[@role="feed"]')
            )
        )

        # ==================================================
        # SCROLL
        # ==================================================

        scrollable_div = driver.find_element(
            By.XPATH,
            '//div[@role="feed"]'
        )

        for i in range(5):

            driver.execute_script(
                """
                arguments[0].scrollTop = arguments[0].scrollHeight
                """,
                scrollable_div
            )

            print(f"Scrolling: {i + 1}")

            time.sleep(random.randint(2, 4))

        # ==================================================
        # GET LISTINGS
        # ==================================================

        listings = driver.find_elements(
            By.XPATH,
            '//div[contains(@class,"Nv2PK")]'
        )

        print(f"Found Listings: {len(listings)}")

        count = 0

        for listing in listings:

            try:

                # ==================================================
                # NAME
                # ==================================================

                try:
                    name = listing.find_element(
                        By.XPATH,
                        './/div[contains(@class,"qBF1Pd")]'
                    ).text.strip()
                except:
                    name = ""

                if not name:
                    continue

                # Duplicate Skip
                if name in visited_names:
                    continue

                visited_names.add(name)

                # ==================================================
                # ADDRESS / INFO
                # ==================================================

                try:
                    address = listing.find_element(
                        By.XPATH,
                        './/div[contains(@class,"W4Efsd")]'
                    ).text.strip()
                except:
                    address = ""

                # ==================================================
                # EXTRACT PHONE
                # ==================================================

                phone = ""

                text = listing.text

                phones = re.findall(
                    r'(?:\+91[\s\-]?)?(?:0)?[6-9]\d{4}[\s\-]?\d{5}|(?:\d{3,5}[\s\-]?\d{5,8})',
                    text
                )

                cleaned_phones = []

                for p in phones:

                    p = re.sub(r'[^0-9+]', '', p)

                    digits_only = re.sub(r'\D', '', p)

                    if 10 <= len(digits_only) <= 13:
                        cleaned_phones.append(p)

                phone = ", ".join(list(set(cleaned_phones)))

                # ==================================================
                # MAP URL
                # ==================================================

                try:
                    map_url = listing.find_element(
                        By.XPATH,
                        './/a'
                    ).get_attribute("href")
                except:
                    map_url = ""

                # ==================================================
                # PRINT
                # ==================================================

                print(f"{name} | {phone}")

                # ==================================================
                # SAVE
                # ==================================================

                results.append({
                    "Keyword": keyword,
                    "Business Name": name,
                    "Phone": phone,
                    "Address": address,
                    "Google Maps URL": map_url
                })

                count += 1

                # Limit
                if count >= MAX_RESULTS_PER_KEYWORD:
                    break

            except Exception as e:

                print("Listing Error:", e)

        # ==================================================
        # LIVE SAVE
        # ==================================================

        pd.DataFrame(results).to_excel(
            OUTPUT_FILE,
            index=False
        )

        print(f"\nSaved Records: {len(results)}")

        # ==================================================
        # RANDOM GAP
        # ==================================================

        gap = random.randint(MIN_DELAY, MAX_DELAY)

        print(f"\nWaiting {gap} seconds before next keyword...\n")

        time.sleep(gap)

    except Exception as e:

        print("Keyword Error:", e)

# ==================================================
# FINAL SAVE
# ==================================================

final_df = pd.DataFrame(results)

final_df.to_excel(
    OUTPUT_FILE,
    index=False
)

print("\n==================================================")
print("SCRAPING COMPLETED")
print(f"Saved File: {OUTPUT_FILE}")
print(f"Total Records: {len(results)}")
print("==================================================")

# ==================================================
# CLOSE
# ==================================================

driver.quit()