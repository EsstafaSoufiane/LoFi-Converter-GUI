from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import yt_dlp
import os
import uuid
import subprocess

app = FastAPI()

# Configure CORS
origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "https://lofi-converter-gui-production.up.railway.app",
    "https://lofi-converter.samevibe.in"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class YouTubeRequest(BaseModel):
    youtube_link: str

def find_ffmpeg():
    """Find FFmpeg in the system"""
    try:
        # First try the PATH
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            return 'ffmpeg'
            
        # Try common locations
        common_paths = [
            '/usr/bin/ffmpeg',
            '/usr/local/bin/ffmpeg',
            '/opt/ffmpeg/ffmpeg'
        ]
        
        for path in common_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path
                
        raise Exception("FFmpeg not found in system")
    except Exception as e:
        print(f"Error finding FFmpeg: {e}")
        return None

def download_youtube_audio(url: str):
    """Download audio from YouTube URL"""
    if not url.startswith(('http://', 'https://')):
        raise ValueError("Invalid URL format")
        
    try:
        # Find FFmpeg
        ffmpeg_path = find_ffmpeg()
        if not ffmpeg_path:
            raise Exception("FFmpeg not found")
            
        # Create unique filename
        os.makedirs('uploaded_files', exist_ok=True)
        file_id = str(uuid.uuid4())
        output_path = os.path.join('uploaded_files', f"{file_id}.%(ext)s")
        
        # Configure yt-dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'ffmpeg_location': ffmpeg_path
        }
        
        # Download and convert
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                raise Exception("Failed to get video info")
                
            # Get output filename
            output_file = ydl.prepare_filename(info)
            output_file = os.path.splitext(output_file)[0] + '.mp3'
            
            if not os.path.exists(output_file):
                raise Exception(f"Output file not found: {output_file}")
                
            return output_file, info.get('title', 'unknown')
            
    except Exception as e:
        print(f"Download error: {str(e)}")
        raise

@app.post("/convert")
async def convert_audio(request: YouTubeRequest):
    try:
        # Download and convert audio
        audio_file, title = download_youtube_audio(request.youtube_link)
        
        # Read the converted file
        with open(audio_file, 'rb') as f:
            audio_data = f.read()
            
        # Clean up
        try:
            os.remove(audio_file)
        except Exception as e:
            print(f"Cleanup error: {e}")
            
        return {
            "audio_data": audio_data,
            "filename": f"{title}.mp3"
        }
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Conversion error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    ffmpeg_path = find_ffmpeg()
    return {
        "status": "healthy" if ffmpeg_path else "unhealthy",
        "ffmpeg_path": ffmpeg_path
    }