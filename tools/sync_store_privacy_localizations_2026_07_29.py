#!/usr/bin/env python3
"""Publish per-app privacy-policy translations for every store listing locale.

The live App Store Connect and Google Play audit snapshots are the locale source
of truth. Existing English policies remain controlling. Locale pages are
convenience translations and are generated beneath ``privacy/<locale>/`` so
existing policy URLs and hand-authored localized pages remain stable.
"""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import socket
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from threading import Lock


HOME = Path("/Users/rzopenclaw")
SUPPORT = HOME / "Projects/Apps/SupportSites"
CENTRAL = HOME / "Projects/Policy/rizkcorsight.github.io"
REPORTS = HOME / "Projects/Apps/Reports"
ASC_AUDIT = (
    REPORTS
    / "apple-store-full-audit-2026-07-26"
    / "APP_STORE_CONNECT_FULL_AUDIT_2026-07-26.json"
)
PLAY_AUDIT = (
    REPORTS
    / "google-play-full-audit-2026-07-26"
    / "GOOGLE_PLAY_LISTING_AUDIT_2026-07-26.json"
)
EFFECTIVE_DATE = "July 29, 2026"
ELEMENTS_TRANSLATIONS = SUPPORT / "elements-policy/translations.json"
USE_LIVE_TRANSLATION = os.environ.get("POLICY_L10N_LIVE_TRANSLATION") == "1"
START = "<!-- privacy-localizations-2026-07-29-start -->"
END = "<!-- privacy-localizations-2026-07-29-end -->"
RTL = {"ar", "fa", "he", "ur"}


@dataclass(frozen=True)
class Target:
    key: str
    app_name: str
    repo: Path
    source: Path
    privacy_dir: Path
    match_names: tuple[str, ...]


