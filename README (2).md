# 📤 kartikdev File Upload → Telegram Bot

Koi bhi `upload.kartikdev.best` pe jaye, files upload kare — seedha tera Telegram pe aa jaye.

---

## ⚡ Step 1 — Telegram Bot Setup

### Bot Token lena:
1. Telegram pe `@BotFather` open kar
2. `/newbot` type kar
3. Name: `KartikUploadBot` (kuch bhi)
4. Username: `kartik_upload_bot` (unique hona chahiye)
5. Token copy kar — ye format hoga: `7234567890:AAGxxxxxxxxxxxxxxxxxxxx`

### Chat ID lena:
1. Telegram pe apne bot se `/start` bhej
2. Browser mein ye URL open kar (token replace kar):
   ```
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```
3. Response mein `"id"` field dekh — wo tera Chat ID hai
   ```json
   {"message":{"chat":{"id": 123456789}}}
   ```

---

## 🚀 Step 2 — Railway pe Deploy

### A) GitHub pe push kar:
```bash
cd kartikupload
git init
git add .
git commit -m "Initial upload app"
git remote add origin https://github.com/<yourusername>/kartikupload.git
git push -u origin main
```

### B) Railway setup:
1. [railway.app](https://railway.app) pe jaa → `New Project` → `Deploy from GitHub repo`
2. Apna `kartikupload` repo select kar
3. **Environment Variables** section mein ye add kar:

| Variable | Value |
|----------|-------|
| `TELEGRAM_BOT_TOKEN` | `7234567890:AAGxxxx...` |
| `TELEGRAM_CHAT_ID` | `123456789` |
| `MAX_FILE_MB` | `50` |

4. Deploy hone do (1-2 min)
5. Railway ek URL dega jaise: `kartikupload-production.up.railway.app`

---

## 🌐 Step 3 — Subdomain Setup (upload.kartikdev.best)

### Ye steps follow kar (domain provider pe jaha se `kartikdev.best` liya hai):

**Namecheap / GoDaddy / Hostinger:**
1. DNS Settings open kar
2. New CNAME Record add kar:
   - **Type:** `CNAME`
   - **Name / Host:** `upload`
   - **Value / Points to:** `kartikupload-production.up.railway.app`
   - **TTL:** Auto

3. Railway mein: `Settings → Domains → Add Custom Domain`
4. Enter karo: `upload.kartikdev.best`
5. DNS propagation mein 5-30 min lag sakta hai

✅ Done! Ab `upload.kartikdev.best` pe jao — site live hogi!

---

## 🧪 Test karna

1. Site kholo
2. Ek photo select karo
3. Name bharo: "Test"
4. Send karo
5. Tera Telegram bot pe message aana chahiye

---

## 🔧 Local Testing (optional)

```bash
pip install -r requirements.txt

# Windows:
set TELEGRAM_BOT_TOKEN=your_token
set TELEGRAM_CHAT_ID=your_chat_id
python app.py

# Mac/Linux:
TELEGRAM_BOT_TOKEN=your_token TELEGRAM_CHAT_ID=your_chat_id python app.py
```

Open: `http://localhost:5000`

---

## 📁 Project Structure

```
kartikupload/
├── app.py              ← Flask backend (main logic)
├── requirements.txt    ← Python packages
├── Procfile            ← Railway/Render deployment
├── README.md           ← Ye file
├── templates/
│   └── upload.html     ← Beautiful upload page
└── uploads/            ← Temporary file storage (auto-created)
```

---

## ✨ Features

- 🖼️ Images, 📄 Docs, 🎬 Videos, 📦 Archives — sab support
- Drag & Drop + Click to browse
- File preview with thumbnails
- Sender name + optional message
- Straight to Telegram — no login needed
- 50 MB per file limit (configurable)
- Mobile friendly
