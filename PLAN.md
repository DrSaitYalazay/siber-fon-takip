# Bulut Otomasyon Planı — Siber Güvenlik Fon Takip Sistemi

**Amaç:** Pano ve haftalık tarama, bilgisayar kapalı olsa bile 7/24 bulutta çalışsın. Telefondan kalıcı bir web linkiyle açılsın.

**Seçilen yol:** GitHub Actions (zamanlayıcı) + Claude API (beyin) + GitHub Pages (kalıcı link) + e-posta + opsiyonel OneDrive kopyası.

---

## 1. Mimari

```
 ┌─────────────────────┐   her Pazartesi 08:00 (cron, buluttta)
 │   GitHub Actions     │ ◄───────────── bilgisayardan bağımsız
 │   (weekly.yml)       │
 └──────────┬───────────┘
            │ çalıştırır
            ▼
 ┌─────────────────────┐   Claude API + web arama
 │   build.py           │ ──► yeni çağrıları bulur, başvuru hakkını süzer,
 │   (Python script)    │     özet yazar, DATA + SUM üretir
 └──────────┬───────────┘
            │ üretir
            ▼
 ┌─────────────────────┐
 │   index.html (pano)  │
 └──────────┬───────────┘
            │ yayınlar / gönderir
   ┌────────┼─────────────────────┬───────────────────┐
   ▼        ▼                     ▼                   ▼
GitHub Pages  Repo'ya commit    E-posta (Outlook)   OneDrive (ops.)
(kalıcı URL)  (geçmiş/versiyon) (haftalık özet)     (telefon senkron)
```

**OneDrive'ın rolü:** Sadece depolama. "Çalıştıran" o değil; panonun bir kopyasını telefonuna senkronlamak için opsiyonel. GitHub Pages linki zaten telefonda açıldığı için OneDrive şart değil.

---

## 2. Bileşenler ve görevleri

| Bileşen | Görevi | Maliyet |
|---|---|---|
| GitHub Actions | Haftalık cron tetikleyici (bilgisayar kapalıyken de çalışır) | Ücretsiz (genel/özel repo: aylık 2000 dk kota; bu iş ~dakikalar) |
| Claude API | Web'i tarar, süzer, özet yazar, pano verisini üretir | Kullandıkça öde — haftalık çalıştırma ~0,05–0,30 USD |
| GitHub Pages | Panoyu kalıcı `https://...github.io/...` linkinde yayınlar | Ücretsiz |
| E-posta (SMTP) | Haftalık özeti gönderir | Ücretsiz (Outlook/Gmail SMTP) |
| OneDrive (ops.) | Pano kopyasını telefona senkronlar | M365 aboneliğine dahil |

---

## 3. Gereksinimler (hepsi sende mevcut)

- [x] GitHub hesabı
- [x] Anthropic (Claude) API anahtarı
- [x] Microsoft 365 (Outlook e-posta + OneDrive)

---

## 4. Kurulum adımları (tek seferlik, ~30–45 dk)

### Adım 1 — Repo oluştur
1. GitHub'da yeni bir **private** repo aç: örn. `siber-fon-takip`.
2. Bu klasördeki dosyaları repoya koy:
   - `build.py`
   - `requirements.txt`
   - `dashboard_template.html` (mevcut panonun bir kopyası — tek kaynak)
   - `.github/workflows/weekly.yml`

### Adım 2 — Gizli anahtarları (Secrets) ekle
Repo → **Settings → Secrets and variables → Actions → New repository secret**:
- `ANTHROPIC_API_KEY` → Claude API anahtarın
- `MAIL_USERNAME` → Gmail adresin
- `MAIL_PASSWORD` → Gmail **uygulama parolası** (16 haneli; normal şifre değil)
- `MAIL_TO` → `ysait2021@gmail.com` (birden çok alıcı için virgülle ayır)
- `MAIL_CC` → opsiyonel ek alıcılar (virgülle). İstemezsen boş bırak.

> Anahtarlar koda yazılmaz; GitHub Secrets şifreli saklar. Bu en güvenli yöntemdir.

### Adım 3 — GitHub Pages'i aç
Repo → **Settings → Pages** → Source: **GitHub Actions** (workflow zaten yayınlıyor).
Birkaç dakika sonra panon `https://<kullanıcıadın>.github.io/siber-fon-takip/` adresinde olur. Bu linki telefonda Safari'de aç, "Ana Ekrana Ekle" de — uygulama gibi durur.

### Adım 4 — İlk çalıştırma (test)
Repo → **Actions → Weekly Fon Tarama → Run workflow** (manuel tetikle). Yeşil tik gelince hem pano güncellenir hem e-posta gelir.

### Adım 5 — Zamanlama otomatik
`weekly.yml` içindeki cron `0 6 * * 1` (her Pazartesi 06:00 UTC ≈ 08:00 TR/DE) bundan sonra kendiliğinden çalışır. Bilgisayar kapalı olsa da çalışır.

### Adım 6 — OneDrive (opsiyonel)
İki kolay yol:
- **Kolay:** GitHub Pages linkini OneDrive'da bir not/kısayol olarak sakla (yeterli, çünkü pano zaten web'de canlı).
- **Tam senkron:** `build.py`'ye Microsoft Graph ile yükleme adımı eklenir (Azure'da uygulama kaydı gerekir — orta seviye kurulum). İstersen bunu sonra ekleriz.

---

## 5. Haftalık çalışma akışı (otomatik)

1. Pazartesi cron tetiklenir.
2. `build.py` Claude API'yi web aramayla çağırır; AB/Almanya/NRW/dünya kaynaklarında yeni veya yaklaşan çağrıları bulur.
3. Yalnızca **bireysel / firma-KOBİ / dernek-vakıf / üniversite** başvurabilenleri tutar; kamu-only olanları `publicOnly:true` işaretler.
4. Her yeni projeye özet (Frist, kim başvurabilir, bütçe, şartlar, nasıl, ipucu) üretir.
5. `index.html` yeniden oluşturulur, repoya commit edilir, GitHub Pages yayınlar.
6. Haftalık özet e-postası gönderilir (bu hafta eklenenler + 45 gün içinde kapanacaklar).

---

## 6. Maliyet özeti

- GitHub Actions + Pages: **0 USD**
- E-posta (Outlook SMTP): **0 USD**
- Claude API: **kullandıkça öde**, haftalık ~0,05–0,30 USD → yıllık tahmini **3–15 USD**.
- OneDrive: M365 aboneliğine dahil.

---

## 7. Güvenlik notları

- API anahtarı ve e-posta parolası **yalnızca GitHub Secrets'ta** durur, kodda görünmez.
- Repo **private** olmalı.
- Outlook için normal parola yerine **uygulama parolası** kullan; istediğinde iptal edebilirsin.
- Pano herkese açık bir Pages linkinde yayınlanır; içinde hassas veri yok (yalnızca kamuya açık fon bilgileri). Gizli olmasını istersen Pages yerine sadece OneDrive'a özel yükleme tercih edilir.

---

## 8. Sonraki adım

Bu klasörde başlangıç kodları hazır: `build.py`, `requirements.txt`, `.github/workflows/weekly.yml`, `README.md`.
İstersen: (a) kodları senin repo adın ve tercihlerine göre özelleştireyim, (b) OneDrive tam-senkron adımını ekleyeyim, (c) e-postayı Outlook yerine Gmail SMTP'ye çevireyim.
