from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import yt_dlp
import os
import uuid
from pydub import AudioSegment
import tempfile
import shutil

app = FastAPI()

# Configure CORS
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:8000",
    "https://lofi-converter-gui-production.up.railway.app",
    "https://lofi-converter.samevibe.in",
    "https://*.up.railway.app",
    "*"  # Allow all origins for health check
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]
)

class YouTubeRequest(BaseModel):
    youtube_link: str

def download_youtube_audio(youtube_url: str) -> str:
    try:
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        
        # Generate a unique filename (without extension)
        filename = str(uuid.uuid4())
        output_path = os.path.join(temp_dir, filename)
        
        # Download options
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': output_path,
        }
        
        # Download the audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
        
        # The actual output file will have .mp3 extension added by yt-dlp
        actual_output_path = output_path + '.mp3'
        if not os.path.exists(actual_output_path):
            raise Exception(f"Downloaded file not found at {actual_output_path}")
            
        return actual_output_path
        
    except Exception as e:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        raise Exception(f"Error downloading audio: {str(e)}")

def apply_lofi_effect(input_path: str) -> str:
    try:
        if not os.path.exists(input_path):
            raise Exception(f"Input file not found at {input_path}")
            
        # Create output path in the same directory as input
        output_dir = os.path.dirname(input_path)
        output_filename = f"lofi_{os.path.basename(input_path)}"
        output_path = os.path.join(output_dir, output_filename)
        
        print(f"Processing audio file: {input_path}")
        print(f"Output will be saved to: {output_path}")
        
        # Load the audio file
        audio = AudioSegment.from_mp3(input_path)
        
        # Apply lo-fi effects:
        # 1. Slow down the tempo (85% speed)
        slowed_audio = audio._spawn(audio.raw_data, overrides={
            "frame_rate": int(audio.frame_rate * 0.85)
        })
        
        # 2. Lower the sample rate for that "vintage" sound
        lofi_audio = slowed_audio.set_frame_rate(22050)
        
        # 3. Add some subtle compression
        lofi_audio = lofi_audio.compress_dynamic_range()
        
        # Export the processed audio
        lofi_audio.export(output_path, format="mp3", bitrate="192k")
        
        if not os.path.exists(output_path):
            raise Exception(f"Failed to create output file at {output_path}")
            
        return output_path
        
    except Exception as e:
        raise Exception(f"Error applying lo-fi effect: {str(e)}")

@app.post("/convert")
async def convert_audio(request: YouTubeRequest):
    temp_dir = None
    input_path = None
    output_path = None
    
    try:
        # Download the YouTube audio
        input_path = download_youtube_audio(request.youtube_link)
        
        # Apply lo-fi effect
        output_path = apply_lofi_effect(input_path)
        
        # Read the processed file
        with open(output_path, 'rb') as f:
            audio_data = f.read()
            
        # Return base64 encoded audio data
        import base64
        return {
            "audio_data": base64.b64encode(audio_data).decode('utf-8'),
            "filename": f"lofi_{uuid.uuid4()}.mp3"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # Clean up temporary files
        if input_path and os.path.exists(input_path):
            os.remove(input_path)
        if output_path and os.path.exists(output_path):
            os.remove(output_path)
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

@app.get("/health")
@app.get("/")
async def health_check():
    try:
        # Basic system checks
        import psutil
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "status": "healthy",
            "message": "Lo-Fi Converter API is running",
            "system_info": {
                "memory_available": f"{memory.available / (1024 * 1024):.1f}MB",
                "disk_free": f"{disk.free / (1024 * 1024 * 1024):.1f}GB"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": str(e)
        }