#!/usr/bin/env python3
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
META = Path("/Users/rzopenclaw/Projects/Apps/Apple/FishDiscover/Store-Package/AppStore/metadata.md").read_text()
LANGS = ["en", "es", "fr", "de", "it", "ja", "pt", "zh-hans", "zh-hant", "nl", "ko", "ar", "ru", "cs", "da", "fi", "he", "hi", "id", "nb", "pl", "sv", "tr", "vi"]
META_LANG = {"zh-hans":"zh-Hans", "zh-hant":"zh-Hant"}
COMING = {
    "en":"Coming soon", "es":"Próximamente", "fr":"Bientôt disponible", "de":"Demnächst", "it":"Prossimamente",
    "ja":"近日公開", "pt":"Em breve", "zh-hans":"即将推出", "zh-hant":"即將推出", "nl":"Binnenkort",
    "ko":"출시 예정", "ar":"قريبًا", "ru":"Скоро", "cs":"Již brzy", "da":"Kommer snart", "fi":"Tulossa pian",
    "he":"בקרוב", "hi":"जल्द आ रहा है", "id":"Segera hadir", "nb":"Kommer snart", "pl":"Już wkrótce",
    "sv":"Kommer snart", "tr":"Çok yakında", "vi":"Sắp ra mắt"
}
LEAD = {
    "en":"Meet your next field guide", "es":"Conoce tu próxima guía de campo", "fr":"Découvrez votre prochain guide de terrain", "de":"Dein nächster Feldführer",
    "it":"La tua prossima guida da campo", "ja":"次のフィールドガイド", "pt":"Conheça o seu próximo guia de campo", "zh-hans":"认识你的下一本随身鱼类图鉴",
    "zh-hant":"認識你的下一本隨身魚類圖鑑", "nl":"Maak kennis met je volgende veldgids", "ko":"새로운 필드 가이드를 만나보세요", "ar":"تعرّف على دليلك الميداني القادم",
    "ru":"Ваш новый полевой справочник", "cs":"Poznejte svého nového terénního průvodce", "da":"Mød din næste feltguide", "fi":"Tutustu uuteen kenttäoppaaseesi",
    "he":"הכירו את מדריך השטח הבא שלכם", "hi":"अपनी अगली फील्ड गाइड से मिलें", "id":"Kenali panduan lapangan Anda berikutnya", "nb":"Møt din neste feltguide",
    "pl":"Poznaj swój nowy przewodnik terenowy", "sv":"Möt din nästa fältguide", "tr":"Yeni saha rehberinizle tanışın", "vi":"Gặp gỡ cẩm nang thực địa tiếp theo của bạn"
}

def metadata(lang):
    key = META_LANG.get(lang, lang)
    block = re.search(rf'^## {re.escape(key)} \([^\n]+\)\n(.*?)(?=^## |\Z)', META, re.M | re.S)
    if not block:
        raise RuntimeError(f"Missing metadata for {lang}")
    body = block.group(1)
    subtitle = re.search(r'- \*\*Subtitle\*\*: `([^`]+)`', body).group(1)
    promo = re.search(r'- \*\*Promotional Text\*\*: `([^`]+)`', body).group(1)
    return subtitle, promo

CSS = r'''
/* Fish Discover coming-soon spotlight */
.soonspot{padding:34px 0 18px}
.fishsoon{position:relative;min-height:540px;border-radius:32px;overflow:hidden;display:flex;align-items:flex-end;padding:clamp(26px,5vw,58px);color:#fff;background:#063d59 url('/assets/art/fishdiscover-hero.webp') center/cover no-repeat;box-shadow:0 26px 70px rgba(4,67,94,.28)}
.fishsoon::before{content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(1,26,43,.88) 0%,rgba(1,35,55,.68) 44%,rgba(1,30,48,.12) 76%),linear-gradient(0deg,rgba(1,24,39,.65),transparent 60%)}
.fishsoon-content{position:relative;z-index:1;max-width:610px}
.fishsoon-kicker{display:inline-flex;align-items:center;gap:9px;padding:8px 15px;border:1px solid rgba(255,255,255,.36);border-radius:999px;background:rgba(0,25,40,.34);backdrop-filter:blur(10px);font-size:12px;font-weight:800;letter-spacing:.16em;text-transform:uppercase}
.fishsoon-kicker::before{content:"";width:8px;height:8px;border-radius:50%;background:#70f0de;box-shadow:0 0 16px #70f0de}
.fishsoon-brand{display:flex;align-items:center;gap:16px;margin:22px 0 10px}.fishsoon-brand img{width:74px;height:74px;border-radius:19px;box-shadow:0 12px 28px rgba(0,0,0,.3)}
.fishsoon h2{font-size:clamp(38px,6vw,70px);line-height:1;color:#fff;text-shadow:0 3px 24px rgba(0,0,0,.35)}
.fishsoon .fishsub{font-family:Fraunces,serif;font-size:clamp(18px,2.4vw,25px);font-style:italic;color:#b9fff4;margin:0 0 12px}
.fishsoon .fishdesc{font-size:16px;line-height:1.7;color:rgba(255,255,255,.94);max-width:58ch}
.soonstores{display:flex;gap:10px;flex-wrap:wrap;margin-top:23px}.soonstore{display:inline-flex;align-items:center;gap:10px;padding:11px 15px;border:1px solid rgba(255,255,255,.3);border-radius:13px;background:rgba(0,24,39,.46);backdrop-filter:blur(10px);font-size:13px;font-weight:700}.soonstore svg{width:17px;height:17px;flex:none}
@media(max-width:680px){.fishsoon{min-height:610px;background-position:58% center;padding:24px}.fishsoon::before{background:linear-gradient(0deg,rgba(1,24,39,.94) 0%,rgba(1,30,48,.63) 67%,rgba(1,30,48,.06) 100%)}.fishsoon-brand img{width:62px;height:62px}.fishsoon .fishdesc{font-size:14.5px}}
'''