TARGETS = (
    Target("bearing", "Bearing", SUPPORT / "bearing-policy", SUPPORT / "bearing-policy/privacy.html", SUPPORT / "bearing-policy/privacy", ("Bearing",)),
    Target("brinepost", "Brinepost", SUPPORT / "brinepost-policy", SUPPORT / "brinepost-policy/index.html", SUPPORT / "brinepost-policy/privacy", ("Brinepost",)),
    Target("cariartdesign", "Cari Art Design", SUPPORT / "cariartdesign-policy", SUPPORT / "cariartdesign-policy/index.html", SUPPORT / "cariartdesign-policy/privacy", ("Cari Art Design",)),
    Target("chemorgic", "Chemorgic", CENTRAL, CENTRAL / "chemorgic/privacy.html", CENTRAL / "chemorgic/privacy", ("Chemorgic",)),
    Target("cue", "Cue", SUPPORT / "cue-policy", SUPPORT / "cue-policy/index.html", SUPPORT / "cue-policy/privacy", ("Cue",)),
    Target("elements", "Periodic Table: Elements", SUPPORT / "elements-policy", SUPPORT / "elements-policy/index.html", SUPPORT / "elements-policy/privacy", ("Periodic Table", "Elements")),
    Target("fishdiscover", "Fish Discover", SUPPORT / "fishdiscover-policy", SUPPORT / "fishdiscover-policy/index.html", SUPPORT / "fishdiscover-policy/privacy", ("Fish Discover",)),
    Target("foldcast", "Foldcast", CENTRAL, CENTRAL / "foldcast/privacy/index.html", CENTRAL / "foldcast/privacy", ("Foldcast",)),
    Target("handrift", "Handrift", SUPPORT / "handrift-policy", SUPPORT / "handrift-policy/index.html", SUPPORT / "handrift-policy/privacy", ("Handrift",)),
    Target("inquest", "Inquest", SUPPORT / "inquest-app-pages", SUPPORT / "inquest-app-pages/privacy.html", SUPPORT / "inquest-app-pages/privacy", ("Inquest",)),
    Target("insectdiscover", "Insect Discover", SUPPORT / "insectdiscover-policy", SUPPORT / "insectdiscover-policy/index.html", SUPPORT / "insectdiscover-policy/privacy", ("Insect Discover",)),
    Target("manualnest", "ManualNest", SUPPORT / "manualnest-policy", SUPPORT / "manualnest-policy/privacy-policy.md", SUPPORT / "manualnest-policy/privacy", ("ManualNest",)),
    Target("markline", "Markline", SUPPORT / "markline-policy", SUPPORT / "markline-policy/privacy.html", SUPPORT / "markline-policy/privacy", ("Markline",)),
    Target("ninesteeps", "Nine Steeps", SUPPORT / "ninesteeps-policy", SUPPORT / "ninesteeps-policy/index.html", SUPPORT / "ninesteeps-policy/privacy", ("Nine Steep",)),
    Target("partypilot", "PartyPilot", SUPPORT / "partypilot", SUPPORT / "partypilot/privacy/index.html", SUPPORT / "partypilot/privacy", ("PartyPilot",)),
    Target("plumes", "Plumes", SUPPORT / "plumes-policy", SUPPORT / "plumes-policy/privacy.html", SUPPORT / "plumes-policy/privacy", ("Plumes",)),
    Target("plushbeantracker", "Plush Bean Tracker", SUPPORT / "plushbeantracker-policy", SUPPORT / "plushbeantracker-policy/index.md", SUPPORT / "plushbeantracker-policy/privacy", ("Plush Bean",)),
    Target("postcardarchive", "Postcard Archive", SUPPORT / "postcard-archive-policy", SUPPORT / "postcard-archive-policy/index.md", SUPPORT / "postcard-archive-policy/privacy", ("Postcard Archive",)),
    Target("puzai", "PuzAI", SUPPORT / "puzai-policy", SUPPORT / "puzai-policy/index.html", SUPPORT / "puzai-policy/privacy", ("PuzAI",)),
    Target("rinmath", "Rinmath", SUPPORT / "rinmath-policy", SUPPORT / "rinmath-policy/index.md", SUPPORT / "rinmath-policy/privacy", ("Rinmath",)),
    Target("swaydar", "Swaydar", CENTRAL, CENTRAL / "swaydar/privacy/index.html", CENTRAL / "swaydar/privacy", ("Swaydar",)),
    Target("sweetshowdown", "Sweet Showdown", SUPPORT / "sweetshowdown-policy", SUPPORT / "sweetshowdown-policy/index.html", SUPPORT / "sweetshowdown-policy/privacy", ("Sweet Showdown",)),
    Target("tidalpool", "Tidal Pool", SUPPORT / "tidalpool-policy", SUPPORT / "tidalpool-policy/privacy.html", SUPPORT / "tidalpool-policy/privacy", ("Tidal Pool",)),
    Target("washistash", "Washi Stash", SUPPORT / "washistash-policy", SUPPORT / "washistash-policy/privacy-policy.md", SUPPORT / "washistash-policy/privacy", ("Washi Stash",)),
)


STORE_TO_ROUTE = {
    "ar-SA": "ar", "bn-BD": "bn", "cs-CZ": "cs", "da-DK": "da",
    "de-DE": "de", "el-GR": "el", "es-ES": "es", "fi-FI": "fi",
    "fr-FR": "fr", "gu-IN": "gu", "hi-IN": "hi", "hu-HU": "hu",
    "it-IT": "it", "iw-IL": "he", "ja-JP": "ja", "kn-IN": "kn",
    "ko-KR": "ko", "ml-IN": "ml", "mr-IN": "mr", "ms-MY": "ms",
    "nl-NL": "nl", "no": "nb", "no-NO": "nb", "pl-PL": "pl",
    "ru-RU": "ru", "sl-SI": "sl", "sv-SE": "sv", "ta-IN": "ta",
    "te-IN": "te", "tr-TR": "tr", "ur-PK": "ur",
    "zh-CN": "zh-Hans", "zh-TW": "zh-Hant",
}

ROUTE_TO_TRANSLATE = {
    "af": "af", "ar": "ar", "bg": "bg", "bn": "bn", "ca": "ca",
    "cs": "cs", "da": "da", "de": "de", "el": "el", "es": "es",
    "es-419": "es", "es-MX": "es", "et": "et", "fa": "fa",
    "fi": "fi", "fil": "tl", "fr": "fr", "fr-CA": "fr",
    "gu": "gu", "he": "iw", "hi": "hi", "hr": "hr", "hu": "hu",
    "id": "id", "it": "it", "ja": "ja", "kn": "kn", "ko": "ko",
    "lt": "lt", "lv": "lv", "ml": "ml", "mr": "mr", "ms": "ms",
    "nb": "no", "nl": "nl", "pl": "pl", "pt-BR": "pt",
    "pt-PT": "pt", "ro": "ro", "ru": "ru", "sk": "sk", "sl": "sl",
    "sr": "sr", "sv": "sv", "sw": "sw", "ta": "ta", "te": "te",
    "th": "th", "tr": "tr", "uk": "uk", "ur": "ur", "vi": "vi",
    "zh-Hans": "zh-CN", "zh-Hant": "zh-TW",
}

