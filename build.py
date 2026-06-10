#!/usr/bin/env python3
"""
Siber Güvenlik Fon Takip — haftalık pano üreticisi.

Ne yapar:
  1. Claude API'yi web aramasıyla çağırır; AB / Almanya / NRW / dünya
     kaynaklarında siber güvenlik, veri koruma, GRC, NIS2, AI Act, GDPR,
     awareness vb. alanlarda fon/proje fırsatlarını bulur.
  2. Yalnızca bireysel / firma-KOBİ / dernek-vakıf / üniversite başvurabilenleri
     tutar; kamu-only olanları publicOnly:true işaretler.
  3. Her projeye özet (Frist, kim, bütçe, şartlar, nasıl, ipucu) üretir.
  4. dashboard_template.html içindeki DATA, SUM ve TODAY bloklarını günceller,
     index.html olarak yazar.
  5. (Workflow tarafında) repoya commit edilir, Pages yayınlar, e-posta gönderilir.

Gerekli ortam değişkeni: ANTHROPIC_API_KEY
"""

import os
import re
import json
import sys
import urllib.request
import urllib.error
from urllib.parse import quote
from datetime import date

import anthropic

MODEL = "claude-sonnet-4-6"          # gerekirse claude-opus-4-6 yapabilirsiniz
TEMPLATE = "dashboard_template.html"
OUTPUT = "index.html"
TODAY = date.today().isoformat()

