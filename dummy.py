# # eCourts Cause-list Scraper (Selenium, Headless)

# **Goal:** Fetch court listings from [https://services.ecourts.gov.in/ecourtindia_v6/](https://services.ecourts.gov.in/ecourtindia_v6/)

# **Approach:** Selenium (headless Chrome) automation. Saves results as JSON and optionally downloads PDFs and full cause lists.

# ---

# ## Project structure

# ```
# ecourts-scraper/
# ├─ README.md            # this documentation (also included below)
# ├─ requirements.txt
# ├─ scraper.py           # main executable script
# └─ examples/
#    └─ outputs/          # where JSON and PDFs will be saved
# ```

# ---

# ## Requirements (requirements.txt)

# ```
# selenium>=4.8.0
# webdriver-manager>=4.0.0
# requests>=2.28.0
# beautifulsoup4>=4.12.0
# tqdm>=4.65.0
# python-dateutil>=2.8.2
# ```

# ---

# ## README (usage / install)

# 1. Create virtualenv and install requirements:

# ```bash
# python -m venv venv
# source venv/bin/activate     # linux/mac
# venv\Scripts\activate      # windows
# pip install -r requirements.txt
# ```

# 2. Run the script (examples):

# * Search by CNR for today (and optionally download PDF if found):

# ```bash
# python scraper.py --cnr "CNR1234567890123" --today --download-pdf
# ```

# * Search by case type/number/year for tomorrow:

# ```bash
# python scraper.py --case-type "CR" --number 1234 --year 2024 --tomorrow
# ```

# * Download the full cause list for today (HTML/PDF if available):

# ```bash
# python scraper.py --causelist --today --download-causelist
# ```

# * Save output directory (defaults to `examples/outputs`):

# ```bash
# python scraper.py --cnr "..." --today --output-dir ./my_outputs
# ```

# 3. Output

# * JSON file(s) with case search results (serial number & court name when listed for today/tomorrow)
# * Downloaded PDFs (case PDF or cause list PDF) saved to output dir

# ---

# ## Implementation notes

# * This script uses `webdriver-manager` so you don't need to manually manage chromedriver binary. It uses Chrome in headless mode by default.
# * eCourts website uses dynamic content and sometimes session-based token / JS-built elements. The selectors (`xpath` / `css`) in the code are **best-effort**. If a selector fails, update the XPath/CSS in the noted areas.
# * The script includes robust waits (explicit `WebDriverWait`) and error handling for common cases (no listing, unexpected page layout, missing PDF link).

# ---

# ## scraper.py (full script)

# ```python
#!/usr/bin/env python3
"""
ecourts scraper using Selenium (headless)

Notes:
- This script is a best-effort scraper. The exact XPaths/CSS selectors may need updates if the eCourts site changes.
- Tested conceptually; you may need to adapt selectors when running for the first time.
"""

import argparse
import json
import os
import time
from datetime import datetime, timedelta
from dateutil import parser as dateparser
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from tqdm import tqdm

BASE_URL = "https://services.ecourts.gov.in/ecourtindia_v6/"


def init_driver(headless=True, window_size=(1200, 900)):
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"--window-size={window_size[0]},{window_size[1]}")
    # optional: set user-agent if blocking
    options.add_argument("--disable-blink-features=AutomationControlled")

    try:
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    except WebDriverException as e:
        raise RuntimeError("Could not start Chrome webdriver. Ensure Chrome is installed and driver is compatible") from e

    driver.implicitly_wait(5)
    return driver


def safe_get(driver, url, timeout=15):
    try:
        driver.get(url)
    except Exception as e:
        raise RuntimeError(f"Failed to GET {url}: {e}")

    # return page source after waiting for basic load
    time.sleep(1)
    return driver.page_source


