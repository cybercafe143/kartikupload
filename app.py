import os
import requests
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)

# ── Config ──────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID",   "YOUR_CHAT_ID_HERE")
UPLOAD_FOLDER      = os.environ.get("UPLOAD_FOLDER", "uploads")
MAX_FILE_MB        = int(os.environ.get("MAX_FILE_MB", "50"))
ALLOWED_EXTENSIONS = {
    "png","jpg","jpeg","gif","webp","bmp",       # images
    "pdf","doc","docx","txt","xls","xlsx","ppt","pptx",  # docs
    "mp4","mov","avi","mkv","mp3","wav",          # media
    "zip","rar","7z"                              # archives
}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_MB * 1024 * 1024
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ── Helpers ──────────────────────────────────────────────────────
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def send_to_telegram(file_path, filename, caption=""):
    ext = filename.rsplit(".", 1)[-1].lower()
    api = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

    # Choose right Telegram method
    if ext in {"png","jpg","jpeg","gif","webp","bmp"}:
        method, key = "sendPhoto", "photo"
    elif ext in {"mp4","mov","avi","mkv"}:
        method, key = "sendVideo", "video"
    elif ext in {"mp3","wav"}:
        method, key = "sendAudio", "audio"
    else:
        method, key = "sendDocument", "document"

    with open(file_path, "rb") as f:
        resp = requests.post(
            f"{api}/{method}",
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption},
            files={key: (filename, f)},
            timeout=60,
        )
    return resp.ok, resp.json()

# ── Routes ──────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("upload.html")

@app.route("/upload", methods=["POST"])
def upload():
    if "files" not in request.files:
        return jsonify({"success": False, "error": "No files sent"}), 400

    files = request.files.getlist("files")
    sender_name = request.form.get("name", "Anonymous").strip() or "Anonymous"
    message     = request.form.get("message", "").strip()

    results = []
    for file in files:
        if not file or file.filename == "":
            continue
        if not allowed_file(file.filename):
            results.append({"name": file.filename, "ok": False, "error": "File type not allowed"})
            continue

        filename  = secure_filename(file.filename)
        # Prefix with timestamp to avoid collisions
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_name = f"{timestamp}_{filename}"
        save_path  = os.path.join(app.config["UPLOAD_FOLDER"], saved_name)
        file.save(save_path)

        caption = f"📤 New Upload\n👤 From: {sender_name}"
        if message:
            caption += f"\n💬 Note: {message}"
        caption += f"\n📁 File: {filename}"
        caption += f"\n🕐 Time: {datetime.now().strftime('%d %b %Y, %I:%M %p')}"

        ok, _ = send_to_telegram(save_path, saved_name, caption)
        results.append({"name": filename, "ok": ok})

    success_count = sum(1 for r in results if r["ok"])
    if success_count == 0:
        return jsonify({"success": False, "error": "Upload failed", "results": results}), 500

    return jsonify({
        "success": True,
        "message": f"{success_count} file(s) sent to Telegram!",
        "results": results,
    })

@app.route("/uploads/<path:filename>")
def serve_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/health")
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