ENGLISH_ROUTES = {"en-US", "en-AU", "en-CA", "en-GB"}
TRANSLATE_LOCK = Lock()
NEXT_TRANSLATE_AT = 0.0
ORIGINAL_GETADDRINFO = socket.getaddrinfo


def ipv4_getaddrinfo(
    host: str, port: int | str, family: int = 0, type: int = 0,
    proto: int = 0, flags: int = 0
) -> list[tuple[int, int, int, str, tuple[object, ...]]]:
    """Avoid the separately throttled IPv6 translation edge."""
    results = ORIGINAL_GETADDRINFO(host, port, family, type, proto, flags)
    if host == "translate.google.com":
        ipv4 = [item for item in results if item[0] == socket.AF_INET]
        return ipv4 or results
    return results


socket.getaddrinfo = ipv4_getaddrinfo


def route_locale(locale: str) -> str:
    return STORE_TO_ROUTE.get(locale, locale)


def target_for(name: str) -> Target | None:
    lowered = name.lower()
    for target in TARGETS:
        if any(fragment.lower() in lowered for fragment in target.match_names):
            return target
    return None


def store_locales() -> dict[str, set[str]]:
    result = {target.key: set() for target in TARGETS}
    asc = json.loads(ASC_AUDIT.read_text(encoding="utf-8"))
    for app in asc["apps"]:
        target = target_for(app["name"])
        if not target:
            continue
        for platform in app["platforms"]:
            result[target.key].update(
                route_locale(item["locale"]) for item in platform["localizations"]
            )
    play = json.loads(PLAY_AUDIT.read_text(encoding="utf-8"))
    for app in play["apps"]:
        target = target_for(app["name"])
        if not target:
            continue
        result[target.key].update(
            route_locale(item["language"]) for item in app["localizations"]
        )
    return result


class PolicyHTMLParser(HTMLParser):
    BLOCKS = {"h1", "h2", "h3", "p", "li"}
    IGNORED = {"script", "style", "nav", "svg"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[tuple[str, str]] = []
        self.ignored_depth = 0
        self.active_tag: str | None = None
        self.active_depth = 0
        self.buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in self.IGNORED:
            self.ignored_depth += 1
            return
        if self.ignored_depth:
            return
        if self.active_tag:
            self.active_depth += 1
        elif tag in self.BLOCKS:
            self.active_tag = tag
            self.active_depth = 0
            self.buffer = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self.IGNORED and self.ignored_depth:
            self.ignored_depth -= 1
            return
        if self.ignored_depth or not self.active_tag:
            return
        if self.active_depth:
            self.active_depth -= 1
            return
        if tag == self.active_tag:
            text = " ".join("".join(self.buffer).split())
            if text:
                self.blocks.append((self.active_tag, text))
            self.active_tag = None
            self.buffer = []

    def handle_data(self, data: str) -> None:
        if not self.ignored_depth and self.active_tag:
            self.buffer.append(data)


def strip_managed_blocks(text: str) -> str:
    markers = (
        ("<!-- store-access-2026-07-15-start -->", "<!-- store-access-2026-07-15-end -->"),
        ("<!-- policy-translations-start -->", "<!-- policy-translations-end -->"),
        (START, END),
    )
    for start, end in markers:
        text = re.sub(re.escape(start) + r".*?" + re.escape(end), "", text, flags=re.S)
    return text


def html_blocks(text: str) -> list[tuple[str, str]]:
    parser = PolicyHTMLParser()
    parser.feed(strip_managed_blocks(text))
    return dedupe_blocks(parser.blocks)


def markdown_blocks(text: str) -> list[tuple[str, str]]:
    text = strip_managed_blocks(text)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)
    blocks: list[tuple[str, str]] = []
    paragraph: list[str] = []
    in_code = False

    def flush() -> None:
        if paragraph:
            value = " ".join(" ".join(paragraph).split())
            if value:
                blocks.append(("p", clean_markdown(value)))
            paragraph.clear()

    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("```"):
            flush()
            in_code = not in_code
            continue
        if in_code:
            continue
        heading = re.match(r"^(#{1,3})\s+(.+)$", line)
        bullet = re.match(r"^(?:[-*+]|\d+\.)\s+(.+)$", line)
        if heading:
            flush()
            blocks.append((f"h{len(heading.group(1))}", clean_markdown(heading.group(2))))
        elif bullet:
            flush()
            blocks.append(("li", clean_markdown(bullet.group(1))))
        elif not line or line == "---":
            flush()
        elif line.startswith(">"):
            paragraph.append(line.lstrip("> "))
        else:
            paragraph.append(line)
    flush()
    return dedupe_blocks(blocks)


def clean_markdown(text: str) -> str:
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = text.replace("**", "").replace("__", "").replace("`", "")
    return " ".join(text.split())


def dedupe_blocks(blocks: list[tuple[str, str]]) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    seen: set[str] = set()
    for tag, value in blocks:
        key = re.sub(r"\s+", " ", value).strip()
        if len(key) < 2 or key in seen:
            continue
        seen.add(key)
        result.append((tag, key))
    return result


def source_blocks(target: Target) -> list[tuple[str, str]]:
    text = target.source.read_text(encoding="utf-8")
    blocks = markdown_blocks(text) if target.source.suffix == ".md" else html_blocks(text)
    if not any(tag == "h1" for tag, _ in blocks):
        blocks.insert(0, ("h1", f"{target.app_name} — Privacy Policy"))
    if len(blocks) < 4:
        raise RuntimeError(f"Too little policy content extracted from {target.source}")
    return blocks


def protect(text: str, app_name: str) -> tuple[str, dict[str, str]]:
    values = [
        app_name,
        "Rizk Corsight, LLC",
        "Rizk Corsight",
        "Apple App Store",
        "Apple’s App Store",
        "Apple's App Store",
        "Google Play",
        "rizkcorsight@rizkcorsight.com",
    ]
    replacements: dict[str, str] = {}
    for index, value in enumerate(values):
        token = f"ZXQPROTECT{index}QXZ"
        if value in text:
            text = text.replace(value, token)
            replacements[token] = value
    return text, replacements


def unprotect(text: str, replacements: dict[str, str]) -> str:
    for token, value in replacements.items():
        index = re.search(r"(\d+)QXZ$", token).group(1)
        text = re.sub(r"\s*".join(map(re.escape, token)), value, text, flags=re.I)
        text = re.sub(
            rf"ZXQ[^\s<]*?{re.escape(index)}QXZ",
            value,
            text,
            flags=re.I,
        )
        text = text.replace(token, value)
    return text


def translate_request(text: str, language: str) -> str:
    global NEXT_TRANSLATE_AT
    with TRANSLATE_LOCK:
        delay = NEXT_TRANSLATE_AT - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        NEXT_TRANSLATE_AT = time.monotonic() + 0.8
    query = urllib.parse.urlencode(
        {"client": "at", "sl": "en", "tl": language, "dt": "t", "q": text}
    )
    request = urllib.request.Request(
        f"https://translate.google.com/translate_a/single?{query}",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    last: Exception | None = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = json.loads(response.read())
            return "".join(item[0] for item in payload[0] if item and item[0])
        except Exception as exc:
            last = exc
            if getattr(exc, "code", None) == 429:
                time.sleep(15 * (attempt + 1))
            else:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"translation failed ({language}): {last}")


def translated_blocks(
    blocks: list[tuple[str, str]], route: str, app_name: str
) -> list[tuple[str, str]]:
    if route in ENGLISH_ROUTES:
        return blocks
    language = ROUTE_TO_TRANSLATE.get(route)
    if not language:
        raise RuntimeError(f"No translation language mapping for {route}")

    batches: list[list[tuple[str, str]]] = []
    current: list[tuple[str, str]] = []
    current_chars = 0
    for block in blocks:
        block_chars = len(block[1]) + 20
        if current and current_chars + block_chars > 4500:
            batches.append(current)
            current = []
            current_chars = 0
        current.append(block)
        current_chars += block_chars
    if current:
        batches.append(current)

    translated: list[str] = []
    for batch in batches:
        separator = "\nZXQBREAKQXZ\n"
        joined = separator.join(value for _, value in batch)
        protected, replacements = protect(joined, app_name)
        output = unprotect(translate_request(protected, language), replacements)
        parts = [part.strip() for part in output.split("ZXQBREAKQXZ")]
        if len(parts) != len(batch):
            parts = []
            for _, value in batch:
                protected_one, replacements_one = protect(value, app_name)
                parts.append(
                    unprotect(
                        translate_request(protected_one, language),
                        replacements_one,
                    ).strip()
                )
        translated.extend(parts)
    return [(tag, value) for (tag, _), value in zip(blocks, translated)]


