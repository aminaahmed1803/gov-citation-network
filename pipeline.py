import re
import os
import sys
import json
import requests
from urllib.parse import urlparse

from search.google_scraper import GoogleScraper, BotDetectionException as GoogleBotDetectionException
from search.scholar_scraper import ScholarScraper, BotDetectionException as ScholarBotDetectionException

NUM_RESULTS = 5
ADVANCED = False
OUTPUT_DIR = "IDs"

def read_citations_from_file(file_path):
    citations = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    citations.append(line)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return citations

def extract_urls(text):
    url_pattern = r'https?://[^\s,;]+'
    doi_pattern = r'\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b'
    urls = re.findall(url_pattern, text)
    dois = re.findall(doi_pattern, text, flags=re.IGNORECASE)
    return "".join(urls + dois)

def classify(citation_list, package_id, subfolder):
    out_dir = os.path.join(OUTPUT_DIR, subfolder)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{package_id}.json")  # ← changed extension

    google_scraper = GoogleScraper(proxy=None, timeout=5, ssl_verify=True)
    scholar_scraper = ScholarScraper(min_time_between_scrape=45)

    with open(out_path, 'w', encoding='utf-8') as out_file:
        for citation in citation_list:
            found = False
            print(f"Processing citation: {citation}")

            url_or_doi = extract_urls(citation)
            clean_citation = citation.replace(url_or_doi, "").strip() if url_or_doi else citation

            # 1) GOVINFO lookup via Google
            try:
                for url in google_scraper.search( clean_citation + " govinfo", NUM_RESULTS, ADVANCED, sleep_interval=1,unique=True):
                    print(url)
                    if "https://www.govinfo.gov/content/pkg" in url:
                        path_parts = urlparse(url).path.split('/')
                        gov_id = path_parts[3] if len(path_parts) > 3 else ""
                        if gov_id != "" and gov_id == "pkg" and gov_id != package_id:
                            # build JSON object for government
                            obj = {
                                "citation": citation,
                                "type": "GOVERNMENT",
                                "id": gov_id,
                                "url": url
                            }
                            out_file.write(json.dumps(obj) + "\n")
                            out_file.flush()
                            print(gov_id, "GOVERNMENT")
                            found = True
                            break
            except (GoogleBotDetectionException, requests.exceptions.RequestException) as e:
                print(f"Google scraper error or blocked: {e}", file=sys.stderr)
                sys.exit(1)

            if found:
                continue

            # 2) Google Scholar cluster‐ID
            try:
                results = scholar_scraper.get_scholar_data(query=clean_citation)
            except (ScholarBotDetectionException, requests.exceptions.RequestException) as e:
                print(f"Scholar scraper error or blocked: {e}", file=sys.stderr)
                sys.exit(1)

            cit_clean = re.sub(r'[!@#$\.,]', '', clean_citation).lower()
            for res in results:
                title_clean = re.sub(r'[!@#$\.,]', '', res.get("title", "")).lower()
                if title_clean and title_clean in cit_clean and "cluster_id" in res:
                    # build JSON object for scholar
                    obj = {
                        "citation": citation,
                        "type": "SCHOLARLY",
                        "id": res["cluster_id"],
                        "title": res["title"],
                        "title_link": res.get("title_link", "")
                    }
                    out_file.write(json.dumps(obj) + "\n")
                    out_file.flush()
                    found = True
                    print(res['cluster_id'], "SCHOLARLY")
                    break

            if found:
                continue

            # 3) Other (just URL/DOI)
            if url_or_doi:
                obj = {
                    "citation": citation,
                    "type": "OTHER",
                    "id": url_or_doi
                }
                out_file.write(json.dumps(obj) + "\n")
                out_file.flush()
                print(url_or_doi, "OTHER")
                continue

            # 4) Fallback (unknown)
            obj = {"citation": citation, "type": "UNKNOWN"}
            out_file.write(json.dumps(obj) + "\n")
            out_file.flush()
            print("UNKNOWN")

def main():
    if len(sys.argv) < 2:
        print("Usage: python pipeline.py <folder_name1> [<folder_name2> ...]")
        sys.exit(1)

    for folder_name in sys.argv[1:]:
        txt_dir = os.path.join("txt", folder_name)
        if not os.path.isdir(txt_dir):
            print(f"Skipping {folder_name}: no such directory.")
            continue

        for fname in os.listdir(txt_dir):
            if not fname.endswith(".txt"):
                continue

            pkg_id = os.path.splitext(fname)[0]
            filepath = os.path.join(txt_dir, fname)
            print(f"Processing {filepath} → IDs/{folder_name}/{pkg_id}.json")
            citations = read_citations_from_file(filepath)
            classify(citations, pkg_id, folder_name)

if __name__ == "__main__":
    main()

