from flask import Flask, request, jsonify, send_file, render_template_string
from flask_cors import CORS
import yt_dlp
import os
import re
from pathlib import Path
import tempfile
import time

# ================== APP SETUP ==================
app = Flask(__name__)
CORS(app)

# ================== FFMPEG ==================
# Render already has FFmpeg installed
FFMPEG_PATH = None

# ================== DOWNLOAD DIRECTORY ==================
DOWNLOAD_DIR = Path(tempfile.gettempdir()) / "yt_downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

# ================== HTML TEMPLATE ==================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>YouTube Downloader</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 flex items-center justify-center min-h-screen">

<div class="bg-white p-8 rounded shadow-md w-full max-w-xl">
    <h1 class="text-2xl font-bold mb-4 text-center">YouTube Downloader</h1>

    <input id="url" class="w-full border p-3 rounded mb-4"
           placeholder="Paste YouTube URL here">

    <button onclick="getInfo()"
        class="bg-blue-600 text-white px-4 py-2 rounded w-full mb-3">
        Generate
    </button>

    <div id="info" class="hidden">
        <p class="font-semibold mb-3" id="title"></p>

        <button onclick="download('video')"
            class="bg-green-600 text-white px-4 py-2 rounded w-full mb-2">
            Download Video (MP4)
        </button>

        <button onclick="download('audio')"
            class="bg-purple-600 text-white px-4 py-2 rounded w-full">
            Download Audio (MP3)
        </button>
    </div>

    <p id="msg" class="text-red-600 mt-3 text-sm"></p>
</div>

<script>
const API = window.location.origin;
let currentUrl = "";

async function getInfo() {
    const url = document.getElementById("url").value;
    const msg = document.getElementById("msg");
    msg.textContent = "";

    const res = await fetch(API + "/api/video-info", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({url})
    });

    const data = await res.json();
    if (!res.ok) {
        msg.textContent = data.error;
        return;
    }

    document.getElementById("info").classList.remove("hidden");
    document.getElementById("title").textContent = data.title;
    currentUrl = url;
}

async function download(type) {
    const endpoint = type === "video"
        ? "/api/download/video"
        : "/api/download/audio";

    const res = await fetch(API + endpoint, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({url: currentUrl})
    });

    if (!res.ok) {
        const e = await res.json();
        alert(e.error);
        return;
    }

    const blob = await res.blob();
    const a = document.createElement("a");
    a.href = window.URL.createObjectURL(blob);
    a.download = type === "video" ? "video.mp4" : "audio.mp3";
    a.click();
}
</script>
</body>
</html>
"""

# ================== HELPERS ==================
def validate_youtube_url(url):
    patterns = [
        r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+",
        r"(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]+",
        r"(https?://)?(www\.)?youtu\.be/[\w-]+",
    ]
    return any(re.match(p, url) for p in patterns)


def clean_filename(name):
    name = re.sub(r'[<>:"/\\|?*]', "", name).strip(". ")
    return name[:200] if name else "download"


def clean_old_files():
    now = time.time()
    for f in DOWNLOAD_DIR.iterdir():
        if f.is_file() and now - f.stat().st_mtime > 3600:
            f.unlink()


def get_ydl_opts():
    return {
        "quiet": True,
        "nocheckcertificate": True,
        "socket_timeout": 30,
        "user_agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
        ),
        "referer": "https://www.youtube.com/",
    }

# ================== ROUTES ==================
@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/video-info", methods=["POST"])
def video_info():
    try:
        url = request.json.get("url", "").strip()
        if not validate_youtube_url(url):
            return jsonify({"error": "Invalid YouTube URL"}), 400

        opts = get_ydl_opts()
        opts["skip_download"] = True

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)

        return jsonify({
            "title": info.get("title"),
            "duration": info.get("duration"),
            "uploader": info.get("uploader")
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/download/video", methods=["POST"])
def download_video():
    try:
        url = request.json.get("url", "").strip()
        if not validate_youtube_url(url):
            return jsonify({"error": "Invalid YouTube URL"}), 400

        clean_old_files()
        ts = int(time.time())
        outtmpl = str(DOWNLOAD_DIR / f"video_{ts}_%(title)s.%(ext)s")

        opts = get_ydl_opts()
        opts.update({
            "format": "best[ext=mp4]/best",
            "outtmpl": outtmpl,
            "merge_output_format": "mp4",
        })

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        title = clean_filename(info.get("title", "video"))
        return send_file(filename, as_attachment=True,
                         download_name=f"{title}.mp4",
                         mimetype="video/mp4")

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/download/audio", methods=["POST"])
def download_audio():
    try:
        url = request.json.get("url", "").strip()
        if not validate_youtube_url(url):
            return jsonify({"error": "Invalid YouTube URL"}), 400

        clean_old_files()
        ts = int(time.time())
        outtmpl = str(DOWNLOAD_DIR / f"audio_{ts}_%(title)s.%(ext)s")

        opts = get_ydl_opts()
        opts.update({
            "format": "bestaudio/best",
            "outtmpl": outtmpl,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        })

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            base = ydl.prepare_filename(info)
            mp3 = os.path.splitext(base)[0] + ".mp3"

        title = clean_filename(info.get("title", "audio"))
        return send_file(mp3, as_attachment=True,
                         download_name=f"{title}.mp3",
                         mimetype="audio/mpeg")

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# ================== MAIN ==================
if __name__ == "__main__":
    print("🚀 YouTube Downloader running")
    app.run(host="0.0.0.0", port=5000)
