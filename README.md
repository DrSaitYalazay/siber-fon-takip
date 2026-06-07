# Siber Fon Takip — Bulut Otomasyon

7/24 bulutta çalışan haftalık fon/proje tarayıcı. Bilgisayar kapalıyken de çalışır.
Ayrıntılı plan için **PLAN.md**'ye bak.

## Klasör içeriği
```
.
├─ build.py                     # Claude API + web arama → panoyu üretir
├─ requirements.txt             # Python bağımlılığı (anthropic)
├─ dashboard_template.html      # Panonun tek-kaynak şablonu (DATA/SUM/TODAY buradan güncellenir)
├─ index.html                   # build.py'nin ürettiği çıktı (ilk çalıştırmadan sonra oluşur)
├─ PLAN.md                      # Mimari, maliyet, güvenlik, adımlar
└─ .github/workflows/weekly.yml # Haftalık cron + Pages yayını + e-posta
```

## Hızlı kurulum (özet — detay PLAN.md'de)
1. GitHub'da **private** repo aç, bu klasördeki dosyaları yükle.
2. Repo → Settings → Secrets and variables → Actions → şunları ekle:
   - `ANTHROPIC_API_KEY`
   - `MAIL_USERNAME` (Gmail adresin, ör. `ornek@gmail.com`)
   - `MAIL_PASSWORD` (Gmail **uygulama parolası** — 16 haneli, normal şifre değil)
   - `MAIL_TO` = `ysait2021@gmail.com` (birden fazla alıcı için virgülle ayır: `a@x.com, b@y.com`)
   - `MAIL_CC` = *(opsiyonel)* ek alıcılar, yine virgülle ayrılmış. Boş bırakabilirsin.

> **Yeni alıcı eklemek:** `MAIL_TO` (veya `MAIL_CC`) secret'ını düzenleyip yeni adresi virgülle eklemen yeterli — kodu değiştirmene gerek yok.
3. Repo → Settings → Pages → Source: **GitHub Actions**.
4. Repo → Actions → **Weekly Fon Tarama → Run workflow** (ilk test).
5. Pano: `https://<kullanıcıadın>.github.io/<repo-adı>/` — telefonda Safari'de aç, "Ana Ekrana Ekle".

## Yerel test (opsiyonel)
```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python build.py        # index.html üretir
```

## Notlar
- `MODEL` değişkenini `build.py` içinde `claude-opus-4-6` yaparak kaliteyi artırabilirsin (maliyet biraz artar).
- E-postayı Gmail ile göndermek istersen `weekly.yml` içindeki `server_address` → `smtp.gmail.com` ve Gmail uygulama parolası kullan.
- OneDrive tam senkron istersen Microsoft Graph yükleme adımı eklenebilir (PLAN.md Adım 6).
