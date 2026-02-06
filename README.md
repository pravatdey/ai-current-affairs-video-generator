# AI Current Affairs Video Generator

An automated AI-powered system that generates daily current affairs videos with a realistic talking avatar, complete with text-to-speech narration, and uploads them to YouTube automatically.

## Features

- **News Scraping**: Automatically scrapes news from 20+ Indian and International sources
- **AI Script Generation**: Uses LLM (Groq/Ollama) to create engaging news scripts
- **Multi-Language Support**: English, Hindi, Tamil, Telugu support
- **Text-to-Speech**: High-quality voices using Microsoft Edge TTS (Free)
- **Avatar Video**: Realistic talking head generation
- **Video Composition**: Professional video with intros, outros, and overlays
- **Auto Thumbnails**: YouTube-optimized thumbnail generation
- **YouTube Upload**: Automatic upload with SEO-optimized metadata
- **Daily Scheduling**: Run automatically at scheduled times

## Quick Start

### 1. Clone and Setup

```bash
cd "d:/Personal_projects/Ai-current affairs-model"
python setup.py
```

### 2. Get API Keys

**Groq API (Free - Required for LLM)**
1. Go to [https://console.groq.com/](https://console.groq.com/)
2. Sign up for free
3. Create an API key
4. Add to `.env` file: `GROQ_API_KEY=your_key_here`

**YouTube API (Required for uploading)**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable "YouTube Data API v3"
4. Create OAuth 2.0 credentials (Desktop app)
5. Download JSON and save as `config/client_secrets.json`

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Your First Video

```bash
# Generate video (test mode - uploads as private)
python main.py --test

# Generate without uploading
python main.py --no-upload

# Generate in Hindi
python main.py --language hi
```

## Project Structure

```
ai-current-affairs-video/
├── config/
│   ├── settings.yaml         # Main configuration
│   ├── news_sources.yaml     # News source URLs
│   ├── youtube_config.yaml   # YouTube settings
│   └── client_secrets.json   # YouTube OAuth (you create this)
├── src/
│   ├── scraper/              # News scraping module
│   ├── script_generator/     # LLM script generation
│   ├── tts/                  # Text-to-speech
│   ├── avatar/               # Talking head generation
│   ├── video/                # Video composition
│   ├── youtube/              # YouTube upload
│   └── utils/                # Utilities
├── assets/
│   ├── avatars/              # Avatar images
│   ├── backgrounds/          # Video backgrounds
│   └── music/                # Background music
├── output/
│   ├── audio/                # Generated audio
│   ├── videos/               # Generated videos
│   └── thumbnails/           # Generated thumbnails
├── main.py                   # Main pipeline
├── scheduler.py              # Daily scheduler
└── requirements.txt
```

## Usage

### Command Line Options

```bash
# Basic usage
python main.py

# Options
python main.py --language en     # Language: en, hi, ta, te
python main.py --no-upload       # Don't upload to YouTube
python main.py --test            # Upload as private (testing)
python main.py --no-scrape       # Use existing articles only

# Run daily scheduler
python scheduler.py --time 06:00 --timezone "Asia/Kolkata"

# Run once immediately
python scheduler.py --once
```

### Testing Individual Components

```bash
# Test news scraping
python -m src.scraper.news_aggregator --test

# Test TTS
python -m src.tts.tts_manager --test --lang en

# Test thumbnail generation
python -m src.video.thumbnail --title "Test" --output output/test.png

# Test YouTube authentication
python -m src.youtube.uploader --test
```

## Configuration

### settings.yaml

Key settings you can customize:

```yaml
video:
  duration_min: 5           # Minimum video duration
  duration_max: 15          # Maximum video duration
  resolution:
    width: 1920
    height: 1080

languages:
  default: "en"

llm:
  provider: "groq"          # or "ollama" for local

schedule:
  time: "06:00"
  timezone: "Asia/Kolkata"
```

### news_sources.yaml

Add or modify news sources:

```yaml
indian_sources:
  - name: "Your Source"
    type: "rss"
    enabled: true
    language: "en"
    url: "https://example.com/feed.xml"
```

## Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 16+ GB |
| GPU | - | NVIDIA GTX 1660+ |
| Storage | 50 GB | 100+ GB SSD |

*Note: GPU significantly speeds up avatar generation but is optional.*

## API Costs

This project is designed to be **100% free**:

| Service | Cost | Notes |
|---------|------|-------|
| Groq API | Free | 30 requests/minute free tier |
| Edge TTS | Free | Microsoft Edge voices |
| YouTube API | Free | Standard quota sufficient |

## Troubleshooting

### "Groq API key required"
- Get free key at [https://console.groq.com/](https://console.groq.com/)
- Add to `.env`: `GROQ_API_KEY=your_key`

### "No articles found"
- Check internet connection
- Verify news sources in `config/news_sources.yaml`
- Some sources may be temporarily unavailable

### "YouTube authentication failed"
- Ensure `config/client_secrets.json` exists
- Delete `config/youtube_token.json` and re-authenticate
- Check Google Cloud Console for API quota

### "FFmpeg not found"
- Install FFmpeg: [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
- Add to system PATH

## Advanced Setup

### Using Local LLM (Ollama)

1. Install Ollama: [https://ollama.ai/](https://ollama.ai/)
2. Pull a model: `ollama pull llama2`
3. Update `config/settings.yaml`:
   ```yaml
   llm:
     provider: "ollama"
     ollama:
       model: "llama2"
   ```

### Using SadTalker (Better Avatar)

1. Clone: `git clone https://github.com/OpenTalker/SadTalker`
2. Install dependencies
3. Download models
4. Set environment variable: `SADTALKER_PATH=/path/to/SadTalker`

## License

This project is for educational purposes. Please respect:
- News source terms of service
- YouTube Community Guidelines
- API usage policies

## Support

For issues and feature requests, please create an issue in this repository.

---

**Built with Python, powered by AI**
