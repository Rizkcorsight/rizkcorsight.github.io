#!/usr/bin/env python3
"""Synchronize the portfolio's public store-access disclosure.

This script intentionally edits only public policy/support repositories. It
uses the already-reviewed Elements policy translations as the canonical copy
source, then substitutes the applicable app name without changing the legal
meaning of the translated disclosure.
"""

from __future__ import annotations

import html
import os
import re
from pathlib import Path


HOME = Path("/Users/rzopenclaw")
SUPPORT = HOME / "Projects/Apps/SupportSites"
CENTRAL = HOME / "Projects/Policy/rizkcorsight.github.io"
ELEMENTS = SUPPORT / "elements-policy"
START = "<!-- store-access-2026-07-15-start -->"
END = "<!-- store-access-2026-07-15-end -->"
RTL = {"ar", "fa", "he", "ur"}

COMMON_39 = [
    "en", "ar", "ca", "cs", "da", "de", "el", "en-AU", "en-CA", "en-GB",
    "es", "es-MX", "fi", "fr-CA", "fr", "he", "hi", "hr", "hu", "id",
    "it", "ja", "ko", "ms", "nl", "nb", "pl", "pt-BR", "pt-PT", "ro",
    "ru", "sk", "sv", "th", "tr", "uk", "vi", "zh-Hans", "zh-Hant",
]

LOCALES = {
    "bearing-policy": COMMON_39,
    "brinepost-policy": COMMON_39,
    "cariartdesign-policy": ["en", "ar", "ca", "cs", "da", "de", "el", "es", "fi", "fr-CA", "fr", "hi", "hr", "hu", "id", "it", "ja", "ko", "ms", "nl", "nb", "pl", "pt-BR", "pt-PT", "ro", "sk", "sv", "th", "vi", "zh-Hans", "zh-Hant"],
    "cue-policy": [x for x in COMMON_39 if x != "en-CA"],
    "elements-policy": ["en", "ar", "bn", "ca", "cs", "da", "de", "el", "en-GB", "es", "es-419", "fi", "fr-CA", "fr", "gu", "he", "hi", "hr", "hu", "id", "it", "ja", "kn", "ko", "ml", "mr", "ms", "nl", "nb", "pl", "pt-BR", "pt-PT", "ro", "ru", "sk", "sl", "sv", "ta", "te", "th", "tr", "uk", "ur", "vi", "zh-Hans", "zh-Hant"],
    "fishdiscover-policy": ["en", "ar", "bn", "ca", "cs", "da", "de", "el", "es", "fi", "fr", "he", "hi", "hr", "hu", "id", "it", "ja", "ko", "ms", "nb", "pl", "pt-BR", "pt-PT", "ro", "ru", "sk", "sl", "sv", "ta", "te", "th", "tr", "uk", "vi", "zh-Hans", "zh-Hant"],
    "handrift-policy": ["en", "ar", "bg", "ca", "cs", "da", "de", "el", "es-419", "es", "et", "fi", "fr", "he", "hi", "hr", "hu", "id", "it", "ja", "ko", "lt", "lv", "ms", "nl", "nb", "pl", "pt-BR", "pt-PT", "ro", "ru", "sk", "sl", "sv", "th", "tr", "uk", "vi", "zh-Hans", "zh-Hant"],
    "inquest-app-pages": COMMON_39,
    "manualnest-policy": ["en", "ar", "cs", "da", "de", "el", "es", "es-MX", "fi", "fr-CA", "fr", "he", "hi", "id", "it", "ja", "ko", "ms", "nl", "nb", "pl", "pt-BR", "pt-PT", "ro", "ru", "sv", "th", "tr", "uk", "vi", "zh-Hans", "zh-Hant"],
    "markline-policy": COMMON_39,
    "ninesteeps-policy": COMMON_39,
    "partypilot": COMMON_39,
    "plumes-policy": COMMON_39,
    "plushbeantracker-policy": COMMON_39,
    "postcard-archive-policy": [x for x in COMMON_39 if x not in {"en-AU", "en-CA", "en-GB"}],
    "puzai-policy": ["en", "ar", "bn", "cs", "da", "de", "el", "es", "fi", "fr", "he", "hi", "hu", "id", "it", "ja", "ko", "ms", "nl", "nb", "pl", "pt-BR", "pt-PT", "ro", "ru", "sv", "th", "tr", "uk", "ur", "vi", "zh-Hans", "zh-Hant"],
    "rinmath-policy": ["en", "ar", "de", "es", "es-MX", "fr", "it", "ja", "ko", "nl", "pt-BR", "ru", "zh-Hans"],
    "sweetshowdown-policy": ["en", "ar", "de", "es", "es-MX", "fr", "he", "it", "ja", "pt-BR", "zh-Hans"],
    "tidalpool-policy": COMMON_39,
    "washistash-policy": COMMON_39,
}

