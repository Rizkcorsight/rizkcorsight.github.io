#!/usr/bin/env python3
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANGS = ["en", "es", "fr", "de", "it", "ja", "pt", "zh-hans", "zh-hant", "nl", "ko", "ar", "ru", "cs", "da", "fi", "he", "hi", "id", "nb", "pl", "sv", "tr", "vi"]

COPY = {
    "en": (("Read old records & wills", "Train your eye to read historic handwriting with guided letterforms, real manuscript practice, and private on-device study tools."), ("Daily paper-folding puzzle", "Fold a sheet along the clues, predict the punched pattern, and sharpen spatial reasoning in a calm daily puzzle.")),
    "es": (("Lee registros y testamentos antiguos", "Entrena tu vista para leer escritura histórica con formas de letras guiadas, manuscritos reales y estudio privado en el dispositivo."), ("Rompecabezas diario de plegado", "Dobla una hoja siguiendo las pistas, predice el patrón perforado y mejora tu razonamiento espacial con un reto diario tranquilo.")),
    "fr": (("Lisez anciens actes et testaments", "Entraînez votre œil à lire les écritures anciennes grâce aux formes guidées, aux vrais manuscrits et à une étude privée sur l’appareil."), ("Puzzle quotidien de pliage", "Pliez une feuille selon les indices, anticipez le motif perforé et développez votre vision spatiale avec un puzzle quotidien apaisant.")),
    "de": (("Alte Akten und Testamente lesen", "Trainiere historische Handschriften mit geführten Buchstabenformen, echten Manuskripten und privaten Übungen direkt auf deinem Gerät."), ("Tägliches Papierfalt-Rätsel", "Falte ein Blatt nach den Hinweisen, sage das Lochmuster voraus und trainiere räumliches Denken mit einem ruhigen Tagesrätsel.")),
    "it": (("Leggi registri e testamenti antichi", "Allena l’occhio a leggere grafie storiche con lettere guidate, veri manoscritti e strumenti di studio privati sul dispositivo."), ("Puzzle quotidiano di piegatura", "Piega un foglio seguendo gli indizi, prevedi il motivo dei fori e allena il ragionamento spaziale con un puzzle quotidiano rilassante.")),
    "ja": (("古い記録や遺言書を読む", "字形ガイドと実物の写本、端末内で完結する学習ツールで、歴史的な手書き文字を読む力を鍛えます。"), ("毎日の紙折りパズル", "手掛かりに沿って紙を折り、穴の模様を予測。落ち着いたデイリーパズルで空間認識力を磨けます。")),
    "pt": (("Leia registos e testamentos antigos", "Treine a leitura de caligrafia histórica com letras guiadas, manuscritos reais e ferramentas privadas no dispositivo."), ("Puzzle diário de dobragem", "Dobre uma folha seguindo as pistas, preveja o padrão perfurado e desenvolva o raciocínio espacial num puzzle diário tranquilo.")),
    "zh-hans": (("阅读古老档案与遗嘱", "通过字形指导、真实手稿练习和设备端私密学习工具，训练阅读历史手写文字的能力。"), ("每日折纸谜题", "根据线索折叠纸张，预测打孔图案，在轻松的每日谜题中锻炼空间推理能力。")),
    "zh-hant": (("閱讀古老檔案與遺囑", "透過字形指引、真實手稿練習與裝置端私密學習工具，訓練閱讀歷史手寫文字的能力。"), ("每日摺紙謎題", "依照線索摺疊紙張，預測打孔圖案，在平靜的每日謎題中鍛鍊空間推理能力。")),
    "nl": (("Lees oude akten en testamenten", "Train je oog voor historisch handschrift met begeleide lettervormen, echte manuscripten en privé-oefeningen op je apparaat."), ("Dagelijkse papiervouwpuzzel", "Vouw een vel volgens de aanwijzingen, voorspel het gatenpatroon en train je ruimtelijk inzicht met een rustige dagelijkse puzzel.")),
    "ko": (("옛 기록과 유언장 읽기", "글자 모양 안내와 실제 필사본 연습, 기기 내 비공개 학습 도구로 옛 손글씨를 읽는 눈을 키워 보세요."), ("매일 종이접기 퍼즐", "단서에 따라 종이를 접고 구멍 무늬를 예측하며 차분한 데일리 퍼즐로 공간 추론력을 길러 보세요.")),
    "ar": (("اقرأ السجلات والوصايا القديمة", "درّب عينك على قراءة الخطوط التاريخية بأشكال حروف موجهة ومخطوطات حقيقية وأدوات دراسة خاصة على الجهاز."), ("لغز يومي لطي الورق", "اطوِ ورقة وفق الأدلة وتوقّع نمط الثقوب وطوّر التفكير المكاني في لغز يومي هادئ.")),
    "ru": (("Читайте старые записи и завещания", "Учитесь читать исторический почерк по формам букв и настоящим рукописям с приватными упражнениями на устройстве."), ("Ежедневная головоломка со сгибами", "Складывайте лист по подсказкам, предсказывайте узор отверстий и развивайте пространственное мышление каждый день.")),
    "cs": (("Čtěte staré záznamy a závěti", "Trénujte čtení historického rukopisu s vedenými tvary písmen, skutečnými rukopisy a soukromým studiem v zařízení."), ("Denní skládačka papíru", "Složte list podle vodítek, předpovězte děrovaný vzor a procvičujte prostorové myšlení v klidné denní hádance.")),
    "da": (("Læs gamle arkiver og testamenter", "Træn historisk håndskrift med guidede bogstavformer, ægte manuskripter og privat øvelse direkte på enheden."), ("Daglig papirfoldningsgåde", "Fold et ark efter ledetrådene, forudsig hulmønsteret, og træn rumlig tænkning med en rolig daglig gåde.")),
    "fi": (("Lue vanhoja asiakirjoja ja testamentteja", "Harjoittele historiallista käsialaa ohjatuilla kirjainmuodoilla, aidoilla käsikirjoituksilla ja laitteen yksityisillä työkaluilla."), ("Päivittäinen paperintaittopulma", "Taita arkki vihjeiden mukaan, ennusta reikien kuvio ja kehitä avaruudellista päättelyä rauhallisessa päivittäispulmassa.")),
    "he": (("קוראים רשומות וצוואות ישנות", "אמנו את העין לקריאת כתב יד היסטורי בעזרת צורות אותיות מודרכות, כתבי יד אמיתיים ולימוד פרטי במכשיר."), ("חידת קיפול נייר יומית", "קפלו דף לפי הרמזים, חזו את תבנית החורים ושפרו חשיבה מרחבית בחידה יומית רגועה.")),
    "hi": (("पुराने अभिलेख और वसीयतें पढ़ें", "निर्देशित अक्षर रूपों, वास्तविक पांडुलिपियों और डिवाइस पर निजी अभ्यास से ऐतिहासिक लिखावट पढ़ना सीखें।"), ("रोज़ की कागज़ मोड़ पहेली", "संकेतों के अनुसार कागज़ मोड़ें, छेदों का पैटर्न पहचानें और शांत दैनिक पहेली से स्थानिक सोच निखारें।")),
    "id": (("Baca arsip dan surat wasiat lama", "Latih mata membaca tulisan tangan bersejarah dengan bentuk huruf terpandu, manuskrip nyata, dan latihan privat di perangkat."), ("Teka-teki lipat kertas harian", "Lipat kertas mengikuti petunjuk, tebak pola lubangnya, dan asah penalaran spasial lewat teka-teki harian yang tenang.")),
    "nb": (("Les gamle arkiver og testamenter", "Tren på historisk håndskrift med veiledede bokstavformer, ekte manuskripter og privat øving direkte på enheten."), ("Daglig papirbrettingspuslespill", "Brett et ark etter ledetrådene, forutsi hullmønsteret og tren romforståelsen med et rolig daglig puslespill.")),
    "pl": (("Czytaj stare akta i testamenty", "Ćwicz czytanie historycznego pisma dzięki prowadzonym kształtom liter, prawdziwym rękopisom i prywatnej nauce na urządzeniu."), ("Codzienna łamigłówka z papierem", "Składaj kartkę według wskazówek, przewiduj wzór otworów i ćwicz wyobraźnię przestrzenną w spokojnej codziennej łamigłówce.")),
    "sv": (("Läs gamla dokument och testamenten", "Träna historisk handstil med guidade bokstavsformer, riktiga manuskript och privat övning direkt på enheten."), ("Dagligt pappersvikningspussel", "Vik ett ark efter ledtrådarna, förutse hålmönstret och träna rumsuppfattningen med ett lugnt dagligt pussel.")),
    "tr": (("Eski kayıtları ve vasiyetleri okuyun", "Yönlendirmeli harf biçimleri, gerçek el yazmaları ve cihazda özel çalışma araçlarıyla tarihî el yazılarını okumayı öğrenin."), ("Günlük kâğıt katlama bulmacası", "İpuçlarına göre kâğıdı katlayın, delik desenini tahmin edin ve sakin bir günlük bulmacayla uzamsal düşünmeyi geliştirin.")),
    "vi": (("Đọc hồ sơ và di chúc cổ", "Rèn luyện cách đọc chữ viết tay lịch sử bằng mẫu chữ hướng dẫn, bản thảo thật và công cụ học riêng tư trên thiết bị."), ("Câu đố gấp giấy hằng ngày", "Gấp tờ giấy theo gợi ý, dự đoán mẫu lỗ và luyện tư duy không gian qua một câu đố nhẹ nhàng mỗi ngày.")),
}