PROMPT = f"""Bugünün tarihi: {TODAY}.

Sen Dr. Sait için bir fon/proje izleme asistanısın. Aşağıdaki alanlarda AB,
Almanya, NRW ve dünya çapında GÜNCEL ve YAKLAŞAN fon çağrıları, startup
destekleri, eğitim/awareness ve GRC/uyum projelerini web aramasıyla bul:

- AB fonları: Horizon Europe (Cluster 3 / ECCC cybersecurity), Digital Europe
  Programme (DIGITAL/CYBER), EIC Accelerator, EIT Digital, ESF+, Interreg NWE,
  cascade funding / FSTP
- Almanya & NRW: Förderdatenbank des Bundes (BMWK — foerderdatenbank.de, tüm
  federal/eyalet/AB programlarının resmi veritabanı, MUTLAKA kaynak olarak kullan),
  BMBF/BMFTR IT-Sicherheit, BSI (KoPa45), Cyberagentur, Gründungsstipendium.NRW,
  NRW.Bank programları, EDIH, EXIST, ZIM, Invest-BW
- Startup: cybersecurity akseleratör/inkübatör/yarışma
- Eğitim & awareness: EU Cybersecurity Skills Academy, awareness training, pentest,
  DAAD (akademik işbirliği/değişim)
- GRC, AI Act & Uyum: NIS2, DORA, GDPR, EU AI Act, GRC automation, security risk
- Kommunal / Belediye: belediyelere (Kommunen) ve personeline yönelik siber
  güvenlik/eğitim destekleri ve İHALELER. Yayın yerleri: Smart Cities Modellprojekte
  (BMWSB/KfW-436), BSI Allianz für Cybersicherheit, NRW digital-sicher.nrw / NRW.BANK,
  eyalet İçişleri bakanlıkları (IM NRW), ve kamu ihale portalları (service.bund.de,
  Vergabe.NRW, TED). Hizmet sağlayıcının (firma) katılabileceği fırsatları öne çıkar.
- Kredi / Finansman: startup/KOBİ için UYGUN KOŞULLU krediler — düşük faiz, geri
  ödemesiz (tilgungsfrei) yıllar, uzun vade. KfW (ERP-Gründerkredit StartGeld 067,
  ERP-Kapital 058, ERP-Förderkredit Digitalisierung/Innovation 511/512), NRW.BANK
  (NRW/EU.Mikrodarlehen, NRW.BANK.Gründung und Wachstum). Yeni çıkan ya da koşulları
  iyileşen (limit artışı, faiz indirimi, daha uzun tilgungsfrei) kredileri de yakala.
- Uluslararası: World Bank, OECD (genelde kamu-only)

BAŞVURU HAKKI: Sadece bireysel / firma-KOBİ / dernek-vakıf / üniversite-araştırma
başvurabilenleri öne çıkar. Yalnızca kamu kurumlarının başvurabildiklerini
publicOnly=true işaretle (silme, işaretle).

ÇIKTI BİÇİMİ: SADECE geçerli JSON döndür, başka metin yok. Şu şemada:

{{
  "data": [
    {{
      "title": "Kısa benzersiz başlık",
      "org": "Yürüten kurum",
      "cat": "AB fon çağrısı | Startup desteği | Almanya & NRW desteği | Eğitim & araştırma | GRC, AI Act & Uyum | Kommunal / Belediye | Kredi / Finansman | Uluslararası fon (WB/OECD)",
      "region": "AB | Almanya | NRW | Dünya | Dünya / UK | Dünya / CH | AB / Almanya",
      "budget": "ör. ≈ €50 milyon / %75 eş finansman",
      "deadline": "YYYY-MM-DD veya rolling",
      "elig": ["Firma/KOBİ","Üniversite/Araştırma","Dernek/Vakıf","Birey (startup kurucu)"],
      "publicOnly": false,
      "desc": "1-2 cümle açıklama",
      "url": "resmi sayfa linki"
    }}
  ],
  "sum": {{
    "Kısa benzersiz başlık": {{
      "frist": "son tarih/Frist detayı (aşama bilgisi varsa ekle)",
      "kimler": "kim başvurabilir detayı",
      "butce": "toplam bütçe ve hibe miktarı",
      "es_finansman": "eş finansman/öz kaynak oranı (ör. %75 hibe, %25 öz kaynak) — yoksa boş",
      "basari_orani": "tahmini başarı oranı / rekabet seviyesi (ör. Horizon ~%15, EIC <%10) — biliniyorsa",
      "konsorsiyum": "konsorsiyum/ortaklık şartı (ör. min 3 ülke/3 kurum) — varsa, yoksa 'Tekil başvuru mümkün'",
      "hazirlik": "ne kadar erken başlamalı + başvuru yükü (ağır/orta/hafif)",
      "sartlar": ["kısa şart 1","kısa şart 2","kısa şart 3"],
      "belgeler": ["gerekli belge/ek 1","belge 2"],
      "kriterler": "neye göre değerlendirilir (ör. Excellence/Impact/Implementation)",
      "nasil": "nasıl/nereden başvurulur",
      "kaynaklar": "yardım kaynakları: NCP/ulusal irtibat, webinar, FAQ, partner-arama (varsa link/isim)",
      "ipucu": "pratik ipucu"
    }}
  }}
}}

KURALLAR:
- 18-26 fırsat hedefle; köklü programları (Horizon, DIGITAL, EIC, BMBF, NRW,
  Skills Academy, EXIST, ZIM, EIT Digital, ESF+, Interreg NWE, DAAD, World Bank,
  OECD) her zaman dahil et, varsa yenileri ekle.
- "sum" içindeki her anahtar "data" içindeki bir "title" ile birebir aynı olmalı.
- "sartlar" ve "belgeler" en fazla 4 KISA madde; tüm metinler kısa ve öz olsun.
- Yeni sum alanlarını (es_finansman, basari_orani, konsorsiyum, hazirlik, belgeler,
  kriterler, kaynaklar) uygun olduğunda doldur; bilgi yoksa o alanı boş string ya da
  boş dizi bırak (uydurma yapma).
- Tarih ve başvuru hakkını resmi kaynaktan doğrula; eminsizsen desc'e
  "teyit edilmeli" yaz.
- Tüm metin Türkçe.
- ÇOK ÖNEMLİ: Yanıtın TAMAMI tek bir geçerli JSON nesnesi olmalı. JSON'dan önce
  veya sonra HİÇBİR açıklama/metin yazma. JSON'ı eksiksiz kapat (tüm parantezler
  dengeli). String içinde satır başı kullanma.
- String DEĞERLERİNİN İÇİNDE çift tırnak (") KULLANMA. Vurgu/alıntı gerekiyorsa
  tek tırnak (') veya köşeli/eğik tırnak kullan. Aksi halde JSON bozulur.
"""


def get_opportunities() -> dict:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    # Büyük max_tokens + web arama uzun sürebildiği için streaming şart.
    with client.messages.stream(
        model=MODEL,
        max_tokens=32000,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 12}],
        messages=[{"role": "user", "content": PROMPT}],
    ) as stream:
        final = stream.get_final_message()
    # Web arama tool'u birden çok metin bloğu döndürebilir; hepsini birleştir.
    text = "".join(b.text for b in final.content if getattr(b, "type", "") == "text")
    try:
        return extract_json(text)
    except (ValueError, json.JSONDecodeError):
        # Metin JSON'ı bozuksa: zorunlu araç şemasıyla garantili geçerli JSON al.
        return coerce_json(client, text)


