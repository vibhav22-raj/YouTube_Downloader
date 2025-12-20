from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import re
from pathlib import Path
import tempfile
import time

app = Flask(__name__)
CORS(app)

# ========== FFMPEG CONFIGURATION ==========
FFMPEG_PATH = r'C:\ffmpeg\bin'

if os.path.exists(FFMPEG_PATH):
    os.environ['PATH'] = FFMPEG_PATH + os.pathsep + os.environ.get('PATH', '')
    print(f"✅ FFmpeg path added: {FFMPEG_PATH}")
else:
    print(f"⚠️  FFmpeg not found at: {FFMPEG_PATH}")
# ==========================================

DOWNLOAD_DIR = Path(tempfile.gettempdir()) / 'yt_downloads'
DOWNLOAD_DIR.mkdir(exist_ok=True)

def validate_youtube_url(url):
    """Validate if the URL is a valid YouTube URL"""
    youtube_patterns = [
        r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/',
        r'(https?://)?(www\.)?youtube\.com\/watch\?v=[\w-]+',
        r'(https?://)?(www\.)?youtu\.be\/[\w-]+'
    ]
    return any(re.match(pattern, url) for pattern in youtube_patterns)

def clean_filename(filename):
    """Remove invalid characters from filename"""
    # Remove characters not allowed in Windows filenames
    cleaned = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Remove leading/trailing spaces and dots
    cleaned = cleaned.strip('. ')
    # Limit length to 200 characters
    if len(cleaned) > 200:
        cleaned = cleaned[:200]
    return cleaned if cleaned else 'download'

def clean_old_files():
    """Clean files older than 1 hour"""
    try:
        current_time = time.time()
        for file in DOWNLOAD_DIR.iterdir():
            if file.is_file():
                file_age = current_time - file.stat().st_mtime
                if file_age > 3600:
                    file.unlink()
    except Exception as e:
        print(f"Error cleaning old files: {e}")

def get_ydl_opts():
    """Get common yt-dlp options"""
    return {
        'quiet': False,
        'no_warnings': False,
        'extract_flat': False,
        'socket_timeout': 30,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'referer': 'https://www.youtube.com/',
    }

@app.route('/api/video-info', methods=['POST'])
def get_video_info():
    """Get video information without downloading"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        if not validate_youtube_url(url):
            return jsonify({'error': 'Invalid YouTube URL'}), 400
        
        ydl_opts = get_ydl_opts()
        ydl_opts['skip_download'] = True
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            return jsonify({
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', 'Unknown')
            }), 200
            
    except yt_dlp.utils.DownloadError as e:
        return jsonify({'error': f'YouTube error: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to fetch video info: {str(e)}'}), 500

@app.route('/api/download/video', methods=['POST'])
def download_video():
    """Download YouTube video as MP4"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        if not validate_youtube_url(url):
            return jsonify({'error': 'Invalid YouTube URL'}), 400
        
        clean_old_files()
        
        timestamp = int(time.time())
        output_template = str(DOWNLOAD_DIR / f'video_{timestamp}_%(title)s.%(ext)s')
        
        ydl_opts = get_ydl_opts()
        ydl_opts.update({
            'format': 'best[ext=mp4]/best',
            'outtmpl': output_template,
            'merge_output_format': 'mp4',
            'ffmpeg_location': FFMPEG_PATH,
        })
        
        print(f"📹 Downloading video from: {url}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            video_title = clean_filename(info.get('title', 'video'))
        
        if not os.path.exists(filename):
            filename_mp4 = os.path.splitext(filename)[0] + '.mp4'
            if os.path.exists(filename_mp4):
                filename = filename_mp4
            else:
                return jsonify({'error': 'Download failed - file not found'}), 500
        
        print(f"✅ Video downloaded: {video_title}.mp4")
        
        return send_file(
            filename,
            as_attachment=True,
            download_name=f"{video_title}.mp4",
            mimetype='video/mp4'
        )
        
    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        if '403' in error_msg or 'Forbidden' in error_msg:
            return jsonify({'error': 'YouTube blocked the download. Try a different video.'}), 403
        return jsonify({'error': f'Download error: {error_msg}'}), 500
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

@app.route('/api/download/audio', methods=['POST'])
def download_audio():
    """Download YouTube audio as MP3"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        if not validate_youtube_url(url):
            return jsonify({'error': 'Invalid YouTube URL'}), 400
        
        clean_old_files()
        
        timestamp = int(time.time())
        output_template = str(DOWNLOAD_DIR / f'audio_{timestamp}_%(title)s.%(ext)s')
        
        ydl_opts = get_ydl_opts()
        ydl_opts.update({
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'prefer_ffmpeg': True,
            'ffmpeg_location': FFMPEG_PATH,
        })
        
        print(f"🎵 Downloading audio from: {url}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            base_filename = ydl.prepare_filename(info)
            filename = os.path.splitext(base_filename)[0] + '.mp3'
            audio_title = clean_filename(info.get('title', 'audio'))
        
        if not os.path.exists(filename):
            return jsonify({'error': 'Download failed - MP3 conversion failed'}), 500
        
        print(f"✅ Audio downloaded: {audio_title}.mp3")
        
        return send_file(
            filename,
            as_attachment=True,
            download_name=f"{audio_title}.mp3",
            mimetype='audio/mpeg'
        )
        
    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        if '403' in error_msg or 'Forbidden' in error_msg:
            return jsonify({'error': 'YouTube blocked the download. Try a different video.'}), 403
        if 'ffmpeg' in error_msg.lower() or 'ffprobe' in error_msg.lower():
            return jsonify({'error': f'FFmpeg error. Check installation at {FFMPEG_PATH}'}), 500
        return jsonify({'error': f'Download error: {error_msg}'}), 500
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Server is running'}), 200

if __name__ == '__main__':
    print("🚀 YouTube Downloader Backend Starting...")
    print(f"📁 Download directory: {DOWNLOAD_DIR}")
    print(f"🔧 FFmpeg location: {FFMPEG_PATH}")
    print("🌐 Server running on http://localhost:5000\n")
    app.run(debug=True, host='0.0.0.0', port=5000)