APPLE = "https://apps.apple.com/us/app/handrift-old-handwriting/id6787851462"
FOLDCAST_APPLE = "https://apps.apple.com/us/app/foldcast-paper-folding-game/id6787431868"
GOOGLE = "https://play.google.com/store/apps/details?id=com.rizkcorsight.foldcast"

def app_item(position, name, desc, os_name, category, url, same_as, slug, image, icon, language):
    return {"@type":"ListItem","position":position,"item":{"@type":"MobileApplication","name":name,"description":desc,"operatingSystem":os_name,"applicationCategory":f"https://schema.org/{category}","offers":{"@type":"Offer","price":"0","priceCurrency":"USD"},"publisher":{"@id":"https://www.rizkcorsight.com/#organization"},"url":url,"sameAs":same_as,"@id":f"https://www.rizkcorsight.com/#{slug}","inLanguage":language,"image":f"https://www.rizkcorsight.com/assets/screens/{image}","thumbnailUrl":f"https://www.rizkcorsight.com/assets/icons/{icon}"}}

def badge(template, href):
    return re.sub(r'href="[^"]+"', f'href="{href}"', template, count=1)

for lang in LANGS:
    path = ROOT / ("index.html" if lang == "en" else f"{lang}/index.html")
    text = path.read_text()
    text = text.replace("https://rizkcorsight.github.io", "https://www.rizkcorsight.com")
    hand, fold = COPY[lang]

    scripts = list(re.finditer(r'<script type="application/ld\+json">(.*?)</script>', text, re.S))
    item_match = next(m for m in scripts if '"@type":"ItemList"' in m.group(1))
    data = json.loads(item_match.group(1))
    data["itemListElement"] = [x for x in data["itemListElement"] if x["item"].get("@id", "").split("#")[-1] not in {"handrift", "foldcast"}]
    data["itemListElement"].append(app_item(21, "Handrift: Old Handwriting", hand[1], "iOS, iPadOS, macOS", "EducationalApplication", APPLE, [APPLE], "handrift", "handrift-1.webp", "handrift.webp", lang))
    data["itemListElement"].append(app_item(22, "Foldcast", fold[1], "iOS, iPadOS, Android", "GameApplication", FOLDCAST_APPLE, [FOLDCAST_APPLE, GOOGLE], "foldcast", "foldcast-1.webp", "foldcast.webp", lang))
    data["numberOfItems"] = 22
    replacement = '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + '</script>'
    text = text[:item_match.start()] + replacement + text[item_match.end():]

    app_badge_match = re.search(r'<a class="badge appstore".*?</a>', text, re.S)
    play_badge_match = re.search(r'<a class="badge gplay".*?</a>', text, re.S)
    if not app_badge_match or not play_badge_match:
        raise RuntimeError(f"Badges not found in {path}")
    app_badge = badge(app_badge_match.group(0), APPLE)
    foldcast_app_badge = badge(app_badge_match.group(0), FOLDCAST_APPLE)
    play_badge = badge(play_badge_match.group(0), GOOGLE)
    open_label = {"es":"Abrir", "fr":"Ouvrir", "de":"Öffne", "it":"Apri", "ja":"ストアで開く", "pt":"Abrir", "zh-hans":"在商店中打开", "zh-hant":"在商店中開啟", "nl":"Open", "ko":"스토어에서 열기", "ar":"فتح", "ru":"Открыть", "cs":"Otevřít", "da":"Åbn", "fi":"Avaa", "he":"פתיחה", "hi":"खोलें", "id":"Buka", "nb":"Åpne", "pl":"Otwórz", "sv":"Öppna", "tr":"Aç", "vi":"Mở"}.get(lang, "Open")
    hand_card = f'''      <article class="card reveal" id="handrift" style="--g1:#b14dff;--g2:#ff5bc0">
        <div class="shotwrap"><a class="shot" href="{APPLE}" target="_blank" rel="noopener" aria-label="{html.escape(open_label)} Handrift"><img loading="lazy" src="/assets/screens/handrift-1.webp" width="300" height="450" alt="Handrift"></a></div>
        <div class="meta"><img class="icon" loading="lazy" src="/assets/icons/handrift.webp" width="54" height="54" alt=""><div><h3>Handrift: Old Handwriting</h3><p class="sub">{html.escape(hand[0])}</p></div></div>
        <p class="desc">{html.escape(hand[1])}</p><div class="badges">{app_badge}</div>
      </article>
'''
    fold_card = f'''      <article class="card reveal" id="foldcast" style="--g1:#b14dff;--g2:#ff5bc0">
        <div class="shotwrap"><a class="shot" href="{FOLDCAST_APPLE}" target="_blank" rel="noopener" aria-label="{html.escape(open_label)} Foldcast"><img loading="lazy" src="/assets/screens/foldcast-1.webp" width="300" height="495" alt="Foldcast"></a></div>
        <div class="meta"><img class="icon" loading="lazy" src="/assets/icons/foldcast.webp" width="54" height="54" alt=""><div><h3>Foldcast</h3><p class="sub">{html.escape(fold[0])}</p></div></div>
        <p class="desc">{html.escape(fold[1])}</p><div class="badges">{foldcast_app_badge}{play_badge}</div>
      </article>
'''
    text = re.sub(r'\s*<article class="card reveal" id="handrift".*?</article>\s*', '\n      ', text, flags=re.S)
    text = re.sub(r'\s*<article class="card reveal" id="foldcast".*?</article>\s*', '\n      ', text, flags=re.S)
    marker = '      <article class="card reveal" id="cue"'
    if marker not in text:
        raise RuntimeError(f"Cue marker not found in {path}")
    text = text.replace(marker, hand_card + fold_card + marker, 1)
    text = re.sub(r'<img loading="lazy" src="/assets/icons/(?:handrift|foldcast)\.webp" width="58" height="58" alt="">', '', text)
    text = text.replace('</div>\n      <p class="statline">', '<img loading="lazy" src="/assets/icons/handrift.webp" width="58" height="58" alt=""><img loading="lazy" src="/assets/icons/foldcast.webp" width="58" height="58" alt=""></div>\n      <p class="statline">', 1)

    def update_counts(match):
        counts = iter((22, 22, 21))
        return re.sub(r'<b>(.*?)</b>', lambda b: '<b>' + re.sub(r'\d+', str(next(counts)), b.group(1), count=1) + '</b>', match.group(0))

    text = re.sub(r'<p class="statline">.*?</p>', update_counts, text, count=1)
    path.write_text(text)

for rel in ["robots.txt", "sitemap.xml", "llms.txt", "_config.yml"]:
    path = ROOT / rel
    if path.exists():
        path.write_text(path.read_text().replace("https://rizkcorsight.github.io", "https://www.rizkcorsight.com"))

llms = ROOT / "llms.txt"
text = llms.read_text()
foldcast_line = "- Foldcast — Daily paper-folding puzzle. Fold a sheet along the clues, predict the punched pattern, and sharpen spatial reasoning in a calm daily puzzle. [App Store: " + FOLDCAST_APPLE + "] [Google Play: " + GOOGLE + "]"
text = re.sub(r'^- Foldcast —.*$', foldcast_line, text, flags=re.M)
llms.write_text(text)
