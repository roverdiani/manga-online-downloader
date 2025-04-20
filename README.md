# 📚 Manga Online Downloader

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
[![Licence](https://img.shields.io/github/license/Ileriayo/markdown-badges?style=for-the-badge)](./LICENSE)

A Python script to download manga chapters from MangaOnline.biz with progress tracking and CBZ packaging.

## Notice about using this script
This script is provided as a free tool to help manga fans conveniently access their favorite series. Please use it responsibly by:

- Respecting MangaOnline.biz's terms of service
- Only downloading content you're personally authorized to access
- Supporting manga creators through official releases when possible

While I've made this tool to be helpful, I can't guarantee how it's used. **The script simply automates what you could do manually in a browser.**

***P.S. Consider buying volumes or subscribing to official sources to support the artists you love.***

##  Features

- **Progress Tracking**
- **Flexible Download Options:**
  - Download single chapter or entire series
  - Start from specific chapter number

- **Efficient Packaging**
  - Automatic CBZ file creation 
  - Optional folder cleanup

- **Robust Performance**
   - Multithreaded downloads 
   - Automatic retries for failed downloads 
   - Rate limiting

## Installation
```bash
 git clone https://github.com/roverdiani/manga-online-downloader.git
 cd manga-online-downloader
 pip install -r requirements.txt
```

## Virtual Environment Setup (Recommended)

For isolated dependency management:
```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run script
python manga_downloader.py

# Deactivate when done
deactivate
```

## Usage
```bash
python manga_downloader.py
```

Interactive prompts will guide you through.

## Configuration

Customize through the interactive menu or modify these defaults in the code:
```python
# Default settings (configurable)
output_folder = "manga_downloads"    # Download location
retry_count = 3                      # Download retry attempts
delay_between_requests = 1           # Seconds between requests
```

## Output Structure

```manga_downloads/
└─ Manga_Name/
   ├─ Chapter_01/
   │  ├─ 0001.jpg
   │  └─ ...
   ├─ Chapter_01.cbz
   └─ ...
```

## Limitations
 - Requires stable internet connection
 - Subject to website changes (DOM structure)
 - Rate limits enforced by Manga Online

## Contributing
Contributions welcome! Please open an issue for:
 - Bug reports
 - Feature requests
 - Website structure updates

### Happy Reading! 📖