APP_NAMES = {
    "bearing-policy": "Bearing",
    "brinepost-policy": "Brinepost",
    "cariartdesign-policy": "Cari Art Design",
    "cue-policy": "Cue",
    "elements-policy": "Elements",
    "fishdiscover-policy": "Fish Discover",
    "handrift-policy": "Handrift",
    "inquest-app-pages": "Inquest",
    "manualnest-policy": "ManualNest",
    "markline-policy": "Markline",
    "ninesteeps-policy": "Nine Steeps",
    "partypilot": "PartyPilot",
    "plumes-policy": "Plumes",
    "plushbeantracker-policy": "Plush Bean Tracker",
    "postcard-archive-policy": "Postcard Archive",
    "puzai-policy": "PuzAI",
    "rinmath-policy": "Rinmath",
    "sweetshowdown-policy": "Sweet Showdown",
    "tidalpool-policy": "TidalPool",
    "washistash-policy": "Washi Stash",
}

ALIASES = {
    "en-AU": "en", "en-CA": "en", "en-GB": "en-GB",
    "es-MX": "es-419", "nb": "no",
}


def source_template(locale: str) -> tuple[str, str]:
    source_locale = ALIASES.get(locale, locale)
    if source_locale == "en":
        path = ELEMENTS / "index.html"
        source_app = "Elements"
    elif source_locale == "sw":
        path = SUPPORT / "puzai-policy/sw/index.html"
        source_app = "PuzAI"
    else:
        path = ELEMENTS / source_locale / "index.html"
        source_app = "Elements"
    if not path.exists():
        path = ELEMENTS / "index.html"
        source_app = "Elements"
    text = path.read_text()
    pairs = re.findall(r"<h2>(.*?)</h2>\s*<p>(.*?)</p>", text, re.S)
    for heading, paragraph in pairs:
        plain = html.unescape(re.sub(r"<[^>]+>", "", paragraph))
        if source_app in plain and "App Store" in plain and "Google Play" in plain:
            return heading.strip(), paragraph.strip()
    raise RuntimeError(f"Purchase translation not found in {path}")


def localized_copy(app: str, locale: str) -> tuple[str, str]:
    heading, paragraph = source_template(locale)
    return heading, paragraph.replace("Elements", html.escape(app)).replace("PuzAI", html.escape(app))


def translation_note(locale: str, href: str) -> str:
    source_locale = ALIASES.get(locale, locale)
    if source_locale == "en":
        return f'<a href="{html.escape(href)}">Read the complete English privacy policy.</a>'
    path = ELEMENTS / source_locale / "index.html"
    if not path.exists():
        return f'<a href="{html.escape(href)}">Read the complete English privacy policy.</a>'
    match = re.search(r'<p class="note">(.*?)</p>', path.read_text(), re.S)
    if not match:
        return f'<a href="{html.escape(href)}">Read the complete English privacy policy.</a>'
    note = re.sub(r'href="[^"]*"', f'href="{html.escape(href)}"', match.group(1))
    return note