def parse_cause_list_page(html):
    """Parse an eCourts cause list HTML and return structured rows.

    NOTE: The HTML structure varies; this function should be adapted to the real page structure.
    This function returns a list of dicts with keys: date, court_name, serial, case_no, party_names, pdf_link (if any)
    """
    soup = BeautifulSoup(html, "html.parser")
    results = []

    # Heuristic: find table rows in cause-list. Update selectors if needed.
    # Try a few common patterns.
    tables = soup.find_all("table")
    for table in tables:
        # skip tiny tables
        if len(table.find_all("tr")) < 2:
            continue
        # iterate rows
        for tr in table.find_all("tr"):
            tds = tr.find_all(["td", "th"])
            if not tds:
                continue
            text = " | ".join([td.get_text(strip=True) for td in tds])
            # simple heuristic: look for a probable serial number and court name
            results.append({
                "raw": text,
                "columns": [td.get_text(strip=True) for td in tds],
            })
    return results


def download_file(url, out_dir, session=None, filename=None):
    session = session or requests.Session()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if filename is None:
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path) or f"download_{int(time.time())}.pdf"
    outfile = out_dir / filename

    try:
        resp = session.get(url, stream=True, timeout=30)
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        with open(outfile, "wb") as f:
            if total == 0:
                f.write(resp.content)
            else:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        return str(outfile)
    except Exception as e:
        print(f"Download failed for {url}: {e}")
        return None


def search_by_cnr(driver, cnr):
    """Open site, search by CNR. Return page source of result or raise.

    The selectors here are placeholders and may need to be adjusted.
    """
    driver.get(BASE_URL)

    wait = WebDriverWait(driver, 15)

    try:
        # Example: find element that navigates to "Case Status" or CNR search
        # Real page may have id/class; update these XPaths to match actual site.
        # We'll try to locate an input with placeholder or label 'CNR'
        # Common approach: locate input by name 'cnr' or id containing 'cnr'
        possible_inputs = driver.find_elements(By.XPATH, "//input[contains(translate(@placeholder,'CNR','cnr'),'cnr') or contains(translate(@id,'cnr','cnr'),'cnr')]")
        if possible_inputs:
            cnr_input = possible_inputs[0]
        else:
            # fallback: find input fields and pick the one with maxlength 16 (cnr length)
            inputs = driver.find_elements(By.XPATH, "//input[@type='text']")
            cnr_input = None
            for inp in inputs:
                try:
                    maxlength = inp.get_attribute('maxlength')
                    if maxlength and int(maxlength) >= 16:
                        cnr_input = inp
                        break
                except:
                    continue
            if cnr_input is None:
                raise RuntimeError("CNR input field not found - you may need to update the XPath selectors")

        cnr_input.clear()
        cnr_input.send_keys(cnr)

        # Attempt to submit - look for a nearby button
        # Try button with text 'Search' or an input[type=submit]
        try:
            search_btn = driver.find_element(By.XPATH, "//button[contains(translate(text(),'SEARCH','search'),'search') or @type='submit']")
            search_btn.click()
        except NoSuchElementException:
            # try pressing Enter on input
            cnr_input.send_keys('\n')

        # Wait for results container - generic wait
        time.sleep(2)
        return driver.page_source
    except Exception as e:
        raise RuntimeError(f"CNR search failed: {e}")


def search_by_case_number(driver, case_type, number, year):
    driver.get(BASE_URL)
    time.sleep(1)
    # Implementation depends on site: find fields for case-type, number, year
    try:
        # placeholders: adapt these selectors based on site structure
        type_inp = driver.find_element(By.XPATH, "//input[contains(@placeholder,'Case Type') or contains(@id,'caseType')]")
        num_inp = driver.find_element(By.XPATH, "//input[contains(@placeholder,'Case No') or contains(@id,'caseNo')]")
        year_inp = driver.find_element(By.XPATH, "//input[contains(@placeholder,'Year') or contains(@id,'caseYear')]")

        type_inp.clear(); type_inp.send_keys(case_type)
        num_inp.clear(); num_inp.send_keys(str(number))
        year_inp.clear(); year_inp.send_keys(str(year))

        # submit
        try:
            search_btn = driver.find_element(By.XPATH, "//button[contains(translate(text(),'SEARCH','search'),'search') or @type='submit']")
            search_btn.click()
        except NoSuchElementException:
            num_inp.send_keys('\n')

        time.sleep(2)
        return driver.page_source
    except Exception as e:
        raise RuntimeError(f"Case number search failed: {e}")


