import React, { useState } from 'react';
import './LofiConverter.css';

const LofiConverter = () => {
  const [youtubeLink, setYoutubeLink] = useState('');
  const [isConverting, setIsConverting] = useState(false);
  const [convertedFile, setConvertedFile] = useState(null);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsConverting(true);
    setError('');
    setConvertedFile(null);

    try {
      console.log('Starting conversion for URL:', youtubeLink);
      
      const response = await fetch('http://localhost:8000/convert', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({ youtube_link: youtubeLink }),
      });

      console.log('Response status:', response.status);
      
      const data = await response.json();
      console.log('Response data:', data);

      if (!response.ok) {
        throw new Error(data.detail || 'Conversion failed');
      }

      if (!data.audio_data) {
        throw new Error('No audio data received');
      }

      const audioArray = Uint8Array.from(atob(data.audio_data), c => c.charCodeAt(0));
      const audioBlob = new Blob([audioArray], { type: 'audio/mp3' });
      const url = window.URL.createObjectURL(audioBlob);
      
      setConvertedFile({
        url,
        filename: data.filename || 'converted.mp3'
      });
      
    } catch (err) {
      console.error('Conversion error:', err);
      setError(err.message || 'Failed to convert video. Please make sure the YouTube link is valid and the video is under 10 minutes.');
    } finally {
      setIsConverting(false);
    }
  };

  return (
    <div className="lofi-converter">
      <div className="converter-container">
        <div className="header">
          <h1>🎵 Lofi Converter</h1>
          <p className="tip">🎧 Use Headphones for best experience</p>
        </div>

        <form onSubmit={handleSubmit} className="converter-form">
          <div className="input-group">
            <input
              type="text"
              value={youtubeLink}
              onChange={(e) => setYoutubeLink(e.target.value)}
              placeholder="Enter YouTube link..."
              className="youtube-input"
              required
            />
            <button 
              type="submit" 
              className="convert-button"
              disabled={isConverting}
            >
              {isConverting ? 'Converting...' : 'Convert to Lofi'}
            </button>
          </div>
        </form>

        {error && <div className="error-message">{error}</div>}

        {convertedFile && (
          <div className="result-section">
            <h2>Your Lofi Version is Ready! 🎉</h2>
            <audio controls className="audio-player">
              <source src={convertedFile.url} type="audio/mpeg" />
              Your browser does not support the audio element.
            </audio>
            <a 
              href={convertedFile.url} 
              download={convertedFile.filename}
              className="download-button"
            >
              Download MP3
            </a>
          </div>
        )}

        <div className="github-section">
          <a 
            href="https://github.com/EsstafaSoufiane/LoFi-Converter-GUI" 
            target="_blank" 
            rel="noopener noreferrer"
            className="github-link"
          >
            ⭐ Star on GitHub
          </a>
        </div>
      </div>
    </div>
  );
};

export default LofiConverter;