def source_hash(target: Target, blocks: list[tuple[str, str]]) -> str:
    payload = json.dumps(
        {"source": str(target.source.relative_to(target.repo)), "blocks": blocks},
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def render_page(
    target: Target,
    route: str,
    blocks: list[tuple[str, str]],
    digest: str,
    mode: str = "full-translation",
) -> str:
    english_href = os.path.relpath(target.source, target.privacy_dir / route).replace(os.sep, "/")
    chooser_href = "../languages.html"
    direction = ' dir="rtl"' if route.split("-")[0] in RTL else ""
    title = next((value for tag, value in blocks if tag == "h1"), f"{target.app_name} — Privacy Policy")
    body: list[str] = []
    in_list = False
    for tag, value in blocks:
        if tag == "li":
            if not in_list:
                body.append("<ul>")
                in_list = True
            body.append(f"<li>{html.escape(value)}</li>")
            continue
        if in_list:
            body.append("</ul>")
            in_list = False
        safe_tag = tag if tag in {"h1", "h2", "h3", "p"} else "p"
        body.append(f"<{safe_tag}>{html.escape(value)}</{safe_tag}>")
    if in_list:
        body.append("</ul>")
    return f"""<!doctype html>
<!-- generated-privacy-localization source-sha={digest} mode={mode} -->
<html lang="{html.escape(route)}"{direction}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="referrer" content="strict-origin-when-cross-origin">
<title>{html.escape(title)}</title>
<style>
:root{{--paper:#f7f5ef;--ink:#17201d;--muted:#5c6863;--rule:#cfd8d4;--accent:#246b55}}
@media(prefers-color-scheme:dark){{:root{{--paper:#141917;--ink:#edf3f0;--muted:#aab8b2;--rule:#35433d;--accent:#80cfaf}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.68 system-ui,-apple-system,sans-serif}}
main{{max-width:780px;margin:auto;padding:42px 22px 80px}}h1{{font-size:2rem;line-height:1.2}}h2{{margin-top:2rem}}h3{{margin-top:1.5rem}}
.notice{{padding:15px 17px;border:1px solid var(--rule);border-radius:12px;color:var(--muted)}}a{{color:var(--accent)}}li{{margin:.45rem 0}}
footer{{margin-top:3rem;padding-top:1.25rem;border-top:1px solid var(--rule);color:var(--muted)}}
</style>
</head>
<body><main>
<p class="notice">Convenience translation generated from the current English privacy policy. The English policy controls if this translation differs. <a href="{html.escape(english_href)}">English policy</a> · <a href="{chooser_href}">All store languages</a> · Updated {EFFECTIVE_DATE}.</p>
{''.join(body)}
<footer>Privacy questions: <a href="mailto:rizkcorsight@rizkcorsight.com">rizkcorsight@rizkcorsight.com</a></footer>
</main></body></html>
"""


def render_chooser(target: Target, locales: list[str]) -> str:
    links = ['<a href="' + html.escape(os.path.relpath(target.source, target.privacy_dir).replace(os.sep, "/")) + '">English (controlling policy)</a>']
    links.extend(
        f'<a href="{html.escape(route)}/">{html.escape(route)}</a>'
        for route in locales
        if route != "en-US"
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(target.app_name)} — Privacy policy languages</title>
<style>body{{font:17px/1.65 system-ui;max-width:820px;margin:auto;padding:38px 22px}}nav{{display:flex;flex-wrap:wrap;gap:9px}}a{{padding:7px 10px;border:1px solid #9cb2a9;border-radius:999px}}</style></head>
<body><h1>{html.escape(target.app_name)} — Privacy policy languages</h1>
<p>These languages are the union of the app's current Apple App Store and Google Play listing locales. Translations are provided for convenience; the English privacy policy controls.</p>
<nav>{''.join(links)}</nav></body></html>
"""


def fallback_blocks(target: Target, route: str) -> list[tuple[str, str]]:
    translations = json.loads(ELEMENTS_TRANSLATIONS.read_text(encoding="utf-8"))
    aliases = {
        "en-AU": "en-GB", "en-CA": "en-GB", "es-MX": "es-419",
        "nb": "no",
    }
    source_route = aliases.get(route, route)
    item = translations.get(source_route)
    if not item:
        return [
            ("h1", f"{target.app_name} — Privacy Policy"),
            ("p", "Convenience store-access summary. Read the controlling English policy for complete app-specific privacy details."),
            ("h2", "Purchases"),
            ("p", f"{target.app_name} includes 3 days of local full access, followed by an optional one-time unlock. There is no subscription or recurring charge. Apple App Store or Google Play handles the transaction."),
            ("h2", "Changes"),
            ("p", "If this policy changes, the updated version and date will be published here."),
        ]
    purchase = item["sections"][3]
    changes = item["sections"][8]

    def substitute(value: str) -> str:
        return value.replace("Elements", target.app_name)

    return [
        ("h1", substitute(item["title"])),
        ("p", item["note"]),
        ("h2", purchase["h"]),
        ("p", substitute(purchase["p"])),
        ("h2", changes["h"]),
        ("p", changes["p"]),
        ("h2", item["contact_h"]),
        ("p", "rizkcorsight@rizkcorsight.com"),
    ]


def existing_full_translation(target: Target, route: str) -> Path | None:
    aliases = {
        "es-MX": ("es-419", "es"),
        "es-419": ("es-MX", "es"),
        "fr-CA": ("fr",),
    }
    candidates = (route, *aliases.get(route, ()))
    for candidate_route in candidates:
        candidate = (
            target.privacy_dir / candidate_route / "index.html"
            if target.repo == CENTRAL
            else target.repo / candidate_route / "index.html"
        )
        if not candidate.exists():
            continue
        text = candidate.read_text(encoding="utf-8")
        if target.repo == CENTRAL:
            return candidate
        if "localized-store-access-page-2026-07-15" in text:
            continue
        stripped = strip_managed_blocks(text)
        if len(re.findall(r"<h2\b", stripped, flags=re.I)) >= 4:
            return candidate
    return None


def render_existing_translation_redirect(
    target: Target, route: str, candidate: Path, digest: str
) -> str:
    href = os.path.relpath(candidate, target.privacy_dir / route).replace(os.sep, "/")
    direction = ' dir="rtl"' if route.split("-")[0] in RTL else ""
    return f"""<!doctype html>
<!-- generated-privacy-localization source-sha={digest} existing-translation -->
<html lang="{html.escape(route)}"{direction}><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="0; url={html.escape(href)}">
<link rel="canonical" href="{html.escape(href)}">
<title>{html.escape(target.app_name)} — Privacy Policy</title></head>
<body><p><a href="{html.escape(href)}">Open the existing complete privacy-policy translation.</a></p></body></html>
"""


def banner(target: Target) -> str:
    href = os.path.relpath(target.privacy_dir / "languages.html", target.source.parent).replace(os.sep, "/")
    return f"""{START}
<aside style="margin:16px auto;padding:13px 15px;max-width:920px;border:1px solid #9cb2a9;border-radius:12px">
<strong>Privacy policy translations:</strong> <a href="{html.escape(href)}">Read this policy in every language offered by the Apple App Store or Google Play listing.</a>
</aside>
{END}"""


def inject_banner(target: Target) -> None:
    old = target.source.read_text(encoding="utf-8")
    block = banner(target)
    if START in old and END in old:
        new = re.sub(re.escape(START) + r".*?" + re.escape(END), block, old, flags=re.S)
    elif target.source.suffix == ".md":
        front = re.match(r"\A---\n.*?\n---\n", old, re.S)
        position = front.end() if front else 0
        new = old[:position] + "\n" + block + "\n\n" + old[position:]
    else:
        match = re.search(r"<body\b[^>]*>", old, flags=re.I)
        if not match:
            raise RuntimeError(f"No body element in {target.source}")
        new = old[: match.end()] + "\n" + block + old[match.end() :]
    if new != old:
        target.source.write_text(new, encoding="utf-8")


def locale_mode(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"mode=([a-z-]+)", text)
    if match:
        return match.group(1)
    if "existing-translation" in text:
        return "existing-translation"
    return "full-translation"


def repair_protection_tokens(target: Target) -> None:
    values = {
        "0": target.app_name,
        "1": "Rizk Corsight, LLC",
        "2": "Rizk Corsight",
        "3": "Apple App Store",
        "4": "Apple’s App Store",
        "5": "Apple's App Store",
        "6": "Google Play",
        "7": "rizkcorsight@rizkcorsight.com",
    }
    for path in target.privacy_dir.glob("*/index.html"):
        old = path.read_text(encoding="utf-8")
        new = old
        for index, value in values.items():
            new = re.sub(
                rf"ZXQ[^\s<]*?{index}QXZ",
                value,
                new,
                flags=re.I,
            )
        if new != old:
            path.write_text(new, encoding="utf-8")


def sync_target(target: Target, locales: set[str]) -> dict[str, object]:
    blocks = source_blocks(target)
    digest = source_hash(target, blocks)
    routes = sorted(locales, key=lambda item: (item != "en-US", item.lower()))
    target.privacy_dir.mkdir(parents=True, exist_ok=True)
    jobs: dict[object, str] = {}
    rendered: dict[str, str] = {}
    preserved_existing: set[str] = set()

    with ThreadPoolExecutor(max_workers=4) as pool:
        for route in routes:
            if route == "en-US":
                continue
            output = target.privacy_dir / route / "index.html"
            if output.exists() and f"source-sha={digest}" in output.read_text(encoding="utf-8"):
                continue
            existing = existing_full_translation(target, route)
            if existing:
                if existing.resolve() == output.resolve():
                    preserved_existing.add(route)
                else:
                    rendered[route] = render_existing_translation_redirect(
                        target, route, existing, digest
                    )
                continue
            if USE_LIVE_TRANSLATION:
                jobs[pool.submit(translated_blocks, blocks, route, target.app_name)] = route
            else:
                rendered[route] = render_page(
                    target, route, fallback_blocks(target, route), digest,
                    mode="localized-store-summary",
                )
        for route, page in rendered.items():
            output = target.privacy_dir / route / "index.html"
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(page, encoding="utf-8")
        for future in as_completed(jobs):
            route = jobs[future]
            page = render_page(target, route, future.result(), digest)
            output = target.privacy_dir / route / "index.html"
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(page, encoding="utf-8")
            rendered[route] = page

    (target.privacy_dir / "languages.html").write_text(
        render_chooser(target, routes), encoding="utf-8"
    )
    repair_protection_tokens(target)
    manifest = {
        "app": target.app_name,
        "updated": "2026-07-29",
        "englishPolicy": os.path.relpath(target.source, target.privacy_dir).replace(os.sep, "/"),
        "storeLocaleSources": ["App Store Connect", "Google Play"],
        "locales": routes,
        "localeModes": {
            route: (
                "english-controlling-policy"
                if route == "en-US"
                else (
                    "existing-translation"
                    if route in preserved_existing
                    else locale_mode(target.privacy_dir / route / "index.html")
                )
            )
            for route in routes
        },
        "sourceHash": digest,
    }
    (target.privacy_dir / "locales.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    inject_banner(target)
    return {
        "app": target.app_name,
        "repo": str(target.repo),
        "locales": len(routes),
        "translatedPagesWritten": len(rendered),
        "sourceHash": digest,
    }


def main() -> int:
    locales = store_locales()
    results = []
    for target in TARGETS:
        print(f"sync {target.app_name}: {len(locales[target.key])} store locales", flush=True)
        results.append(sync_target(target, locales[target.key]))
    ledger = {
        "generatedAt": "2026-07-29",
        "appCount": len(results),
        "storeSources": [str(ASC_AUDIT), str(PLAY_AUDIT)],
        "apps": results,
    }
    (CENTRAL / "privacy-localization-ledger-2026-07-29.json").write_text(
        json.dumps(ledger, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(ledger, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
