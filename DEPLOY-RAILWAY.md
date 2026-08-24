# 🚂 Deploy YouTube Clipper ke Railway — Reference Guide

File ini sebagai panduan cepat untuk deploy dan troubleshooting app ini ke Railway.

## 🔧 Langkah Deploy

1. **Fork / buat repo** `youtube-clipper` di GitHub (sudah ada: https://github.com/irbabulsalas/youtube-clipper)
2. **Buka [railway.app](https://railway.app)** → login → **New Project** → deploy from repo
3. Pilih repo: `irbabulsalas/youtube-clipper`
4. Di **Settings → Variables**, tambahkan:
   - `CLIPPER_LLM_API_KEY` = API key LLM (bisa kosong pakai fallback opencode-free)
   - `CLIPPER_SECRET_KEY` = string random apa saja
   - `CLIPPER_OWNER_PASSWORD` = (opsional) default `123456`
5. Di **Settings → Networking → Volumes**, mount volume ke `/app/data`, ukuran 500MB–1GB
6. Klik **Deploy** → tunggu sampai tampil URL seperti:
   ```
   https://youtube-clipper-production.up.railway.app
   ```

## 🔑 Akun Default

| Username | Password |
|---|---|
| `salasklip` | `123456` *(bisa di-override via env `CLIPPER_OWNER_PASSWORD`)* |

## 🔧 Troubleshoot Umum

| Error | Penyebab | Solusi |
|------|---------|--------|
| `Invalid value for '--port': '$PORT'` | CMD JSON array bentuk, shell tidak expand `$PORT` | Pakai `CMD sh -c "..."` di Dockerfile |
| `cannot import name 'yt_dlp_ejs'` | Versi yt-dlp lama | Upgrade: `pip install --upgrade yt-dlp` |
| `Sign in to confirm you're not a bot` | IP Datacenter diban YouTube | Upload `cookies.txt` lewat UI |
| File hilang setelah restart | Volume `/app/data` belum di-mount | Mount volume di Railway |

## 📤 Upload Cookies (Bot Bypass)

1. Di browser: install extension **Get cookies.txt LOCALLY** (Chrome Web Store)
2. Buka [youtube.com](https://youtube.com), pastikan login
3. Klik extension → **Export** → simpan `cookies.txt`
4. Di app: klik tombol **Upload File** → pilih `cookies.txt` → **Upload**

## 🧪 Smoke Test

```bash
APP="https://youtube-clipper-production.up.railway.app"

curl $APP/health                      # harus 200 OK
curl -X POST $APP/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"salasklip","password":"123456"}'
```

## Env Vars

| Variable | Contoh/Penjelasan |
|---|---|
| `CLIPPER_SECRET_KEY` | random 32-char untuk JWT |
| `CLIPPER_OWNER_PASSWORD` | ubah password admin default |
| `CLIPPER_LLM_API_KEY` | API key LLM (optional) |
| `CLIPPER_COOKIES_FILE` | path ke cookies.txt, default `/app/data/cookies.txt` |
| `PORT` | auto-injected oleh Railway, jangan set manual |