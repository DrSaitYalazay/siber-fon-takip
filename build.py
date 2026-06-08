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
  Programme (DIGITAL/CYBER), EIC Accelerator, cascade funding / FSTP
- Almanya & NRW: BMBF/BMFTR IT-Sicherheit, BSI (KoPa45), Cyberagentur,
  Gründungsstipendium.NRW, NRW.Bank, EDIH
- Startup: cybersecurity akseleratör/inkübatör/yarışma
- Eğitim & awareness: EU Cybersecurity Skills Academy, awareness training, pentest
- GRC, AI Act & Uyum: NIS2, DORA, GDPR, EU AI Act, GRC automation, security risk
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
      "cat": "AB fon çağrısı | Startup desteği | Almanya & NRW desteği | Eğitim & araştırma | GRC, AI Act & Uyum | Uluslararası fon (WB/OECD)",
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
      "frist": "son tarih/Frist detayı",
      "kimler": "kim başvurabilir detayı",
      "butce": "bütçe ve eş finansman oranı",
      "sartlar": ["şart 1","şart 2","şart 3"],
      "nasil": "nasıl/nereden başvurulur",
      "ipucu": "pratik ipucu"
    }}
  }}
}}

KURALLAR:
- 16-20 fırsat hedefle; köklü programları (Horizon, DIGITAL, EIC, BMBF, NRW,
  Skills Academy, World Bank, OECD) her zaman dahil et, varsa yenileri ekle.
- "sum" içindeki her anahtar "data" içindeki bir "title" ile birebir aynı olmalı.
- "sartlar" en fazla 4 KISA madde; tüm metinler kısa ve öz olsun.
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


def main():
    payload = get_opportunities()
    if "data" not in payload or "sum" not in payload:
        print("HATA: beklenen 'data'/'sum' alanları yok.", file=sys.stderr)
        sys.exit(1)
    html = build_html(payload)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"OK: {OUTPUT} güncellendi — {len(payload['data'])} fırsat ({TODAY}).")


if __name__ == "__main__":
    main()
