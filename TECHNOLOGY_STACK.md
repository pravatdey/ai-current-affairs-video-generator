# Technology Stack Overview

**Project:** AI-Powered Current Affairs Video Generator
**Purpose:** Fully automated pipeline that scrapes news, generates AI scripts, produces professional videos with TTS & avatar, and uploads to YouTube — optimized for UPSC exam preparation.

---

## Languages & Runtime

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.9+ | Core application language |
| YAML | — | Configuration files |
| JSON | — | Data serialization & credentials |
| SQL (SQLite) | — | Local database for article & video tracking |

---

## AI & Machine Learning

| Technology | Details | Purpose |
|------------|---------|---------|
| **Groq API** | llama-3.3-70b-versatile (Free tier) | Cloud-based LLM for script generation |
| **Ollama** | Llama2 (local, optional) | Local LLM alternative for privacy |
| **LangChain** | v0.1+ | LLM orchestration & prompt management |
| **PyTorch** | v2.0+ | Deep learning framework for avatar generation |
| **OpenCV** | v4.8+ | Computer vision & image processing |
| **SadTalker** | External (optional) | Realistic talking-head avatar generation |
| **Wav2Lip** | External (optional) | Audio-driven lip-sync technology |
| **GFPGAN** | v1.3+ (optional) | AI face enhancement for avatar quality |

---

## Text-to-Speech (TTS)

| Technology | Details | Purpose |
|------------|---------|---------|
| **Microsoft Edge TTS** | Free, multi-language | Natural-sounding voice synthesis |
| **pydub** | v0.25+ | Audio post-processing & effects |
| **librosa** | v0.10+ | Audio analysis & feature extraction |

### Supported Languages & Voices
- English (Indian) — `en-IN-PrabhatNeural`
- Hindi — `hi-IN-MadhurNeural`
- Tamil — `ta-IN-ValluvarNeural`
- Telugu — `te-IN-ShrutiNeural`
- Bengali, Marathi, Gujarati, Kannada, Malayalam (extended)

---

## Video Production

| Technology | Details | Purpose |
|------------|---------|---------|
| **MoviePy** | v1.0.3 | Video composition & editing |
| **FFmpeg** | System dependency | Video/audio encoding (H.264, AAC) |
| **Pillow (PIL)** | v10.0+ | Image manipulation & thumbnail generation |
| **NumPy** | v1.24+ | Array operations for image/audio data |
| **imageio** | v2.31+ | Image I/O with FFmpeg integration |

### Video Output Specs
- **Resolution:** 1280×720 (HD)
- **Frame Rate:** 30 FPS
- **Codec:** H.264 (libx264)
- **Format:** MP4
- **Bitrate:** 1500 kbps

---

## Web Scraping & Data Processing

| Technology | Details | Purpose |
|------------|---------|---------|
| **feedparser** | v6.0+ | RSS/Atom feed parsing |
| **BeautifulSoup4** | v4.12+ | HTML parsing & web scraping |
| **newspaper3k** | v0.2.8+ | Article content extraction |
| **requests** | v2.31+ | HTTP requests |
| **lxml** | v4.9+ | XML/HTML processing |

> Aggregates from **20+ news sources** including The Hindu, Indian Express, PIB, BBC, Reuters, and more.

---

## Cloud Services & APIs

| Service | Purpose |
|---------|---------|
| **Groq API** | Free-tier LLM inference (30 req/min) |
| **YouTube Data API v3** | Video upload, metadata & thumbnail management |
| **Google Drive API** | PDF notes storage & shareable links |
| **Microsoft Edge TTS** | Free text-to-speech |
| **Telegram Bot API** | Status notifications (optional) |

---

## Database & ORM

| Technology | Purpose |
|------------|---------|
| **SQLAlchemy** v2.0+ | ORM for database operations |
| **SQLite** | Lightweight local database |

### Database Tables
- **Article** — Tracks scraped articles (SHA256 deduplication)
- **GeneratedVideo** — Tracks generated & uploaded videos

---

## PDF Generation

| Technology | Purpose |
|------------|---------|
| **ReportLab** v4.0+ | Professional PDF creation |

> Generates **Drishti IAS SARAANSH-style** study notes with structured layouts, tables, and UPSC-focused formatting.

---

## Scheduling & Automation

| Technology | Purpose |
|------------|---------|
| **APScheduler** v3.10+ | In-app job scheduling (Cron triggers) |
| **GitHub Actions** | CI/CD daily automation pipeline |

### GitHub Actions Workflow
- **Schedule:** Daily at 10:00 AM IST (4:30 AM UTC)
- **Runtime:** Ubuntu with Python 3.11, FFmpeg, ImageMagick
- **Artifacts:** Video files uploaded as build artifacts
- **Notifications:** Telegram alerts on success/failure

---

## Authentication & Security

| Technology | Purpose |
|------------|---------|
| **Google OAuth 2.0** | YouTube & Drive API authentication |
| **python-dotenv** | Secure environment variable management |
| **.env files** | API keys & credentials (not committed to repo) |

---

## Logging & Monitoring

| Technology | Purpose |
|------------|---------|
| **Loguru** v0.7+ | Advanced structured logging |
| **tqdm** v4.66+ | Progress bars for long-running tasks |

---

## Testing

| Technology | Purpose |
|------------|---------|
| **pytest** v7.4+ | Unit testing framework |
| **pytest-asyncio** v0.21+ | Async test support for TTS & scraping |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions (Daily Cron)               │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────────┐
│  News Scraper │───▶│ Script Gen   │───▶│  Text-to-Speech  │
│  (RSS + Web)  │    │ (Groq LLM)  │    │  (Edge TTS)      │
└──────────────┘    └──────────────┘    └────────┬─────────┘
                           │                      │
                           ▼                      ▼
                    ┌──────────────┐    ┌──────────────────┐
                    │  PDF Notes   │    │  Avatar Generator │
                    │ (ReportLab)  │    │ (SadTalker/Wav2Lip)│
                    └──────┬───────┘    └────────┬─────────┘
                           │                      │
                           ▼                      ▼
                    ┌──────────────┐    ┌──────────────────┐
                    │ Google Drive │    │ Video Composer    │
                    │   Upload     │    │ (MoviePy+FFmpeg)  │
                    └──────────────┘    └────────┬─────────┘
                                                  │
                                                  ▼
                                        ┌──────────────────┐
                                        │  YouTube Upload   │
                                        │  (API v3 + OAuth) │
                                        └──────────────────┘
```

---

## System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **Python** | 3.9 | 3.11 |
| **RAM** | 8 GB | 16 GB |
| **Storage** | 50 GB | 100 GB |
| **GPU** | Not required | NVIDIA GTX 1660+ (for avatar) |
| **OS** | Windows / Linux / macOS | Ubuntu 22.04 LTS |
| **FFmpeg** | Required | Latest stable |
| **Internet** | Required | Broadband |

---

## Key Highlights

- **100% Automated** — From news scraping to YouTube upload, zero manual intervention
- **Zero API Cost** — Uses free-tier Groq API & Microsoft Edge TTS
- **Multi-Language** — Supports 9+ Indian languages
- **UPSC Optimized** — Content filtered & structured for exam relevance
- **Production Ready** — Database tracking, error handling, retry logic & Telegram alerts
- **Scalable** — Modular pipeline architecture, easy to extend

---

*Built with open-source technologies and free-tier cloud services for maximum accessibility.*
