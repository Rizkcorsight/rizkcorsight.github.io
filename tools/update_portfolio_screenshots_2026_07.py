#!/usr/bin/env python3
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANGS = ["en", "es", "fr", "de", "it", "ja", "pt", "zh-hans", "zh-hant", "nl", "ko", "ar", "ru", "cs", "da", "fi", "he", "hi", "id", "nb", "pl", "sv", "tr", "vi"]
VERSION = "2026071504"
VERSIONS = {
    "partypilot": None,
}

# These images were selected after comparing every portfolio card with the
# current App Store screenshot set. Localized routes use localized artwork.
UPGRADES = {
    "brinepost": "brinepost-1.webp",
    "bearing": "bearing-1.webp",
    "cari": "cari-1.webp",
    "cue": "cue-1.webp",
    "handrift": "handrift-1.webp",
    "inquest": "inquest-1.webp",
    "manualnest": "manualnest-1.webp",
    "markline": "markline-1.webp",
    "partypilot": "partypilot-2026071506.webp",
    "plumes": "plumes-1.webp",
    "plushbeantracker": "plushbeantracker-1.webp",
    "postcardarchive": "postcardarchive-1.webp",
    "puzai": "puzai-1.webp",
    "rinmath": "rinmath-1.webp",
    "swaydar": "swaydar-1.webp",
    "sweetshowdown": "sweetshowdown-1.webp",
    "tidalpool": "tidalpool-1.webp",
}

for lang in LANGS:
    path = ROOT / ("index.html" if lang == "en" else f"{lang}/index.html")
    text = path.read_text()

    for slug, filename in UPGRADES.items():
        version = VERSIONS.get(slug, VERSION)
        suffix = f"?v={version}" if version else ""
        if lang == "en":
            replacement = f"/assets/screens/{filename}{suffix}"
            legacy_filename = "partypilot-1.webp" if slug == "partypilot" else filename
            text = re.sub(
                rf"/assets/screens/(?:{re.escape(filename)}|{re.escape(legacy_filename)})(?:\?v=\d+)?",
                replacement,
                text,
            )
        else:
            localized_filename = filename if slug == "partypilot" else f"{slug}.webp"
            legacy_localized_filename = f"{slug}.webp"
            replacement = f"/assets/screens/i18n/{lang}/{localized_filename}{suffix}"
            text = re.sub(
                rf"/assets/screens/(?:{re.escape(filename)}|i18n/{re.escape(lang)}/(?:{re.escape(localized_filename)}|{re.escape(legacy_localized_filename)}))(?:\?v=\d+)?",
                replacement,
                text,
            )

    text = re.sub(
        r'(src="/assets/screens/(?:handrift-1\.webp|i18n/[^/]+/handrift\.webp)\?v=\d+" width="300" height=")450(")',
        r"\g<1>650\g<2>",
        text,
    )
    path.write_text(text)
