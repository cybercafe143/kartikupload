import os
import requests
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)

# ── Config ──────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID",   "YOUR_CHAT_ID_HERE")
UPLOAD_FOLDER      = os.environ.get("UPLOAD_FOLDER", "/tmp/uploads")  # /tmp on Render free tier
MAX_FILE_MB        = int(os.environ.get("MAX_FILE_MB", "500"))

ALLOWED_EXTENSIONS = {
    "png","jpg","jpeg","gif","webp","bmp",
    "pdf","doc","docx","txt","xls","xlsx","ppt","pptx",
    "mp4","mov","avi","mkv","mp3","wav","m4a","ogg",
    "zip","rar","7z"
}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = None  # No Flask-level limit
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ── Helpers ──────────────────────────────────────────────────────
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size_mb(path):
    return os.path.getsize(path) / (1024 * 1024)

def send_to_telegram(file_path, filename, caption=""):
    ext     = filename.rsplit(".", 1)[-1].lower()
    api     = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    size_mb = get_file_size_mb(file_path)

    # Smart method selection based on type + size
    if ext in {"png","jpg","jpeg","gif","webp","bmp"} and size_mb < 10:
        method, key = "sendPhoto", "photo"
    elif ext in {"mp4","mov","avi","mkv"} and size_mb < 50:
        method, key = "sendVideo", "video"
    elif ext in {"mp3","wav","m4a","ogg"} and size_mb < 50:
        method, key = "sendAudio", "audio"
    else:
        method, key = "sendDocument", "document"  # Works for ALL types up to 2GB

    try:
        with open(file_path, "rb") as f:
            resp = requests.post(
                f"{api}/{method}",
                data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption},
                files={key: (filename, f)},
                timeout=300,  # 5 min timeout for large files
            )

        # Fallback: agar photo/video fail ho toh document try karo
        if not resp.ok and method != "sendDocument":
            with open(file_path, "rb") as f:
                resp = requests.post(
                    f"{api}/sendDocument",
                    data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption},
                    files={"document": (filename, f)},
                    timeout=300,
                )

        return resp.ok, resp.json()

    except requests.exceptions.Timeout:
        notif = caption + f"\n\n⚠️ File too large to forward ({size_mb:.1f} MB)"
        requests.post(f"{api}/sendMessage",
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": notif}, timeout=10)
        return False, {"error": "timeout"}

    except Exception as e:
        return False, {"error": str(e)}

    finally:
        try:
            os.remove(file_path)
        except:
            pass

# ── Routes ──────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("upload.html")

@app.route("/upload", methods=["POST"])
def upload():
    if "files" not in request.files:
        return jsonify({"success": False, "error": "No files sent"}), 400

    files       = request.files.getlist("files")
    sender_name = request.form.get("name", "Anonymous").strip() or "Anonymous"
    message     = request.form.get("message", "").strip()

    results = []
    for file in files:
        if not file or file.filename == "":
            continue
        if not allowed_file(file.filename):
            results.append({"name": file.filename, "ok": False, "error": "File type not allowed"})
            continue

        filename   = secure_filename(file.filename)
        timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_name = f"{timestamp}_{filename}"
        save_path  = os.path.join(app.config["UPLOAD_FOLDER"], saved_name)

        try:
            file.save(save_path)
        except Exception as e:
            results.append({"name": filename, "ok": False, "error": f"Save failed: {str(e)}"})
            continue

        size_mb = get_file_size_mb(save_path)

        if size_mb > MAX_FILE_MB:
            os.remove(save_path)
            results.append({"name": filename, "ok": False,
                            "error": f"File too large ({size_mb:.0f} MB). Max {MAX_FILE_MB} MB."})
            continue

        caption  = f"📤 New Upload\n👤 From: {sender_name}"
        if message:
            caption += f"\n💬 Note: {message}"
        caption += f"\n📁 File: {filename}"
        caption += f"\n📦 Size: {size_mb:.1f} MB"
        caption += f"\n🕐 Time: {datetime.now().strftime('%d %b %Y, %I:%M %p')}"

        ok, _ = send_to_telegram(save_path, saved_name, caption)
        results.append({"name": filename, "ok": ok, "size": f"{size_mb:.1f} MB"})

    success_count = sum(1 for r in results if r["ok"])
    failed        = [r for r in results if not r["ok"]]

    if success_count == 0 and failed:
        return jsonify({"success": False, "error": failed[0].get("error", "Upload failed"),
                        "results": results}), 500

    return jsonify({"success": True,
                    "message": f"{success_count} file(s) sent to Telegram! 🎉",
                    "results": results})

@app.errorhandler(413)
def too_large(e):
    return jsonify({"success": False, "error": "File too large!"}), 413

@app.route("/health")
def health():
    return jsonify({"status": "ok", "max_file_mb": MAX_FILE_MB})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
