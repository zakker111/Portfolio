#!/usr/bin/env python3
"""One-off helper: self-host the IBM Plex Mono + Syne latin subsets.

Fetches the exact woff2 files the page used to load from fonts.gstatic.com,
writes them under assets/fonts/, and swaps the Google Fonts stylesheet link in
index.html for local @font-face rules.

Nothing is written unless the downloaded bytes and the rewritten index.html
match the reviewed hashes, so a mismatch fails the run instead of shipping a
silently different page.
"""
import hashlib
import pathlib
import sys
import urllib.request

FONTS = {
    "assets/fonts/ibm-plex-mono-400.woff2": (
        "https://fonts.gstatic.com/s/ibmplexmono/v20/-F63fjptAgt5VM-kVkqdyU8n1i8q131nj-o.woff2",
        "c36f509c0a8f9f85f29cb44bc8701d8a9e0b14c499e77a884f789ead7093a7ac",
    ),
    "assets/fonts/ibm-plex-mono-500.woff2": (
        "https://fonts.gstatic.com/s/ibmplexmono/v20/-F6qfjptAgt5VM-kVkqdyU8n3twJwlBFgsAXHNk.woff2",
        "a76f53ca6612e7b3828eec2311098675b7f9849ae4169a8bcef6302aec02a6c0",
    ),
    "assets/fonts/ibm-plex-mono-600.woff2": (
        "https://fonts.gstatic.com/s/ibmplexmono/v20/-F6qfjptAgt5VM-kVkqdyU8n3vAOwlBFgsAXHNk.woff2",
        "ad4580d8cb4b5f627c2d18457656732f7f7b070f7837fbc380e08054157e6f6c",
    ),
    "assets/fonts/syne-latin.woff2": (
        "https://fonts.gstatic.com/s/syne/v24/8vIH7w4qzmVxm2BL9G78HEY.woff2",
        "cfff412005eed2f0152d1c110c78ac564642b943e64322fbd687083177d6fa70",
    ),
}

OLD_LINKS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Syne:wght@700;800&display=swap" rel="stylesheet">\n'
)

FONT_FACES = """/* Self-hosted fonts (latin subset) — no request leaves the visitor's browser until they consent. */
@font-face{font-family:'IBM Plex Mono';font-style:normal;font-weight:400;font-display:swap;src:url(assets/fonts/ibm-plex-mono-400.woff2) format('woff2');unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}
@font-face{font-family:'IBM Plex Mono';font-style:normal;font-weight:500;font-display:swap;src:url(assets/fonts/ibm-plex-mono-500.woff2) format('woff2');unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}
@font-face{font-family:'IBM Plex Mono';font-style:normal;font-weight:600;font-display:swap;src:url(assets/fonts/ibm-plex-mono-600.woff2) format('woff2');unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}
@font-face{font-family:'Syne';font-style:normal;font-weight:700;font-display:swap;src:url(assets/fonts/syne-latin.woff2) format('woff2');unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}
@font-face{font-family:'Syne';font-style:normal;font-weight:800;font-display:swap;src:url(assets/fonts/syne-latin.woff2) format('woff2');unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}
"""

EXPECTED_HTML_SHA256 = "07c93f0cca0676b0b115539bcf615323a2c8ffcb527c92a59eca6d9dc4bef61d"


def main() -> int:
    failed = False

    for path, (url, want) in FONTS.items():
        dest = pathlib.Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        data = dest.read_bytes() if dest.exists() else b""
        if hashlib.sha256(data).hexdigest() != want:
            request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(request, timeout=60) as response:
                data = response.read()
        got = hashlib.sha256(data).hexdigest()
        if got != want:
            print(f"FAIL {path}: sha256 {got} != {want}", file=sys.stderr)
            failed = True
            continue
        dest.write_bytes(data)
        print(f"ok   {path} ({len(data)} bytes)")

    index = pathlib.Path("index.html")
    html = index.read_text(encoding="utf-8")
    if OLD_LINKS in html:
        html = html.replace(OLD_LINKS, "", 1)
    if FONT_FACES not in html:
        html = html.replace(
            "<style>\n:root{--bg:#0f0f12;", "<style>\n" + FONT_FACES + ":root{--bg:#0f0f12;", 1
        )
    got = hashlib.sha256(html.encode()).hexdigest()
    if got != EXPECTED_HTML_SHA256:
        print(f"FAIL index.html: sha256 {got} != {EXPECTED_HTML_SHA256}", file=sys.stderr)
        return 1
    index.write_text(html, encoding="utf-8")
    print(f"ok   index.html ({len(html.encode())} bytes)")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