def locale_for_file(repo: Path, path: Path) -> str:
    relative = path.relative_to(repo)
    if len(relative.parts) >= 2 and relative.parts[0] in set(LOCALES.get(repo.name, [])) | {"sw", "sr", "fa", "fil", "bg", "et", "lt", "lv", "sl"}:
        return relative.parts[0]
    return "en"


def notice(app: str, locale: str, href: str) -> str:
    heading, paragraph = localized_copy(app, locale)
    lang = locale.split("-")[0]
    direction = ' dir="rtl"' if lang in RTL else ""
    return f'''{START}
<section class="store-access-policy" lang="{html.escape(locale)}"{direction} style="margin:24px auto;padding:16px 18px;max-width:920px;border:2px solid #246b55;border-radius:14px;background:#f3fbf7;color:#10241d">
<h2 style="margin-top:0">{heading}</h2>
<p>{paragraph}</p>
<p style="margin-bottom:0"><a href="{html.escape(href)}#{html.escape(locale)}">Store access terms in every supported language</a> · Updated July 15, 2026</p>
</section>
{END}'''


def localized_policy_page(app: str, locale: str, full_policy_href: str, access_href: str) -> str:
    heading, paragraph = localized_copy(app, locale)
    lang = locale.split("-")[0]
    direction = ' dir="rtl"' if lang in RTL else ""
    note = translation_note(locale, full_policy_href)
    block = notice(app, locale, access_href)
    return f'''<!doctype html>
<!-- localized-store-access-page-2026-07-15 -->
<html lang="{html.escape(locale)}"{direction}><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(app)} — {heading}</title>
<style>body{{font:16px/1.65 system-ui,-apple-system,sans-serif;max-width:980px;margin:auto;padding:28px;color:#17231f}}.note{{color:#53665f}}[dir=rtl]{{text-align:right}}</style></head><body>
<h1>{html.escape(app)} — {heading}</h1>
<p class="note">{note}</p>
{block}
</body></html>
'''


def replace_marker(text: str, block: str) -> str:
    if START in text and END in text:
        return re.sub(re.escape(START) + r".*?" + re.escape(END), block, text, flags=re.S)
    body = re.search(r"<body\b[^>]*>", text, re.I)
    if body:
        return text[:body.end()] + "\n" + block + text[body.end():]
    return block + "\n" + text


def sync_html(repo: Path, path: Path, app: str, locale: str) -> None:
    href = os.path.relpath(repo / "store-access.html", path.parent).replace(os.sep, "/")
    old = path.read_text()
    new = replace_marker(old, notice(app, locale, href))
    if new != old:
        path.write_text(new)


def sync_markdown(repo: Path, path: Path, app: str) -> None:
    block = f'''{START}
> **Store access and purchases — updated July 15, 2026:** {app} is free to download and includes a local 3-day full-access trial. After the trial, continued access requires one one-time unlock at the price displayed by Apple App Store or Google Play. There is no subscription, automatic renewal, or recurring charge. [Read this disclosure in every supported language](store-access.html).
{END}'''
    old = path.read_text()
    if START in old and END in old:
        new = re.sub(re.escape(START) + r".*?" + re.escape(END), block, old, flags=re.S)
    else:
        front = re.match(r"\A---\n.*?\n---\n", old, re.S)
        pos = front.end() if front else 0
        new = old[:pos] + "\n" + block + "\n\n" + old[pos:]
    if new != old:
        path.write_text(new)


def all_existing_locales(repo: Path) -> set[str]:
    return {p.parent.name for p in repo.glob("*/index.html") if p.parent.name not in {"privacy", "support", "face-data"}}