APPLE_SVG = '<svg viewBox="0 0 16 16" aria-hidden="true" fill="currentColor"><path d="M11.05 8.46c-.02-1.7 1.39-2.52 1.45-2.56-.79-1.16-2.02-1.31-2.46-1.33-1.05-.11-2.05.62-2.58.62-.53 0-1.35-.6-2.22-.59-1.14.02-2.2.66-2.79 1.69-1.19 2.07-.3 5.13.86 6.81.57.82 1.25 1.74 2.13 1.71.86-.04 1.18-.55 2.22-.55 1.03 0 1.33.55 2.23.53.92-.02 1.51-.84 2.07-1.66.65-.95.92-1.87.94-1.92-.02-.01-1.79-.69-1.81-2.74z"/><path d="M9.6 3.57c.47-.57.79-1.36.7-2.15-.68.03-1.5.45-1.99 1.02-.44.5-.82 1.31-.72 2.08.76.06 1.54-.39 2.01-.95z"/></svg>'
PLAY_SVG = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M1.8 1.3 9.6 8l-7.8 6.7z" fill="#34a853"/><path d="M11.9 5.7 9.6 8 1.8 1.3z" fill="#ea4335"/><path d="M11.9 10.3 1.8 14.7 9.6 8z" fill="#fbbc04"/><path d="m11.9 5.7 2.6 1.43c.5.29.5 1.45 0 1.74l-2.6 1.43L9.6 8z" fill="#4285f4"/></svg>'

for lang in LANGS:
    path = ROOT / ("index.html" if lang == "en" else f"{lang}/index.html")
    text = path.read_text()
    subtitle, promo = metadata(lang)
    section = f'''  <section class="soonspot" id="fishdiscover" aria-labelledby="fishdiscover-title">
    <div class="wrap"><div class="fishsoon">
      <div class="fishsoon-content">
        <span class="fishsoon-kicker">{html.escape(COMING[lang])}</span>
        <div class="fishsoon-brand"><img src="/assets/icons/fishdiscover.webp" width="74" height="74" alt=""><h2 id="fishdiscover-title">Fish Discover</h2></div>
        <p class="fishsub">{html.escape(LEAD[lang])} · {html.escape(subtitle)}</p>
        <p class="fishdesc">{html.escape(promo)}</p>
        <div class="soonstores" aria-label="{html.escape(COMING[lang])}"><span class="soonstore">{APPLE_SVG}{html.escape(COMING[lang])} · App Store</span><span class="soonstore">{PLAY_SVG}{html.escape(COMING[lang])} · Google Play</span></div>
      </div>
    </div></div>
  </section>
'''
    text = re.sub(r'\s*<section class="soonspot" id="fishdiscover".*?(?=\s*<section class="section" id="play")', '\n', text, flags=re.S)
    play_match = re.search(r'\s*<section class="section" id="play"', text)
    if not play_match:
        raise RuntimeError(f"Play section marker missing: {path}")
    text = text[:play_match.start()] + '\n' + section + '    <section class="section" id="play"' + text[play_match.end():]
    if '/* Fish Discover coming-soon spotlight */' not in text:
        text = text.replace('/* promise */', CSS + '\n/* promise */', 1)
    structured = {"@context":"https://schema.org","@type":"MobileApplication","name":"Fish Discover","description":promo,"operatingSystem":"iOS, iPadOS, macOS, Android","applicationCategory":"https://schema.org/EducationalApplication","url":f"https://www.rizkcorsight.com/{'' if lang == 'en' else lang + '/'}#fishdiscover","image":"https://www.rizkcorsight.com/assets/art/fishdiscover-hero.webp","thumbnailUrl":"https://www.rizkcorsight.com/assets/icons/fishdiscover.webp","inLanguage":lang,"publisher":{"@id":"https://www.rizkcorsight.com/#organization"},"offers":{"@type":"Offer","availability":"https://schema.org/PreOrder","price":"0","priceCurrency":"USD"},"releaseNotes":COMING[lang]}
    script = '<script type="application/ld+json" data-app="fishdiscover">' + json.dumps(structured, ensure_ascii=False, separators=(",", ":")) + '</script>'
    text = re.sub(r'\s*<script type="application/ld\+json" data-app="fishdiscover">.*?</script>\s*', '\n', text, flags=re.S)
    text = text.replace('</head>', script + '\n</head>', 1)
    path.write_text(text)

llms = ROOT / "llms.txt"
text = llms.read_text()
if "Fish Discover — Coming soon" not in text:
    text = text.replace("## Stores", "- Fish Discover — Coming soon on Apple and Android. Private, offline fish identification from a photo, with clear field marks that help people learn why a species matches. [Preview: https://www.rizkcorsight.com/#fishdiscover]\n\n## Stores")
llms.write_text(text)
