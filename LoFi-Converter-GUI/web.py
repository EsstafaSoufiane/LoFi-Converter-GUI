import os
import streamlit as st
import music
import yt_dlp
import uuid
import sys
import traceback
from streamlit.components.v1 import html, components
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

# Set FFmpeg paths globally
FFMPEG_PATH = "/usr/local/bin/ffmpeg"
FFPROBE_PATH = "/usr/local/bin/ffprobe"

app = FastAPI()

# Configure CORS with specific origins
origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:8501",
    "https://lofi-converter-gui-production.up.railway.app",
    "https://lofi-converter.samevibe.in"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

class YouTubeRequest(BaseModel):
    youtube_link: str

def check_ffmpeg():
    """Verify FFmpeg installation and permissions"""
    try:
        if not os.path.exists(FFMPEG_PATH):
            # Try to find ffmpeg in PATH
            import subprocess
            try:
                ffmpeg_path = subprocess.check_output(['which', 'ffmpeg']).decode().strip()
                global FFMPEG_PATH
                FFMPEG_PATH = ffmpeg_path
                print(f"Found FFmpeg at: {FFMPEG_PATH}")
            except subprocess.CalledProcessError:
                raise Exception("FFmpeg not found in system")
                
        if not os.access(FFMPEG_PATH, os.X_OK):
            # Try to fix permissions
            try:
                os.chmod(FFMPEG_PATH, 0o755)
                print(f"Fixed FFmpeg permissions at {FFMPEG_PATH}")
            except Exception as e:
                raise Exception(f"Cannot make FFmpeg executable: {str(e)}")
                
        return True
    except Exception as e:
        print(f"FFmpeg check failed: {str(e)}")
        return False

def isDownlaodable(url: str) -> bool:
    try:
        if not url.startswith(('http://', 'https://')):
            print(f"Invalid URL format: {url}")
            return False
            
        with yt_dlp.YoutubeDL() as ydl:
            result = ydl.extract_info(url, download=False)
            duration = result.get('duration', 0)
            
            if duration > 600:  # 10 minutes
                print(f"Video too long: {duration} seconds")
                return False
                
            return True
    except Exception as e:
        print(f"Error checking URL {url}: {str(e)}")
        return False

def download_youtube_audio(url: str):
    print(f"\n=== Starting download for URL: {url} ===")
    
    if not check_ffmpeg():
        raise Exception("FFmpeg is not properly configured")
        
    if not isDownlaodable(url):
        print("URL validation failed")
        return None
        
    try:
        os.makedirs('uploaded_files', exist_ok=True)
        uu = str(uuid.uuid4())
        output_template = os.path.join('uploaded_files', f"{uu}.%(ext)s")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'prefer_ffmpeg': True,
            'ffmpeg_location': FFMPEG_PATH,
            'verbose': True
        }
        
        print("Starting YouTube-DL with options:", ydl_opts)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info_dict = ydl.extract_info(url, download=True)
                print("Info dict retrieved:", info_dict.get('title', 'No title'))
                
                audio_file = ydl.prepare_filename(info_dict)
                audio_file = os.path.splitext(audio_file)[0] + '.mp3'
                song_name = info_dict['title']
                
                print(f"Expected audio file: {audio_file}")
                print(f"File exists: {os.path.exists(audio_file)}")
                
                if not os.path.exists(audio_file):
                    raise Exception(f"Audio file not found at {audio_file}")
                    
                return audio_file, song_name
                
            except Exception as e:
                print(f"YouTube-DL error: {str(e)}")
                print("Traceback:", traceback.format_exc())
                return None
                
    except Exception as e:
        print(f"Download error: {str(e)}")
        print("Traceback:", traceback.format_exc())
        return None

def delete_temp_files(audio_file, output_file, mp3_file):
    os.remove(audio_file)
    os.remove(output_file)
    if mp3_file:
        os.remove(mp3_file)