def extract_listings_from_result_page(html, target_dates):
    """Given HTML of a case's status/listing page, parse and check if it's listed in target_dates.

    Returns: dict with keys: listed (bool), entries: [{date, serial, court_name, pdf_link?}]
    """
    soup = BeautifulSoup(html, "html.parser")
    entries = []

    # Heuristic parsing - find cause-list sections or tables mentioning dates
    # Try to find all occurrences of dates and surrounding text
    text = soup.get_text(separator='\n')

    # Look for a cause list table first
    results = parse_cause_list_page(html)

    # Try to map parsed table rows to actual dates and courts
    for r in results:
        row_text = r['raw']
        # extract any date-like substring
        try:
            dt = None
            # attempt to find date token in columns
            for col in r['columns']:
                try:
                    parsed_dt = dateparser.parse(col, fuzzy=True, default=None)
                    if parsed_dt:
                        dt = parsed_dt.date()
                        break
                except Exception:
                    continue

            # fallback: if no date parsed, skip date match
            entry = {
                'raw': row_text,
                'date': dt.isoformat() if dt else None,
                'serial': None,
                'court_name': None,
                'pdf_link': None,
            }

            # attempt to find serial and court name heuristically
            cols = r['columns']
            if len(cols) >= 2:
                # common pattern: [serial, case no, party, court]
                # We'll search for a short integer as serial
                for col in cols:
                    if col.isdigit() and len(col) < 6:
                        entry['serial'] = col
                        break
                # court name guess
                entry['court_name'] = cols[-1]

            # if entry date matches any target date, include
            if dt and dt in target_dates:
                entries.append(entry)
            else:
                # also include fuzzy matches: if no dt parsed but text contains today's/tomorrow's date string
                for td in target_dates:
                    if td.isoformat() in row_text:
                        entry['date'] = td.isoformat()
                        entries.append(entry)
                        break
        except Exception:
            continue

    listed = len(entries) > 0
    return {
        'listed': listed,
        'entries': entries,
    }


def download_cause_list_for_today(driver, out_dir):
    """Attempt to navigate to the master cause list page (today) and download PDF/HTML.

    NOTE: The exact navigation depends on the site. We'll attempt to find links mentioning 'Cause List' or 'Today'.
    """
    driver.get(BASE_URL)
    time.sleep(1)
    page = driver.page_source
    soup = BeautifulSoup(page, 'html.parser')

    # try to find link to today's cause list - heuristics
    links = soup.find_all('a', href=True)
    target = None
    for a in links:
        txt = a.get_text(strip=True).lower()
        if 'cause list' in txt or 'cause-list' in txt or 'cause list for today' in txt or 'today' in txt:
            target = a['href']
            break
    if not target:
        # fallback: attempt to search a known URL pattern (this may or may not exist)
        # There's sometimes a static path like '/ecourtindia_v6/cause_list_print.php' - this is speculative.
        possible = urljoin(BASE_URL, '/ecourtindia_v6/cause_list_print.php')
        target = possible

    full = urljoin(BASE_URL, target)
    # try to download the page
    try:
        src = safe_get(driver, full)
        # try to find PDF link
        soup = BeautifulSoup(src, 'html.parser')
        pdf = None
        for a in soup.find_all('a', href=True):
            if a['href'].lower().endswith('.pdf'):
                pdf = urljoin(full, a['href'])
                break
        if pdf:
            out = download_file(pdf, out_dir)
            return {'cause_list_pdf': out, 'cause_list_url': pdf}
        else:
            # save HTML snapshot
            out_file = Path(out_dir) / f"cause_list_{datetime.now().strftime('%Y%m%d')}.html"
            out_file.write_text(src, encoding='utf-8')
            return {'cause_list_html': str(out_file), 'cause_list_url': full}
    except Exception as e:
        return {'error': str(e)}