def access_page(app: str, locales: list[str]) -> str:
    links = " ".join(f'<a href="#{html.escape(loc)}">{html.escape(loc)}</a>' for loc in locales)
    sections = []
    for locale in locales:
        heading, paragraph = localized_copy(app, locale)
        lang = locale.split("-")[0]
        direction = ' dir="rtl"' if lang in RTL else ""
        sections.append(f'''<article id="{html.escape(locale)}" lang="{html.escape(locale)}"{direction}><h2>{heading} <small>({html.escape(locale)})</small></h2><p>{paragraph}</p></article>''')
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(app)} — Store access and purchases</title>
<style>body{{font:16px/1.65 system-ui,-apple-system,sans-serif;max-width:980px;margin:auto;padding:28px;color:#17231f}}nav{{display:flex;flex-wrap:wrap;gap:8px;margin:20px 0 30px}}nav a{{padding:5px 9px;border:1px solid #9db7ad;border-radius:999px}}article{{padding:16px 0;border-top:1px solid #d7e2de}}small{{font-weight:400;color:#53665f}}[dir=rtl]{{text-align:right}}</style></head><body>
<h1>{html.escape(app)} — Store access and purchases</h1>
<p><strong>Effective July 15, 2026.</strong> This policy reconciles the access and purchase model used by the Apple App Store and Google Play versions of {html.escape(app)}. The English policy controls if a translation differs.</p>
<nav aria-label="Languages">{links}</nav>
{''.join(sections)}
</body></html>
'''


def repair_known_conflicts(repo: Path) -> None:
    for path in list(repo.rglob("*.html")) + list(repo.rglob("*.md")):
        if ".git" in path.parts:
            continue
        old = path.read_text()
        new = old
        if repo.name == "sweetshowdown-policy":
            accurate = "Sweet Showdown is free to download with a local 3-day full-access trial. After the trial, one optional one-time purchase unlocks continued access. There is no subscription, auto-renewal, recurring charge, consumable purchase, advertising, account, analytics, tracking, chat, or developer backend."
            new = re.sub(r"Sweet Showdown is paid upfront in the app stores and has no in-app purchases, subscriptions, consumables, ads, accounts, analytics, tracking, chat, or developer backend\.", accurate, new)
            new = re.sub(r"Sweet Showdown is paid upfront through the app store where you installed it\. It has no in-app purchases, no subscriptions, no auto-renewal, no advertising, and no consumable purchases\.", accurate, new)
            new = re.sub(r"The app is paid upfront in the app stores and has no in-app purchases, subscriptions, ads, consumables, or unlock purchases\.", accurate, new)
            new = new.replace("There are no in-app purchases, subscriptions, ads, tracking, chat, or consumable purchases.", "There is one optional non-consumable unlock after the local 3-day trial; there are no subscriptions, ads, tracking, chat, recurring charges, or consumable purchases.")
        if repo.name == "brinepost-policy":
            new = new.replace("confirmation that the unlock or trial belongs to your store account", "confirmation that you own the unlock; the 3-day trial starts and remains local to your device")
            new = new.replace("The 3-day trial is free. No subscription.", "The free 3-day trial starts locally on your device and is not a store product or subscription. There is no subscription or recurring charge.")
        if repo.name == "partypilot":
            new = new.replace("Apple StoreKit handles purchase, restore, refund, receipt, and localized price display.", "Apple StoreKit or Google Play Billing handles purchase, restore, refund, receipt, and localized price display, depending on the store where the app was downloaded.")
            new = new.replace("outside Apple's in-app purchase system", "outside Apple App Store or Google Play purchase systems")
            new = new.replace("Apple may process purchase, restore, transaction verification, and localized price display.", "Apple App Store or Google Play may process purchase, restore, transaction verification, and localized price display, depending on the installed platform.")
        if repo.name == "fishdiscover-policy":
            new = new.replace("Apple processes App Store purchases and restoration under Apple’s privacy policy.", "Apple App Store or Google Play processes purchases and restoration under the applicable store privacy policy.")
        if repo.name == "postcard-archive-policy":
            new = new.replace("If you choose Postcard Archive Pro or Full Access, Apple StoreKit or Google Play Billing handles the one-time unlock", "Postcard Archive is free to download with a local 3-day full-access trial. After the trial, if you choose Postcard Archive Pro or Full Access, Apple StoreKit or Google Play Billing handles the one-time unlock")
        if new != old:
            path.write_text(new)


def sync_repo(repo_name: str) -> None:
    repo = SUPPORT / repo_name
    app = APP_NAMES[repo_name]
    locales = sorted(set(LOCALES[repo_name]) | all_existing_locales(repo), key=lambda x: (x != "en", x.lower()))
    (repo / "store-access.html").write_text(access_page(app, locales))
    full_policy = "../privacy.html" if (repo / "privacy.html").exists() else "../"
    for locale in locales:
        if locale == "en":
            continue
        path = repo / locale / "index.html"
        generated = path.exists() and ("localized-store-access-page-2026-07-15" in path.read_text() or (path.stat().st_size < 6000 and START in path.read_text() and path.read_text().count("<h2") == 1))
        if not path.exists() or generated:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(localized_policy_page(app, locale, full_policy, "../store-access.html"))
    for path in [repo / "index.html", repo / "privacy.html", repo / "terms.html"]:
        if path.exists():
            sync_html(repo, path, app, "en")
    for path in repo.glob("*/index.html"):
        if path.parent.name not in {"privacy", "support", "face-data"}:
            sync_html(repo, path, app, locale_for_file(repo, path))
    for path in [repo / "index.md", repo / "privacy-policy.md"]:
        if path.exists():
            sync_markdown(repo, path, app)
    if repo_name == "partypilot":
        sync_html(repo, repo / "privacy/index.html", app, "en")
    repair_known_conflicts(repo)


CENTRAL_APPS = {
    "bearing": ("Bearing", COMMON_39, ["bearing/privacy.html"]),
    "brinepost": ("Brinepost", COMMON_39, ["brinepost/privacy.html", "brinepost/privacy/index.html"]),
    "cariartdesign-policy": ("Cari Art Design", LOCALES["cariartdesign-policy"], ["cariartdesign-policy/index.html"]),
    "chemorgic": ("Chemorgic", [x for x in COMMON_39 if x not in {"en-AU", "en-CA", "en-GB"}], ["chemorgic/privacy.html"]),
    "fishdiscover": ("Fish Discover", LOCALES["fishdiscover-policy"], ["fishdiscover/privacy/index.html"]),
    "foldcast": ("Foldcast", ["en", "ar", "cs", "da", "de", "el", "es", "fi", "fr", "he", "hi", "hu", "id", "it", "ja", "ko", "nl", "nb", "pl", "pt-BR", "pt-PT", "ro", "ru", "sv", "th", "tr", "uk", "vi", "zh-Hans", "zh-Hant"], ["foldcast/privacy/index.html"]),
    "plumes": ("Plumes", COMMON_39, ["plumes/privacy.html"]),
    "swaydar": ("Swaydar", COMMON_39, ["swaydar/privacy/index.html"]),
    "tidalpool": ("TidalPool", COMMON_39, ["tidalpool/privacy.html", "tidalpool/policy/index.html", "tidalpool-policy/index.html"]),
}


def sync_central() -> None:
    for slug, (app, configured, relatives) in CENTRAL_APPS.items():
        locales = sorted(set(configured), key=lambda x: (x != "en", x.lower()))
        page = CENTRAL / slug / "store-access.html"
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(access_page(app, locales))
        for relative in relatives:
            path = CENTRAL / relative
            if path.exists():
                href = os.path.relpath(page, path.parent).replace(os.sep, "/")
                old = path.read_text()
                new = replace_marker(old, notice(app, "en", href))
                if new != old:
                    path.write_text(new)
        if slug == "cariartdesign-policy":
            localized_root = CENTRAL / slug
            full_policy = "../"
        elif slug == "tidalpool":
            localized_root = CENTRAL / "tidalpool/policy"
            full_policy = "../"
        elif slug in {"bearing", "chemorgic", "plumes"}:
            localized_root = CENTRAL / slug / "privacy"
            full_policy = "../../privacy.html"
        else:
            localized_root = CENTRAL / slug / "privacy"
            full_policy = "../"
        for locale in locales:
            if locale == "en":
                continue
            path = localized_root / locale / "index.html"
            generated = path.exists() and ("localized-store-access-page-2026-07-15" in path.read_text() or (path.stat().st_size < 6000 and START in path.read_text() and path.read_text().count("<h2") == 1))
            if not path.exists() or generated:
                path.parent.mkdir(parents=True, exist_ok=True)
                access_href = os.path.relpath(page, path.parent).replace(os.sep, "/")
                path.write_text(localized_policy_page(app, locale, full_policy, access_href))
        if slug == "swaydar":
            for path in (CENTRAL / "swaydar/privacy").glob("*/index.html"):
                locale = path.parent.name
                href = os.path.relpath(page, path.parent).replace(os.sep, "/")
                old = path.read_text()
                new = replace_marker(old, notice(app, locale, href))
                if new != old:
                    path.write_text(new)


def validate() -> None:
    failures: list[str] = []
    page_count = 0
    locale_count = 0
    forbidden = re.compile(r"paid upfront|unlock or trial belongs|trial belongs to your store account", re.I)
    for repo_name, configured in LOCALES.items():
        repo = SUPPORT / repo_name
        locales = sorted(set(configured) | all_existing_locales(repo))
        access = (repo / "store-access.html").read_text()
        for locale in locales:
            locale_count += 1
            if f'id="{locale}"' not in access:
                failures.append(f"{repo_name}: store-access.html missing {locale}")
            if locale != "en":
                path = repo / locale / "index.html"
                if not path.exists():
                    failures.append(f"{repo_name}: missing localized page {locale}")
                else:
                    text = path.read_text()
                    page_count += 1
                    if START not in text or END not in text:
                        failures.append(f"{path}: missing authoritative notice")
                    marker = text[text.find(START):text.find(END) + len(END)]
                    if "App Store" not in marker or "Google Play" not in marker:
                        failures.append(f"{path}: notice does not cover both stores")
        for path in list(repo.rglob("*.html")) + list(repo.rglob("*.md")):
            if ".git" not in path.parts and forbidden.search(path.read_text()):
                failures.append(f"{path}: stale monetization wording")
    for slug, (app, configured, _) in CENTRAL_APPS.items():
        access = CENTRAL / slug / "store-access.html"
        text = access.read_text()
        for locale in configured:
            if f'id="{locale}"' not in text:
                failures.append(f"central/{slug}: missing {locale}")
    roots = [SUPPORT / name for name in LOCALES] + [CENTRAL]
    for root in roots:
        for path in root.rglob("*.html"):
            if ".git" in path.parts:
                continue
            text = path.read_text()
            if "localized-store-access-page-2026-07-15" in text:
                check_text = text
            elif START in text and END in text:
                check_text = text[text.find(START):text.find(END) + len(END)]
            else:
                continue
            for href in re.findall(r'href="([^"]+)"', check_text):
                target = href.split("#", 1)[0].split("?", 1)[0]
                if not target or target.startswith(("http://", "https://", "mailto:", "tel:", "data:", "/")):
                    continue
                resolved = (path.parent / target).resolve()
                exists = resolved.exists()
                if resolved.is_dir():
                    exists = (resolved / "index.html").exists() or (resolved / "index.md").exists()
                if not exists:
                    failures.append(f"{path}: missing local href {href}")
    if failures:
        raise RuntimeError("Policy validation failed:\n" + "\n".join(failures))
    print(f"Validated {locale_count} app-language mappings and {page_count} localized policy pages.")


def main() -> None:
    for name in LOCALES:
        sync_repo(name)
    sync_central()
    validate()
    print(f"Synchronized {len(LOCALES)} policy repositories and {len(CENTRAL_APPS)} central policy surfaces.")


if __name__ == "__main__":
    main()
