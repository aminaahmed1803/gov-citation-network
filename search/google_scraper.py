import sys
import random
import requests
from time import sleep, time
from bs4 import BeautifulSoup
from urllib.parse import unquote  # to decode the url
from search.user_agents import get_useragent

# How long (at minimum) between successive requests
MIN_DELAY = 45  

class BotDetectionException(Exception):
    pass

class SearchResult:
    def __init__(self, url, title, description):
        self.url = url
        self.title = title
        self.description = description

    def __repr__(self):
        return f"SearchResult(url={self.url}, title={self.title}, description={self.description})"

class GoogleScraper:
    def __init__(self, proxy=None, timeout=5, ssl_verify=True):
        self.session = requests.Session()

        # allow proxy to be a single URL or a list; we'll pick randomly per request
        if proxy is None:
            self.proxies = None
        elif isinstance(proxy, (list, tuple)):
            self.proxies = proxy
        else:
            self.proxies = [proxy]

        self.timeout = timeout
        self.ssl_verify = ssl_verify
        self.last_request = 0
        self.backoff = 1  # initial backoff factor

    def _get_proxy(self):
        if not self.proxies:
            return None
        choice = random.choice(self.proxies)
        return {"https": choice, "http": choice}

    def _throttle(self):
        elapsed = time() - self.last_request
        wait_for = MIN_DELAY - elapsed
        if wait_for > 0:
            # base wait plus up to 5s random jitter
            sleep(wait_for + random.uniform(0, 5))
        self.last_request = time()

    def _maybe_prefetch(self):
        # 20% chance to fetch the Google homepage first (simulates a human landing)
        if random.random() < 0.2:
            try:
                self.session.get(
                    "https://www.google.com/",
                    headers={
                        "User-Agent": get_useragent(),
                        "Accept": "*/*",
                        "Accept-Language": random.choice([
                            "en-US,en;q=0.9",
                            "en-GB,en-US;q=0.8",
                            "fr-FR,fr;q=0.9,en;q=0.8"
                        ]),
                        "Referer": ""
                    },
                    timeout=self.timeout,
                    proxies=self._get_proxy(),
                    verify=self.ssl_verify
                )
                # small human-like pause
                sleep(random.uniform(1, 3))
            except Exception:
                pass  # ignore any homepage fetch errors

    def _req(self, term, results, lang, start, safe, region):
        headers = {
            "User-Agent": get_useragent(),
            "Accept": "*/*",
            "Accept-Language": random.choice([
                "en-US,en;q=0.9",
                "en-GB,en;q=0.8",
                "es-ES,es;q=0.9,en;q=0.8"
            ]),
            "Referer": random.choice([
                "https://www.google.com/",
                "https://www.google.com/?hl=en"
            ])
        }
        params = {
            "q": term,
            "num": results + 2,  # prevent multiple requests
            "hl": lang,
            "start": start,
            "safe": safe,
            "gl": region,
        }
        cookies = {
            'CONSENT': 'PENDING+987',  # bypass consent
            'SOCS': 'CAESHAgBEhIaAB',
        }

        attempted_clear = False
        while True:
            self._throttle()
            self._maybe_prefetch()

            resp = self.session.get(
                "https://www.google.com/search",
                headers=headers,
                params=params,
                proxies=self._get_proxy(),
                timeout=self.timeout,
                verify=self.ssl_verify,
                cookies=cookies,
            )

            text = resp.text

            # handle HTTP rate-limit
            if resp.status_code == 429:
                sleep(self.backoff * 2 + random.uniform(0, 1))
                self.backoff = min(self.backoff * 2, 300)
                continue

            # detect CAPTCHA / bot-block page
            lower = text.lower()
            if ("unusual traffic" in lower or "to continue, verify" in lower):
                # first time: clear session state & retry once
                if not attempted_clear:
                    self.session.cookies.clear()
                    self.session = requests.Session()
                    attempted_clear = True
                    sleep(random.uniform(10, 20))
                    continue
                raise BotDetectionException("Blocked by Google: CAPTCHA or unusual-traffic page detected")

            resp.raise_for_status()
            # success — reset backoff
            self.backoff = 1
            return text

    def search(self, term, num_results=10, lang="en", advanced=False,
               sleep_interval=0, safe="active", region=None, start_num=0, unique=False):
        fetched = 0
        seen = set()
        start = start_num

        while fetched < num_results:
            html = self._req(term, num_results - start, lang, start, safe, region)
            soup = BeautifulSoup(html, "html.parser")
            blocks = soup.find_all("div", class_="ezO2md")
            new_this_round = 0

            for b in blocks:
                link_tag = b.find("a", href=True)
                title_tag = link_tag.find("span", class_="CVA68e") if link_tag else None
                desc_tag = b.find("span", class_="FrIlee")
                if not (link_tag and title_tag and desc_tag):
                    continue

                url = unquote(link_tag["href"].split("&")[0].replace("/url?q=", ""))
                if unique and url in seen:
                    continue

                seen.add(url)
                fetched += 1
                new_this_round += 1

                if advanced:
                    yield SearchResult(url, title_tag.text, desc_tag.text)
                else:
                    yield url

                if fetched >= num_results:
                    break

            if new_this_round == 0:
                break

            start += 10
            # small sleep with jitter between pages as well
            sleep(sleep_interval + random.uniform(0, sleep_interval or 1))


# Example usage:
if __name__ == "__main__":
    scraper = GoogleScraper(proxy=None, timeout=5, ssl_verify=True)
    for url in scraper.search(
        "2018 Farm Bill (H. R. 2—Agriculture Improvement Act of 2018) Public Law No. 115-334.",
        num_results=5,
        sleep_interval=1,
        unique=True
    ):
        print(url)