def run_search(args):
    driver = init_driver(headless=not args.debug)
    try:
        target_dates = set()
        today = datetime.now().date()
        if args.today:
            target_dates.add(today)
        if args.tomorrow:
            target_dates.add(today + timedelta(days=1))

        results = {
            'query': {},
            'target_dates': [d.isoformat() for d in sorted(target_dates)],
            'listed': False,
            'entries': [],
            'downloads': [],
            'errors': [],
        }

        if args.cnr:
            results['query'] = {'cnr': args.cnr}
            try:
                page = search_by_cnr(driver, args.cnr)
                parsed = extract_listings_from_result_page(page, target_dates)
                results['listed'] = parsed['listed']
                results['entries'] = parsed['entries']
                if parsed['listed'] and args.download_pdf:
                    # find pdf link in page and download
                    soup = BeautifulSoup(page, 'html.parser')
                    pdf_link = None
                    for a in soup.find_all('a', href=True):
                        if a['href'].lower().endswith('.pdf'):
                            pdf_link = urljoin(BASE_URL, a['href'])
                            break
                    if pdf_link:
                        dl = download_file(pdf_link, args.output_dir)
                        results['downloads'].append(dl)
            except Exception as e:
                results['errors'].append(str(e))

        elif args.case_type and args.number and args.year:
            results['query'] = {'case_type': args.case_type, 'number': args.number, 'year': args.year}
            try:
                page = search_by_case_number(driver, args.case_type, args.number, args.year)
                parsed = extract_listings_from_result_page(page, target_dates)
                results['listed'] = parsed['listed']
                results['entries'] = parsed['entries']
                if parsed['listed'] and args.download_pdf:
                    soup = BeautifulSoup(page, 'html.parser')
                    pdf_link = None
                    for a in soup.find_all('a', href=True):
                        if a['href'].lower().endswith('.pdf'):
                            pdf_link = urljoin(BASE_URL, a['href'])
                            break
                    if pdf_link:
                        dl = download_file(pdf_link, args.output_dir)
                        results['downloads'].append(dl)
            except Exception as e:
                results['errors'].append(str(e))

        else:
            results['errors'].append('No valid query provided')

        # option: download full cause list
        if args.causelist:
            try:
                cl = download_cause_list_for_today(driver, args.output_dir)
                results['cause_list'] = cl
            except Exception as e:
                results['errors'].append(f"cause list error: {e}")

        # save results to JSON
        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = out_dir / f"ecourts_result_{ts}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"Results saved to: {filename}")
        if results.get('listed'):
            print("Case is listed for target date(s):")
            for e in results['entries']:
                print(f" - Date: {e.get('date')} | Serial: {e.get('serial')} | Court: {e.get('court_name')}")
        else:
            print("Case not listed for the requested date(s).")

        return results
    finally:
        try:
            driver.quit()
        except Exception:
            pass


def build_argparser():
    p = argparse.ArgumentParser(description="eCourts cause-list checker (Selenium)")
    # query options
    p.add_argument('--cnr', type=str, help='Full CNR string')
    p.add_argument('--case-type', type=str, help='Case type (e.g., CR, RSA)')
    p.add_argument('--number', type=int, help='Case number')
    p.add_argument('--year', type=int, help='Case year')

    # date options
    p.add_argument('--today', action='store_true', help='Check if listed today')
    p.add_argument('--tomorrow', action='store_true', help='Check if listed tomorrow')

    # other options
    p.add_argument('--download-pdf', action='store_true', help='If case PDF link available, download it')
    p.add_argument('--causelist', action='store_true', help='Attempt to download full cause list')
    p.add_argument('--output-dir', type=str, default='examples/outputs', help='Directory for outputs')
    p.add_argument('--debug', action='store_true', help='Run with visible browser (not headless)')

    return p


if __name__ == '__main__':
    args = build_argparser().parse_args()
    if not (args.cnr or (args.case_type and args.number and args.year) or args.causelist):
        print("Provide --cnr OR --case-type + --number + --year OR --causelist")
        exit(1)

    run_search(args)
# ```

# ---

# ## Next steps / Tips

# 1. Run the script once with `--debug` to see what the page looks like; then update the XPaths/CSS selectors in `search_by_cnr`, `search_by_case_number`, and `parse_cause_list_page` to match real elements on the site.
# 2. If the site requires additional form tokens or session cookies, use Selenium's browser session to read the network requests or copy form data.
# 3. If you want, I can:

#    * Produce a ready-to-download ZIP with these files.
#    * Push the project to a GitHub repo and create a README and license.
#    * Convert this into a small Flask API (bonus) that accepts case queries and returns JSON over HTTP.

# ---

# ## License

# MIT

# ---

# *End of project document.*
