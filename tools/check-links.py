#!/usr/bin/env python3
"""Fail loudly when any link on the page or in the docs is not HTTP 200.

Run by .github/workflows/refresh.yml on every scheduled refresh; also runnable
locally with `python3 tools/check-links.py`.

Checks:
- every https link on index.html (project buttons, nav, footer),
- every asset the page itself loads (fonts, og:image), resolved against the
  page's own og:url,
- every https link in README.md and AGENTS.md.

Localhost/loopback URLs are instructions for running the site yourself, not
public links, so they are skipped. Transient failures (network errors, 429 and
5xx) are retried before being reported; a final status other than 200 fails the
run and prints a GitHub annotation so it is visible on the run summary.
"""
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request
from html import unescape

ROOT = pathlib.Path(__file__).resolve().parent.parent
UA = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 Chrome/126 Safari/537.36 portfolio-link-check",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
}
SKIP_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "[::1]"}
ATTEMPTS = 3
RETRY_STATUS = {429, 500, 502, 503, 504}


def skip(url):
    host = re.sub(r"^https?://", "", url).split("/")[0].split(":")[0].lower()
    return host in SKIP_HOSTS or host.endswith(".localhost")


def collect():
    """Return {url: sorted list of source files} for everything worth checking."""
    links = {}

    def add(url, source):
        url = unescape(url.strip()).rstrip(".,);\"'")
        if not url.startswith("http") or skip(url):
            return
        links.setdefault(url, set()).add(source)

    page = ROOT / "index.html"
    if page.exists():
        html = page.read_text(encoding="utf-8")
        for url in re.findall(r'href="(https://[^"]+)"', html):
            add(url, "index.html")
        og = re.search(r'<meta property="og:url" content="([^"]+)"', html)
        base = og.group(1) if og else None
        if base:
            for rel in re.findall(r'url\((assets/[^)]+)\)', html):
                add(base.rstrip("/") + "/" + rel, "index.html")
        for url in re.findall(r'<meta (?:property|name)="(?:og:image|twitter:image)" content="(https://[^"]+)"', html):
            add(url, "index.html")

    for name in ("README.md", "AGENTS.md"):
        path = ROOT / name
        if not path.exists():
            continue
        for url in re.findall(r"https?://[^\s`)>\"\]]+", path.read_text(encoding="utf-8")):
            add(url, name)

    return {url: sorted(src) for url, src in links.items()}


def status(url):
    """Final HTTP status, retrying transient failures. None if unreachable."""
    code = None
    for attempt in range(ATTEMPTS):
        try:
            request = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.status
        except urllib.error.HTTPError as error:
            code = error.code
            if code not in RETRY_STATUS:
                return code
        except Exception:
            code = None
        if attempt + 1 < ATTEMPTS:
            time.sleep(2 * (attempt + 1))
    return code


def main():
    links = collect()
    if not links:
        print("::error::link check found no links to verify — is index.html missing?")
        return 1

    failures = []
    for url in sorted(links):
        code = status(url)
        if code == 200:
            print(f"ok    {url}")
        else:
            shown = code if code is not None else "unreachable"
            print(f"DEAD  {url} ({shown})  <- {', '.join(links[url])}")
            failures.append((url, shown, links[url]))

    print(f"\nchecked {len(links)} links, {len(failures)} dead")
    if failures:
        for url, shown, sources in failures:
            print(f"::error::Dead link ({shown}): {url} — referenced by {', '.join(sources)}")
        print("::error::Link check failed. Fix or remove the links above.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