def main():
    st.set_page_config(page_title="Lofi Converter", page_icon=":microphone:", layout="wide")
    
    st.title(":microphone: Lofi Converter")
    st.markdown("# Bookmark new [Website](https://lofi-converter.samevibe.in/)")
    st.info("Tip: Use Headphone for best experience :headphones:")
    youtube_link = st.text_input("Enter the YouTube link 🔗 of the song to convert:", placeholder="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    
    if youtube_link:
        try:
            # Download audio from YouTube link and save as a WAV file
            result = download_youtube_audio(youtube_link)
            print(f"Retrieving YouTube link: {youtube_link}")
            
            if result is not None:
                audio_file, song_name = result

                # Show original audio
                st.write("Original Audio")
                st.audio(audio_file, format="audio/mp3")

                try:
                    # Get user settings for slowedreverb function
                    room_size, damping, wet_level, dry_level, delay, slow_factor = get_user_settings()

                    # Process audio with slowedreverb function
                    output_file = os.path.splitext(audio_file)[0] + "_lofi.wav"
                    print(f"User Settings: {room_size}, {damping}, {wet_level}, {dry_level}, {delay}, {slow_factor}")
                    
                    music.slowedreverb(audio_file, output_file, room_size, damping, wet_level, dry_level, delay, slow_factor)

                    # Show Lofi converted audio
                    st.write("Lofi Converted Audio (Preview)")
                    converted_mp3 = music.msc_to_mp3_inf(output_file)
                    st.audio(converted_mp3, format="audio/mp3")

                    st.download_button("Download MP3", converted_mp3, song_name+"_lofi.mp3")
                    
                    # Clean up temporary files
                    try:
                        delete_temp_files(audio_file, output_file, converted_mp3)
                    except Exception as e:
                        print(f"Error cleaning up files: {e}")
                        
                except Exception as e:
                    st.error(f"Error converting audio: {str(e)}")
                    print(f"Error in audio conversion: {e}")
            else:
                st.error("Failed to download the video. Please check the URL and try again.")
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")
            print(f"Unexpected error in main: {e}")

    # Footer and BuyMeACoffee button
    st.markdown("""
        <h10 style="text-align: center; position: fixed; bottom: 3rem;">Give a ⭐ on <a href="https://github.com/samarthshrivas/LoFi-Converter-GUI"> Github</a> </h10>""",
        unsafe_allow_html=True)
    button = """<script type="text/javascript" src="https://cdnjs.buymeacoffee.com/1.0.0/button.prod.min.js" data-name="bmc-button" data-slug="SamarthShrivas" data-color="#FFDD00" data-emoji="📖" data-font="Cookie" data-text="Buy me a book" data-outline-color="#000000" data-font-color="#000000" data-coffee-color="#ffffff" ></script>"""
    html(button, height=70, width=220)
    st.markdown(
        """
        <style>
            iframe[width="220"] {
                position: fixed;
                bottom: 60px;
                right: 40px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

def get_user_settings():
    advanced_expander = st.expander("Advanced Settings")
    with advanced_expander:
        st.write("Adjust the parameters for the slowedreverb function:")
        room_size = st.slider("Reverb Room Size", min_value=0.1, max_value=1.0, value=0.75, step=0.1)
        damping = st.slider("Reverb Damping", min_value=0.1, max_value=1.0, value=0.5, step=0.1)
        wet_level = st.slider("Reverb Wet Level", min_value=0.0, max_value=1.0, value=0.08, step=0.01)
        dry_level = st.slider("Reverb Dry Level", min_value=0.0, max_value=1.0, value=0.2, step=0.01)
        delay = st.slider("Delay (ms)", min_value=0, max_value=20, value=2)
        slow_factor = st.slider("Slow Factor", min_value=0.0, max_value=0.2, value=0.08, step=0.01)
    return room_size, damping, wet_level, dry_level, delay, slow_factor

@app.options("/convert")
async def options_convert():
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

@app.post("/convert")
async def convert_audio(request: YouTubeRequest):
    try:
        print(f"\n=== Starting conversion request for URL: {request.youtube_link} ===")
        
        result = download_youtube_audio(request.youtube_link)
        if result is None:
            raise HTTPException(status_code=400, detail="Failed to download audio")
            
        audio_file, song_name = result
        print(f"Download successful. Audio file: {audio_file}")
        
        # Read the file and return it
        if not os.path.exists(audio_file):
            raise HTTPException(status_code=500, detail="Generated audio file not found")
            
        with open(audio_file, 'rb') as f:
            audio_data = f.read()
            
        # Clean up
        try:
            os.remove(audio_file)
        except Exception as e:
            print(f"Cleanup error: {str(e)}")
            
        return {
            "audio_data": audio_data,
            "filename": f"{song_name}.mp3"
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Conversion error: {str(e)}")
        print("Traceback:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    ffmpeg_ok = check_ffmpeg()
    return {
        "status": "healthy" if ffmpeg_ok else "unhealthy",
        "ffmpeg_path": FFMPEG_PATH,
        "ffmpeg_exists": os.path.exists(FFMPEG_PATH),
        "ffmpeg_executable": os.access(FFMPEG_PATH, os.X_OK) if os.path.exists(FFMPEG_PATH) else False
    }

if __name__ == "__main__":
    main()