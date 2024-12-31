import os
import streamlit as st
import music
import yt_dlp
import uuid
from streamlit.components.v1 import html, components
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

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

# Function to delete temporary audio files
def delete_temp_files(audio_file, output_file, mp3_file):
    os.remove(audio_file)
    os.remove(output_file)
    if mp3_file:
        os.remove(mp3_file)


@st.cache_data(show_spinner=False, max_entries=5)
def isDownlaodable(youtube_link):
    try:
        with yt_dlp.YoutubeDL({'format': 'bestaudio', "quiet":True, "noplaylist":True}) as ydl:
            info_dict = ydl.extract_info(youtube_link, download=False)
            duration = info_dict.get('duration', 0)
            
            if duration and duration <= 600:
                return True
            else:
                st.error("Make sure song is less than 10 minutes")
                return False

    except Exception as e:
        st.error(f"Error checking video: {str(e)}")
        print(f"ERROR: {e} ==> {youtube_link}")
        return False


# Function to download YouTube audio and save as a WAV file
@st.cache_data(ttl=2)
def download_youtube_audio(youtube_link):
    uu = str(uuid.uuid4())
    
    if not youtube_link.startswith(('http://', 'https://')):
        st.error("Please enter a valid YouTube URL")
        return None

    if isDownlaodable(youtube_link):
        try:
            os.makedirs('uploaded_files', exist_ok=True)
            with yt_dlp.YoutubeDL({
                'format': 'bestaudio/best', 
                'outtmpl': 'uploaded_files/' + uu + '.%(ext)s', 
                "quiet": True, 
                "noplaylist": True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                }]
            }) as ydl:
                info_dict = ydl.extract_info(youtube_link, download=True)
                audio_file = ydl.prepare_filename(info_dict)
                audio_file = os.path.splitext(audio_file)[0] + '.wav'  # Update extension to .wav
                song_name = info_dict['title']
                
            print(f"Downloaded YouTube link: {youtube_link} ==> {song_name}")
            mp3_file_base = music.msc_to_mp3_inf(audio_file)
            return (audio_file, mp3_file_base, song_name)
        except Exception as e:
            st.error(f"Error downloading video: {str(e)}")
            print(f"ERROR: {e} ==> {youtube_link} in download_youtube_audio")
            return None
    return None

# Main function for the web app
def main():
    st.set_page_config(page_title="Lofi Converter", page_icon=":microphone:", layout="wide")
    
    st.title(":microphone: Lofi Converter")
    st.markdown("# Bookmark new [Website](https://lofi-converter.samevibe.in/)")
    st.info("Tip: Use Headphone for best experience :headphones:")
    youtube_link = st.text_input("Enter the YouTube link 🔗 of the song to convert:", placeholder="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    
    if youtube_link:
        try:
            # Download audio from YouTube link and save as a WAV file (using cached function)
            result = download_youtube_audio(youtube_link)
            print(f"Retrieving YouTube link: {youtube_link}")
            
            if result is not None:
                audio_file, mp3_base_file, song_name = result

                # Show original audio
                st.write("Original Audio")
                st.audio(mp3_base_file, format="audio/mp3")

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
                        delete_temp_files(audio_file, output_file, mp3_base_file)
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

# Function to get user settings
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
        result = download_youtube_audio(request.youtube_link)
        if result is None:
            raise HTTPException(status_code=400, detail="Failed to download or convert video")
            
        audio_file, mp3_base_file, song_name = result
        
        # Get default settings
        room_size, damping, wet_level, dry_level, delay, slow_factor = 0.75, 0.5, 0.08, 0.2, 2, 0.08
        
        # Process audio with slowedreverb function
        output_file = os.path.splitext(audio_file)[0] + "_lofi.wav"
        music.slowedreverb(audio_file, output_file, room_size, damping, wet_level, dry_level, delay, slow_factor)
        
        # Convert to MP3
        converted_mp3 = music.msc_to_mp3_inf(output_file)
        
        # Clean up files
        try:
            delete_temp_files(audio_file, output_file, mp3_base_file)
        except Exception as e:
            print(f"Error cleaning up files: {e}")
        
        return {"audio_data": converted_mp3, "filename": f"{song_name}_lofi.mp3"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    main()