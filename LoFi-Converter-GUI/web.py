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

def get_ffmpeg_path():
    """Get FFmpeg path from environment or common locations"""
    print("Searching for FFmpeg...")
    
    # Set the FFmpeg path directly to the known Chocolatey installation
    ffmpeg_path = 'C:\\ProgramData\\chocolatey\\bin\\ffmpeg.exe'
    if os.path.isfile(ffmpeg_path):
        print(f"Found FFmpeg at: {ffmpeg_path}")
        return ffmpeg_path

    # Fallback to checking other common locations
    common_paths = [
        'C:\\ProgramData\\chocolatey\\lib\\ffmpeg\\tools\\ffmpeg\\bin\\ffmpeg.exe',
        'ffmpeg.exe',
        'ffmpeg'
    ]

    print("Checking common locations...")
    for path in common_paths:
        try:
            print(f"Trying {path}...")
            if os.path.isfile(path):
                print(f"Found FFmpeg at: {path}")
                return path
        except Exception as e:
            print(f"Error checking {path}: {str(e)}")
            continue

    print("FFmpeg not found in any location")
    raise Exception("FFmpeg not found in system")

def download_youtube_audio(url: str):
    """Download audio from YouTube URL"""
    if not url.startswith(('http://', 'https://')):
        raise ValueError("Invalid URL format")
        
    try:
        # Get FFmpeg path
        ffmpeg_path = get_ffmpeg_path()
        print(f"Using FFmpeg at: {ffmpeg_path}")
        
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
            'ffmpeg_location': os.path.dirname(ffmpeg_path)
        }
        
        print("Starting download with options:", ydl_opts)
        
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
        print(f"Starting conversion for URL: {request.youtube_link}")
        
        # Download and convert audio
        audio_file, title = download_youtube_audio(request.youtube_link)
        print(f"Download successful. File: {audio_file}")
        
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
    try:
        ffmpeg_path = get_ffmpeg_path()
        return {
            "status": "healthy",
            "ffmpeg_path": ffmpeg_path,
            "ffmpeg_version": subprocess.check_output([ffmpeg_path, '-version']).decode().split('\n')[0]
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }