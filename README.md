# YouTube Clipper

Auto-generate clips from YouTube videos with subtitles. Ready for TikTok, Reels, and YouTube Shorts.

## Features

- 🎬 Automatic clip detection using LLM
- 📝 Subtitle generation and burning
- 📱 Vertical (9:16) and Horizontal (16:9) output
- 🌐 Indonesian and English subtitles
- 🔐 Login system with admin panel
- 🚀 Deployable to Railway

## Quick Start

### Default Admin Account

| Username | Password |
|---|---|
| `salasklip` | `123456` |

Login as admin → access "Kelola User" → create accounts for others.

## Tech Stack

- **Backend:** FastAPI, yt-dlp, faster-whisper, ffmpeg
- **LLM:** Fallback chain (tokbomreplit1 → opencode-free)
- **Frontend:** Vanilla JS + Tailwind CSS
- **Auth:** JWT + bcrypt, SQLite

## Deployment (Railway)

1. Fork/clone this repo
2. Create new project on Railway
3. Connect this repo
4. Add volume for `/app/data` (500MB, for SQLite)
5. Set environment variables:
   - `CLIPPER_LLM_API_KEY` — API key for LLM
   - `CLIPPER_SECRET_KEY` — random string for JWT
   - `CLIPPER_OWNER_PASSWORD` — (optional) override admin password
6. Deploy

## ⚠️ YouTube Bot Detection (Penting!)

YouTube memblokir download dari server/datacenter IP. Jika error "Sign in to confirm you're not a bot":

**Solusi: Export cookies dari browser kamu**

1. Install extension [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) di Chrome/Firefox
2. Buka youtube.com dalam keadaan **sudah login**
3. Klik extension → Export → simpan file `cookies.txt`
4. Upload file tersebut lewat panel admin (fitur akan datang) atau taruh di `/app/data/cookies.txt`

Tanpa cookies, video YouTube umumnya tetap bisa diproses dari IP Indonesia residensial, tapi IP datacenter (Railway) hampir pasti diblokir.

## Local Development

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/api/login` | POST | Login (username, password) |
| `/api/me` | GET | Current user info |
| `/api/admin/users` | GET | List users (admin) |
| `/api/admin/users` | POST | Create user (admin) |
| `/api/admin/users/{username}` | DELETE | Delete user (admin) |
| `/api/clip/create` | POST | Start clip generation |
| `/api/clip/status/{job_id}` | GET | Get job status |
| `/api/clip/download/{clip_id}` | GET | Download clip |

## Local Development

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## License

MIT