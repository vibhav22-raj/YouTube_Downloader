import React, { useState } from 'react';
import { Download, Music, Video, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';

export default function YouTubeDownloader() {
  const [url, setUrl] = useState('');
  const [isValidated, setIsValidated] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [videoInfo, setVideoInfo] = useState(null);

  const validateURL = (url) => {
    const patterns = [
      /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+$/,
      /^(https?:\/\/)?(www\.)?youtube\.com\/watch\?v=[\w-]+/,
      /^(https?:\/\/)?(www\.)?youtu\.be\/[\w-]+/
    ];
    return patterns.some(pattern => pattern.test(url));
  };

  const handleGenerate = async () => {
    if (!url.trim()) {
      setMessage({ type: 'error', text: 'Please enter a YouTube URL' });
      return;
    }

    if (!validateURL(url)) {
      setMessage({ type: 'error', text: 'Invalid YouTube URL. Please check and try again.' });
      return;
    }

    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      // Simulate API call to get video info
      const response = await fetch('http://localhost:5000/api/video-info', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });

      if (!response.ok) {
        throw new Error('Failed to fetch video information');
      }

      const data = await response.json();
      setVideoInfo(data);
      setIsValidated(true);
      setMessage({ type: 'success', text: 'Video found! Choose download option below.' });
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to validate URL. Please check your connection and try again.' });
      setIsValidated(false);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (type) => {
    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      const endpoint = type === 'video' ? '/api/download/video' : '/api/download/audio';
      const response = await fetch(`http://localhost:5000${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });

      if (!response.ok) {
        throw new Error(`Download failed: ${response.statusText}`);
      }

      // Get filename from Content-Disposition header
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = type === 'video' ? 'video.mp4' : 'audio.mp3';
      
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
        if (filenameMatch) filename = filenameMatch[1];
      }

      // Create blob and download
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(downloadUrl);
      document.body.removeChild(a);

      setMessage({ 
        type: 'success', 
        text: `${type === 'video' ? 'Video' : 'Audio'} downloaded successfully!` 
      });
    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: `Failed to download ${type}. Please try again.` 
      });
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setUrl('');
    setIsValidated(false);
    setMessage({ type: '', text: '' });
    setVideoInfo(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-pink-50 p-4">
      <div className="max-w-3xl mx-auto pt-12">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-red-500 to-pink-500 rounded-full mb-4">
            <Download className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            YouTube Downloader
          </h1>
          <p className="text-gray-600">
            Download YouTube videos and audio in high quality
          </p>
        </div>

        {/* Disclaimer */}
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-8 rounded-r-lg">
          <div className="flex items-start">
            <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5 mr-3 flex-shrink-0" />
            <div>
              <p className="text-sm text-yellow-800 font-semibold">Educational Use Only</p>
              <p className="text-xs text-yellow-700 mt-1">
                This tool is for educational purposes. Respect copyright laws and YouTube's Terms of Service.
              </p>
            </div>
          </div>
        </div>

        {/* Main Card */}
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          {!isValidated ? (
            <>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                YouTube Video URL
              </label>
              <div className="flex gap-3 mb-6">
                <input
                  type="text"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://www.youtube.com/watch?v=..."
                  className="flex-1 px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:outline-none transition"
                  disabled={loading}
                  onKeyPress={(e) => e.key === 'Enter' && handleGenerate()}
                />
                <button
                  onClick={handleGenerate}
                  disabled={loading}
                  className="px-8 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-semibold rounded-lg hover:from-purple-700 hover:to-pink-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Validating...
                    </>
                  ) : (
                    'Generate'
                  )}
                </button>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm text-gray-600 mb-2 font-semibold">How to use:</p>
                <ol className="text-sm text-gray-600 space-y-1 list-decimal list-inside">
                  <li>Copy a YouTube video URL</li>
                  <li>Paste it in the input field above</li>
                  <li>Click "Generate" to validate</li>
                  <li>Choose to download video (MP4) or audio (MP3)</li>
                </ol>
              </div>
            </>
          ) : (
            <>
              {/* Video Info */}
              {videoInfo && (
                <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600 mb-1">Ready to download:</p>
                  <p className="font-semibold text-gray-800 truncate">{videoInfo.title || url}</p>
                </div>
              )}

              {/* Download Buttons */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <button
                  onClick={() => handleDownload('video')}
                  disabled={loading}
                  className="flex items-center justify-center gap-3 px-6 py-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-semibold rounded-lg hover:from-blue-700 hover:to-blue-800 transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Video className="w-6 h-6" />
                  <span>Download Video (MP4)</span>
                </button>

                <button
                  onClick={() => handleDownload('audio')}
                  disabled={loading}
                  className="flex items-center justify-center gap-3 px-6 py-4 bg-gradient-to-r from-green-600 to-green-700 text-white font-semibold rounded-lg hover:from-green-700 hover:to-green-800 transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Music className="w-6 h-6" />
                  <span>Download Audio (MP3)</span>
                </button>
              </div>

              <button
                onClick={handleReset}
                disabled={loading}
                className="w-full px-6 py-3 border-2 border-gray-300 text-gray-700 font-semibold rounded-lg hover:bg-gray-50 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Download Another Video
              </button>
            </>
          )}

          {/* Message Display */}
          {message.text && (
            <div className={`mt-6 p-4 rounded-lg flex items-start gap-3 ${
              message.type === 'success' 
                ? 'bg-green-50 border border-green-200' 
                : 'bg-red-50 border border-red-200'
            }`}>
              {message.type === 'success' ? (
                <CheckCircle2 className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
              ) : (
                <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
              )}
              <p className={`text-sm ${
                message.type === 'success' ? 'text-green-800' : 'text-red-800'
              }`}>
                {message.text}
              </p>
            </div>
          )}
        </div>

        {/* Features */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg p-4 shadow-lg text-center">
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <Video className="w-6 h-6 text-blue-600" />
            </div>
            <h3 className="font-semibold text-gray-800 mb-1">High Quality Video</h3>
            <p className="text-sm text-gray-600">Download videos in best available quality</p>
          </div>

          <div className="bg-white rounded-lg p-4 shadow-lg text-center">
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <Music className="w-6 h-6 text-green-600" />
            </div>
            <h3 className="font-semibold text-gray-800 mb-1">MP3 Audio</h3>
            <p className="text-sm text-gray-600">Extract audio in high-quality MP3 format</p>
          </div>

          <div className="bg-white rounded-lg p-4 shadow-lg text-center">
            <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <Download className="w-6 h-6 text-purple-600" />
            </div>
            <h3 className="font-semibold text-gray-800 mb-1">Fast & Secure</h3>
            <p className="text-sm text-gray-600">Direct downloads with no tracking</p>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-gray-600">
          <p>Built for educational purposes • Respect content creators and copyright laws</p>
        </div>
      </div>
    </div>
  );
}