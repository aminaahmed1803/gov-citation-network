import time
import random
import requests
from bs4 import BeautifulSoup
from search.user_agents import get_useragent
from urllib.parse import urlparse, parse_qs

class BotDetectionException(Exception):
    """Raised when Google blocks us for suspected scraping."""
    pass

class ScholarScraper:
    def __init__(self, proxy=None, min_time_between_scrape=45):
        self.session = requests.Session()

        # support a single proxy or a list
        if proxy is None:
            self.proxies = None
        elif isinstance(proxy, (list, tuple)):
            self.proxies = proxy
        else:
            self.proxies = [proxy]

        self.last_time = 0
        self.min_time_between_scrape = min_time_between_scrape

    def _get_proxy(self):
        if not self.proxies:
            return None
        choice = random.choice(self.proxies)
        return {"https": choice, "http": choice}

    def _delay_if_needed(self):
        elapsed = time.time() - self.last_time
        wait = self.min_time_between_scrape - elapsed
        if wait > 0:
            # up to +2s jitter
            time.sleep(wait + random.uniform(0, 2))
        self.last_time = time.time()

    def _maybe_prefetch(self):
        # 20% chance to fetch the Scholar homepage first
        if random.random() < 0.2:
            try:
                self.session.get(
                    "https://scholar.google.com/",
                    headers={
                        "User-Agent": get_useragent(),
                        "Accept": "*/*",
                        "Accept-Language": random.choice([
                            "en-US,en;q=0.9",
                            "en-GB,en;q=0.8"
                        ]),
                        "Referer": ""
                    },
                    proxies=self._get_proxy(),
                    timeout=10,
                    verify=True
                )
                time.sleep(random.uniform(1, 3))
            except Exception:
                pass

    def _get_headers(self):
        return {
            "User-Agent": get_useragent(),
            "Accept": "*/*",
            "Accept-Language": random.choice([
                "en-US,en;q=0.9",
                "en-GB,en;q=0.8"
            ]),
            "Referer": random.choice([
                "https://scholar.google.com/",
                "https://scholar.google.com/scholar"
            ])
        }

    def search(self, query):
        """
        Perform a Google Scholar search and return a BeautifulSoup.
        Raises BotDetectionException if Google presents the CAPTCHA page.
        """
        self._delay_if_needed()
        self._maybe_prefetch()

        url = "https://scholar.google.com/scholar"
        params = {"q": query, "hl": "en"}

        # one-shot retry logic on detection
        attempted_clear = False
        while True:
            resp = self.session.get(
                url,
                params=params,
                headers=self._get_headers(),
                proxies=self._get_proxy(),
                timeout=10,
                verify=True
            )
            text = resp.text

            if resp.status_code != 200:
                raise Exception(f"Error retrieving page: HTTP {resp.status_code}")

            if "our systems have detected unusual traffic" in text.lower():
                if not attempted_clear:
                    self.session.cookies.clear()
                    self.session = requests.Session()
                    attempted_clear = True
                    time.sleep(random.uniform(10, 20))
                    continue
                raise BotDetectionException("Blocked by Google Scholar’s bot detection.")

            return BeautifulSoup(text, "html.parser")

    from urllib.parse import urlparse, parse_qs

    def get_scholar_data(self, query):

        soup = self.search(query)
        results = []

        for el in soup.select(".gs_r"):
            try:
                title_el = el.select_one(".gs_rt")
                if not title_el:
                    continue

            # title and link
                title = title_el.get_text(strip=True)
                a = title_el.select_one("a")
                title_link = a["href"] if a and a.has_attr("href") else ""

            # first look for the standard versions container
                versions_el = el.select_one(".gs_ggs .gs_nph")

            # if that fails, scan all <a> for text containing "version"
                if not versions_el:
                    for cand in el.find_all("a"):
                        text = cand.get_text(strip=True).lower()
                        if "version" in text:
                            versions_el = cand
                            break

                versions_link = ""
                if versions_el and versions_el.has_attr("href"):
                    versions_link = "https://scholar.google.com" + versions_el["href"]

            # assemble the result entry
                entry = {"title": title}
                if title_link:
                    entry["title_link"] = title_link
                if versions_link:
                    entry["versions_link"] = versions_link

                # extract cluster_id if present
                    qs = parse_qs(urlparse(versions_link).query)
                    if "cluster" in qs:
                        entry["cluster_id"] = qs["cluster"][0]

                results.append(entry)

            except Exception as e:
                print(f"Error processing element: {e}")

        return results


if __name__ == "__main__":
    scraper = ScholarScraper(proxy=None, min_time_between_scrape=45)
    queries = [
        "Tomson, Bill, Study: Rising fertilizer prices will hit farmers hard in 2022, AgriPulse, January 10, 2022, https://www.agri-pulse.com/articles/17036-study-rising-fertilizer-prices-will-hit-farmers-har.",
        "Ahrendsen, B.L., Dodson, C.B., Short, G., Rainey, R.L. and Snell, H.A., (2022) Beginning farmer and rancher credit usage by socially disadvantaged status, Agricultural Finance Review, Spring 2022, https://doi.org/10.1108/AFR-05-2021-0060."]
    for q in queries:
        try:
            data = scraper.get_scholar_data(q)
            print(data)
        except BotDetectionException as bde:
            print("Bot detection triggered:", bde)
            break
        except Exception as ex:
            print("Unexpected error:", ex)