def coerce_json(client, raw_text: str) -> dict:
    """Bozuk JSON metnini, zorunlu araç (tool) şemasıyla geçerli JSON'a çevirir."""
    tool = {
        "name": "submit_data",
        "description": "Fon verisini yapılandırılmış JSON olarak gönder.",
        "input_schema": {
            "type": "object",
            "properties": {
                "data": {"type": "array", "items": {"type": "object"}},
                "sum": {"type": "object"},
            },
            "required": ["data", "sum"],
        },
    }
    with client.messages.stream(
        model=MODEL,
        max_tokens=32000,
        tools=[tool],
        tool_choice={"type": "tool", "name": "submit_data"},
        messages=[{
            "role": "user",
            "content": (
                "Aşağıdaki içeriği AYNEN koruyarak submit_data aracına geçerli JSON "
                "olarak gönder. Hiçbir bilgiyi değiştirme veya silme; yalnızca geçerli "
                "JSON haline getir.\n\n" + raw_text
            ),
        }],
    ) as stream:
        final = stream.get_final_message()
    for b in final.content:
        if getattr(b, "type", "") == "tool_use":
            return b.input
    raise ValueError("coerce_json: araç çıktısı bulunamadı.")


def _clean(s: str) -> str:
    # Sondaki gereksiz virgülleri kaldır:  ,}  ,]  ->  }  ]
    return re.sub(r",(\s*[}\]])", r"\1", s)


def _repair_truncated(s: str) -> str:
    """Yarıda kesilmiş JSON'ı en yakın geçerli yapıya kapatmaya çalışır."""
    stack, in_str, esc = [], False, False
    for ch in s:
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch in "{[":
                stack.append("}" if ch == "{" else "]")
            elif ch in "}]" and stack:
                stack.pop()
    out = s
    if in_str:              # açık string'i kapat
        out += '"'
    out = re.sub(r",\s*$", "", out.rstrip())   # sondaki yarım virgül
    out += "".join(reversed(stack))            # açık parantezleri kapat
    return out


def extract_json(text: str) -> dict:
    """Model çıktısından JSON nesnesini güvenle ayıkla (kesilmeye dayanıklı)."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    start = text.find("{")
    if start == -1:
        raise ValueError("Modelden JSON alınamadı:\n" + text[:800])
    text = text[start:]
    end = text.rfind("}")
    candidate = text[: end + 1] if end != -1 else text

    for attempt in (candidate, _clean(candidate), _clean(_repair_truncated(text))):
        try:
            return json.loads(attempt)
        except json.JSONDecodeError:
            continue
    # Hepsi başarısızsa hata ayıklama için kuyruğu göster
    raise ValueError(
        "JSON ayrıştırılamadı. Çıktının sonu:\n" + candidate[-800:]
    )


def js_array(data: list) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def js_object(sum_obj: dict) -> str:
    return json.dumps(sum_obj, ensure_ascii=False, indent=2)


def _alive(url: str) -> bool:
    """URL canlı mı? Önce HEAD, gerekirse GET ile dener."""
    if not url or not url.startswith("http"):
        return False
    ua = {"User-Agent": "Mozilla/5.0 (compatible; SiberFonLinkCheck/1.0)"}
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, method=method, headers=ua)
            with urllib.request.urlopen(req, timeout=12) as r:
                return r.status < 400
        except urllib.error.HTTPError as e:
            if method == "HEAD" and e.code in (400, 403, 405, 406):
                continue  # bazı sunucu HEAD'i reddeder; GET dene
            return False
        except Exception:
            if method == "HEAD":
                continue
            return False
    return False


def _fallback_url(item: dict) -> str:
    reg = (item.get("region") or "").lower()
    if "ab" in reg or "eu" in reg or "avrupa" in reg:
        return ("https://ec.europa.eu/info/funding-tenders/opportunities/portal/"
                "screen/opportunities/calls-for-proposals")
    if "alman" in reg or "nrw" in reg:
        return "https://www.foerderdatenbank.de/FDB/DE/Foerderprogramme/foerderprogramme.html"
    return "https://www.google.com/search?q=" + quote((item.get("title", "") + " funding call"))


def validate_links(payload: dict) -> dict:
    """Her fonun linkini tek tek kontrol et; bozuk olanı resmi arama sayfasıyla değiştir."""
    fixed = 0
    for it in payload.get("data", []):
        if not _alive(it.get("url", "")):
            it["url"] = _fallback_url(it)
            d = it.get("desc", "")
            if "doğrulanamadı" not in d:
                it["desc"] = (d + " (Link otomatik doğrulanamadı; resmi arama "
                              "sayfasına yönlendirildi — güncel çağrıyı orada arayın.)").strip()
            fixed += 1
    print(f"Link kontrolü: {len(payload.get('data', []))} link tarandı, {fixed} tanesi düzeltildi.")
    return payload


def build_html(payload: dict) -> str:
    with open(TEMPLATE, encoding="utf-8") as f:
        html = f.read()

    # const TODAY = new Date('....');
    html = re.sub(
        r"const TODAY = new Date\('[^']*'\);",
        f"const TODAY = new Date('{TODAY}');",
        html, count=1,
    )
    # const DATA = [ ... ];
    html = re.sub(
        r"const DATA = \[.*?\];",
        "const DATA = " + js_array(payload["data"]) + ";",
        html, count=1, flags=re.DOTALL,
    )
    # const SUM = { ... };
    html = re.sub(
        r"const SUM = \{.*?\};",
        "const SUM = " + js_object(payload["sum"]) + ";",
        html, count=1, flags=re.DOTALL,
    )
    return html


def _days_left(dl):
    if not dl or dl == "rolling":
        return None
    try:
        return (date.fromisoformat(dl) - date.today()).days
    except Exception:
        return None


def read_old_titles():
    """Önceki index.html'deki başlıkları oku (bu hafta 'yeni' olanları bulmak için)."""
    if not os.path.exists(OUTPUT):
        return set()
    try:
        old = open(OUTPUT, encoding="utf-8").read()
        m = re.search(r"const DATA = (\[.*?\]);", old, re.DOTALL)
        if m:
            return {d.get("title") for d in json.loads(m.group(1))}
    except Exception:
        pass
    return set()


