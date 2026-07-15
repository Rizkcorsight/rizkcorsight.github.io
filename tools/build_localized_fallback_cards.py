#!/usr/bin/env python3
"""Create language-matched portfolio art when an app lacks that runtime locale.

These cards use real app-owned hero artwork and the already-reviewed localized
website description. They are deliberately used only where an app screenshot
would otherwise show English UI (or a blank/failed capture).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
APPLE = Path("/Users/rzopenclaw/Projects/Apps/Apple")
OUT = Path("/tmp/rizkcorsight-localized-fallbacks")
FONT = Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf")

SITE_LOCALES = [
    "en", "es", "fr", "de", "it", "ja", "pt", "zh-hans", "zh-hant",
    "nl", "ko", "ar", "ru", "cs", "da", "fi", "he", "hi", "id",
    "nb", "pl", "sv", "tr", "vi",
]

RTL = {"ar", "he"}

ART = {
    "partypilot": APPLE / "PartyPilot/iOSApp/PartyPilot/Assets.xcassets/gen_hero02.imageset/gen_hero02.png",
    "cari": APPLE / "CariArtDesign/app/art/onboarding/meet_the_artists_hero.png",
    "rinmath": APPLE / "Rinmath/Rinmath/Resources/Assets.xcassets/OnboardingHero.imageset/onboarding-hero@3x.png",
    "sweetshowdown": APPLE / "SweetShowdown/iPhone/SweetShowdown/Assets.xcassets/gen_launch05.imageset/gen_launch05.png",
    "puzai": APPLE / "PuzAI/ios/PuzAICore/Sources/PuzAIAppShell/Resources/Generated.xcassets/PuzSampleReference.imageset/PuzSampleReference@3x.png",
}

PALETTES = {
    "partypilot": ((250, 244, 225), (21, 92, 87), (25, 46, 44)),
    "cari": ((255, 239, 225), (198, 70, 47), (55, 37, 31)),
    "rinmath": ((9, 9, 12), (241, 174, 53), (250, 247, 238)),
    "sweetshowdown": ((24, 18, 64), (255, 83, 154), (255, 248, 231)),
    "puzai": ((247, 242, 226), (38, 100, 104), (30, 45, 47)),
}


def page(locale: str) -> Path:
    return ROOT / ("index.html" if locale == "en" else f"{locale}/index.html")


def localized_copy(locale: str, slug: str) -> tuple[str, str]:
    html = page(locale).read_text(encoding="utf-8")
    scripts = re.findall(
        r'<script type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S
    )
    for raw in scripts:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if data.get("@type") != "ItemList":
            continue
        for row in data.get("itemListElement", []):
            item = row.get("item", {})
            if str(item.get("@id", "")).endswith(f"#{slug}"):
                return item["name"], item["description"]
    raise KeyError(f"No {slug} copy in {page(locale)}")


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT), size=size, layout_engine=ImageFont.Layout.RAQM)


def fit_crop(image: Image.Image, size: tuple[int, int], focus_x: float = 0.5) -> Image.Image:
    target_w, target_h = size
    scale = max(target_w / image.width, target_h / image.height)
    resized = image.resize(
        (round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS
    )
    left = round((resized.width - target_w) * focus_x)
    top = (resized.height - target_h) // 2
    return resized.crop((left, top, left + target_w, top + target_h))


def rounded(image: Image.Image, radius: int) -> Image.Image:
    mask = Image.new("L", image.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, image.width, image.height), radius, fill=255)
    out = Image.new("RGBA", image.size)
    out.paste(image.convert("RGBA"), mask=mask)
    return out


def wrap(draw: ImageDraw.ImageDraw, value: str, face: ImageFont.FreeTypeFont, width: int) -> list[str]:
    words = value.split()
    if not words:
        return []
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if draw.textlength(candidate, font=face) <= width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def draw_lines(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    y: int,
    face: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
    locale: str,
    spacing: int,
) -> int:
    direction = "rtl" if locale in RTL else "ltr"
    anchor = "ra" if locale in RTL else "la"
    x = 1170 if locale in RTL else 120
    for line in lines:
        draw.text((x, y), line, font=face, fill=fill, direction=direction, anchor=anchor)
        y += face.size + spacing
    return y


def make_card(slug: str, locale: str) -> Path:
    name, description = localized_copy(locale, slug)
    bg, accent, ink = PALETTES[slug]
    canvas = Image.new("RGB", (1290, 2796), bg)

    # A soft vertical tint gives the cards depth while preserving text contrast.
    tint = Image.new("RGBA", (1, canvas.height))
    px = tint.load()
    for y in range(canvas.height):
        px[0, y] = (*accent, round(58 * y / canvas.height))
    tint = tint.resize(canvas.size)
    canvas = Image.alpha_composite(canvas.convert("RGBA"), tint)
    draw = ImageDraw.Draw(canvas)

    label_face = font(50)
    body_face = font(76)
    draw.text(
        (1170 if locale in RTL else 120, 118),
        name,
        font=label_face,
        fill=accent,
        direction="rtl" if locale in RTL else "ltr",
        anchor="ra" if locale in RTL else "la",
    )

    # Prefer the first sentence: it stays punchy at card size and is fully localized.
    headline = re.split(r"(?<=[.!?。！？])\s+", description, maxsplit=1)[0]
    lines = wrap(draw, headline, body_face, 1050)
    while len(lines) > 5 and body_face.size > 54:
        body_face = font(body_face.size - 4)
        lines = wrap(draw, headline, body_face, 1050)
    text_bottom = draw_lines(draw, lines[:5], 220, body_face, ink, locale, 18)

    art = Image.open(ART[slug]).convert("RGBA")
    art_top = max(780, text_bottom + 70)
    art_h = 2796 - art_top - 90
    art_w = 1110
    if slug == "cari":
        prepared = fit_crop(art, (art_w, art_h), focus_x=0.52)
    elif slug in {"partypilot", "puzai"}:
        prepared = fit_crop(art, (art_w, art_h), focus_x=0.5)
    else:
        # Square/portrait hero art sits on a clean panel rather than being over-cropped.
        panel = Image.new("RGBA", (art_w, art_h), (0, 0, 0, 0))
        scale = min((art_w - 50) / art.width, (art_h - 50) / art.height)
        hero = art.resize((round(art.width * scale), round(art.height * scale)), Image.Resampling.LANCZOS)
        panel.alpha_composite(hero, ((art_w - hero.width) // 2, (art_h - hero.height) // 2))
        prepared = panel

    card = rounded(prepared, 58)
    shadow = Image.new("RGBA", canvas.size)
    shadow_block = Image.new("RGBA", (art_w, art_h), (0, 0, 0, 115))
    shadow_block = rounded(shadow_block, 58).filter(ImageFilter.GaussianBlur(30))
    shadow.alpha_composite(shadow_block, (90, art_top + 20))
    canvas = Image.alpha_composite(canvas, shadow)
    canvas.alpha_composite(card, (90, art_top))

    target = OUT / slug / f"{locale}.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(target, optimize=True)
    return target


def main() -> None:
    for slug in ART:
        for locale in SITE_LOCALES:
            path = make_card(slug, locale)
            print(f"{slug:14} {locale:8} -> {path}")


if __name__ == "__main__":
    main()
