#!/usr/bin/env python3
"""Build website card screenshots from verified app-native localized exports.

The App Store may return an English fallback when a storefront has no uploaded
screenshots.  This script deliberately reads the local release screenshot
exports instead, so each website route receives the image for that language.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from PIL import Image

from build_localized_fallback_cards import make_card


ROOT = Path(__file__).resolve().parents[1]
APPLE = Path("/Users/rzopenclaw/Projects/Apps/Apple")

SITE_LOCALES = [
    "en",
    "es",
    "fr",
    "de",
    "it",
    "ja",
    "pt",
    "zh-hans",
    "zh-hant",
    "nl",
    "ko",
    "ar",
    "ru",
    "cs",
    "da",
    "fi",
    "he",
    "hi",
    "id",
    "nb",
    "pl",
    "sv",
    "tr",
    "vi",
]

# Keep the current website artwork where the latest app-native export is not
# publishable. These are deliberately excluded rather than silently replacing
# a clean card with a black capture or untranslated localization keys.
PRESERVE_EXISTING = {
    "cue": {"vi"},
    # Rinmath's current native captures are good for its shipped locales. The
    # other routes get localized, app-owned hero cards below.
    "rinmath": {
        "en", "es", "fr", "de", "it", "ja", "pt", "zh-hans", "nl", "ko", "ar", "ru",
    },
    # English already matches; every translated route gets a language-matched
    # card because the archived Sweet Showdown overlays themselves are English.
    "sweetshowdown": {"en"},
}

LOCALIZED_TOKEN = {
    "en": "en",
    "es": "es",
    "fr": "fr",
    "de": "de",
    "it": "it",
    "ja": "ja",
    "pt": "pt-BR",
    "zh-hans": "zh-Hans",
    "zh-hant": "zh-Hant",
    "nl": "nl",
    "ko": "ko",
    "ar": "ar",
    "ru": "ru",
    "cs": "cs",
    "da": "da",
    "fi": "fi",
    "he": "he",
    "hi": "hi",
    "id": "id",
    "nb": "nb",
    "pl": "pl",
    "sv": "sv",
    "tr": "tr",
    "vi": "vi",
}

INQUEST_TOKEN = {
    **LOCALIZED_TOKEN,
    "en": "en-US",
    "es": "es-ES",
    "fr": "fr-FR",
    "de": "de-DE",
}

PARTYPILOT_TOKEN = {
    **LOCALIZED_TOKEN,
    "en": "en-US",
    "es": "es-ES",
    "fr": "fr-FR",
    "de": "de-DE",
    "nl": "nl-NL",
    "ar": "ar-SA",
    "nb": "no",
}

def first_png(directory: Path, prefix: str) -> Path:
    matches = sorted(directory.glob(f"{prefix}*.png"))
    if not matches:
        raise FileNotFoundError(f"No {prefix} PNG in {directory}")
    return matches[0]


def git_history_image(repo: Path, source: str, target: Path, crop: tuple[int, int, int, int] | None = None) -> Path:
    """Materialize the commit that originally added a pruned store asset."""
    commit = subprocess.run(
        ["git", "log", "--all", "--diff-filter=A", "--format=%H", "--", source],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    if not commit:
        raise FileNotFoundError(f"No Git history for {repo / source}")
    payload = subprocess.run(
        ["git", "show", f"{commit[0]}:{source}"],
        cwd=repo,
        check=True,
        capture_output=True,
    ).stdout
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    if crop is not None:
        with Image.open(target) as image:
            cropped = image.crop(crop)
            cropped.save(target, "PNG", optimize=True)
    return target


def sources() -> dict[str, dict[str, Path]]:
    result: dict[str, dict[str, Path]] = {
        "tidalpool": {},
        "brinepost": {},
        "cue": {},
        "inquest": {},
        "manualnest": {},
        "postcardarchive": {},
        "bearing": {},
        "cari": {},
        "handrift": {},
        "swaydar": {},
        "partypilot": {},
        "puzai": {},
        "plumes": {},
        "plushbeantracker": {},
        "markline": {},
        "rinmath": {},
        "sweetshowdown": {},
    }

    tidal = APPLE / "TidalPool/marketing/screenshots/v-next/raw/iphone69"
    brine = APPLE / "Brinepost/qa/marketing/framed/ios"
    cue = APPLE / "Cue/marketing/marketing"
    inquest = APPLE / "Inquest/Marketing/ScreenshotsV2/output/store-screenshots/apple/iphone-6.9"
    manual = APPLE / "ManualNest/Store-Package/marketing/app-store/localized-iphone-65/v-next-2026-06-07/captioned"
    postcard = APPLE / "PostcardArchive/qa/marketing/framed/ios"
    bearing = APPLE / "Bearing/qa/marketing/newlocale/out/iphone69"
    cari = APPLE / "CariArtDesign/artifacts/website-screenshots/iphone69"
    handrift = APPLE / "Handrift/build/website-screenshots/iphone69"
    swaydar = APPLE / "Swaydar/build/website-screenshots/iphone69"
    partypilot = APPLE / "PartyPilot/fastlane/screenshots"
    puzai = APPLE / "PuzAI/build/website-screenshots/iphone69"
    app_captures = Path("/tmp/website-app-captures")
    history_cache = Path("/tmp/rizkcorsight-history-screens")

    for site, token in LOCALIZED_TOKEN.items():
        result["tidalpool"][site] = tidal / f"slot1_home_{token}.png"
        result["brinepost"][site] = brine / ("en-US" if site == "en" else token) / "iphone69_1_today.png"
        result["cue"][site] = cue / token / "hero.png"
        result["manualnest"][site] = manual / f"{token}.png"
        result["postcardarchive"][site] = postcard / ("en-US" if site == "en" else token) / "iphone69_1_archive.png"
        result["bearing"][site] = bearing / token / "01_sky.png"
        result["cari"][site] = cari / token / "01_onboarding.png"
        result["handrift"][site] = handrift / token / "letterforms.png"
        result["swaydar"][site] = swaydar / token / "onboarding.png"
        result["partypilot"][site] = partypilot / PARTYPILOT_TOKEN[site] / "01-iphone-69.png"
        result["puzai"][site] = puzai / token / "onboarding.png"
        result["plumes"][site] = app_captures / "plumes" / f"{site}.png"
        result["markline"][site] = app_captures / "markline" / f"{site}.png"

        plush_source = f"marketing/screenshots-FINAL-2026-06-08/appstore/iphone-6.9/{token}/01_catalog.png"
        result["plushbeantracker"][site] = git_history_image(
            APPLE / "PlushBeanTracker",
            plush_source,
            history_cache / "plushbeantracker" / f"{site}.png",
            crop=(135, 600, 1185, 2868),
        )

    # Cari's German onboarding copy currently overflows horizontally in-app.
    # The deterministic Manage Styles screen is fully localized and unclipped.
    result["cari"]["de"] = cari / "de/08_manage_styles.png"

    # These app builds do not yet ship every website locale. Use honest,
    # language-matched marketing cards made from their own hero artwork instead
    # of presenting English UI as if it were localized.
    for site in {"he", "ru", "tr"}:
        result["cari"][site] = make_card("cari", site)

    # The archived PuzAI capture set has cross-locale mixups (for example,
    # Vietnamese copy under Hebrew and Norwegian copy under Russian). Replace
    # the entire set with deterministic localized cards and real PuzAI art.
    for site in SITE_LOCALES:
        result["puzai"][site] = make_card("puzai", site)

    rinmath_missing = set(SITE_LOCALES) - PRESERVE_EXISTING["rinmath"]
    for site in rinmath_missing:
        result["rinmath"][site] = make_card("rinmath", site)

    for site in set(SITE_LOCALES) - PRESERVE_EXISTING["sweetshowdown"]:
        result["sweetshowdown"][site] = make_card("sweetshowdown", site)

    result["postcardarchive"]["hi"] = git_history_image(
        APPLE / "PostcardArchive",
        "marketing/screenshots-FINAL-2026-06-08/apple-app-store/iphone-6.9/hi/01_curator-wall.png",
        history_cache / "postcardarchive" / "hi.png",
    )

    for app, locales in PRESERVE_EXISTING.items():
        for site in locales:
            result[app].pop(site, None)

    for site, token in INQUEST_TOKEN.items():
        result["inquest"][site] = first_png(inquest / token, "01_")

    return result


def destination(app: str, site: str) -> Path:
    if site == "en":
        return ROOT / "assets/screens" / f"{app}-1.webp"
    return ROOT / "assets/screens/i18n" / site / f"{app}.webp"


def versioned_destination(app: str, site: str) -> Path | None:
    if app != "partypilot":
        return None
    filename = "partypilot-2026071506.webp"
    if site == "en":
        return ROOT / "assets/screens" / filename
    return ROOT / "assets/screens/i18n" / site / filename


def export_webp(source: Path, target: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        image = image.convert("RGB")
        width = round(image.width * 1300 / image.height)
        image = image.resize((width, 1300), Image.Resampling.LANCZOS)
        image.save(target, "WEBP", quality=90, method=6)


def main() -> None:
    selected = sources()
    expected = set(SITE_LOCALES)
    for app, localized in selected.items():
        app_expected = expected - PRESERVE_EXISTING.get(app, set())
        if set(localized) != app_expected:
            missing = sorted(app_expected - set(localized))
            extra = sorted(set(localized) - app_expected)
            raise RuntimeError(f"{app}: locale mismatch; missing={missing}, extra={extra}")
        for site in SITE_LOCALES:
            if site not in localized:
                print(f"{app:19} {site:8} <- preserved existing website artwork")
                continue
            export_webp(localized[site], destination(app, site))
            versioned = versioned_destination(app, site)
            if versioned is not None:
                export_webp(localized[site], versioned)
            print(f"{app:19} {site:8} <- {localized[site]}")


if __name__ == "__main__":
    main()