def generate_email(payload, old_titles):
    """Haftalık e-posta gövdesini (email_body.html) üretir: yeni eklenenler + krediler + yaklaşanlar."""
    today = date.today().strftime("%d.%m.%Y")
    data = payload["data"]
    new_items = [d for d in data if d.get("title") not in old_titles]
    soon = [d for d in data if (n := _days_left(d.get("deadline"))) is not None and 0 <= n <= 45]
    loans_new = [d for d in new_items if d.get("cat") == "Kredi / Finansman"]

    def li(d):
        return (f'<li><b>{d.get("title","")}</b> — {d.get("budget","")} · '
                f'son tarih: {d.get("deadline","")} · '
                f'<a href="{d.get("url","")}">resmi sayfa</a></li>')

    p = [f"<h2>🛡️ Siber Güvenlik &amp; Fon — Haftalık Güncelleme ({today})</h2>",
         '<p>Canlı pano: <a href="https://drsaityalazay.github.io/siber-fon-takip/">Aç →</a></p>']
    p.append("<h3>🆕 Bu hafta eklenenler</h3>" +
             ("<ul>" + "".join(li(d) for d in new_items) + "</ul>" if new_items
              else "<p>Bu hafta yeni fırsat eklenmedi.</p>"))
    if loans_new:
        p.append("<h3>💶 Yeni / Güncel Krediler</h3><ul>" + "".join(li(d) for d in loans_new) + "</ul>")
    if soon:
        p.append("<h3>⏰ 45 gün içinde kapananlar</h3><ul>" + "".join(li(d) for d in soon) + "</ul>")
    p.append('<p style="color:#888;font-size:12px">Otomatik gönderildi. Linkler her hafta doğrulanır; '
             'bağlayıcı şartlar resmi çağrı dokümanındadır.</p>')
    with open("email_body.html", "w", encoding="utf-8") as f:
        f.write("".join(p))
    print(f"E-posta gövdesi: {len(new_items)} yeni, {len(loans_new)} yeni kredi, {len(soon)} yaklaşan.")


def main():
    payload = get_opportunities()
    if "data" not in payload or "sum" not in payload:
        print("HATA: beklenen 'data'/'sum' alanları yok.", file=sys.stderr)
        sys.exit(1)
    old_titles = read_old_titles()        # önce eski başlıkları al
    payload = validate_links(payload)     # her linki tek tek kontrol et, bozukları düzelt
    html = build_html(payload)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)
    generate_email(payload, old_titles)   # haftalık e-posta gövdesini üret
    print(f"OK: {OUTPUT} güncellendi — {len(payload['data'])} fırsat ({TODAY}).")


if __name__ == "__main__":
    main()
