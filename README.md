# PicHunter 🖼️

A powerful Python tool for downloading all images from any website. Features parallel downloads, duplicate detection, and comprehensive image extraction from various sources.

## Features ✨

- **🚀 Parallel Downloads** - Configurable multi-threaded downloading for maximum speed
- **🔍 Comprehensive Image Detection**
  - Standard `<img>` tags
  - Lazy-loaded images (`data-src`, `data-lazy-src`)
  - Responsive images (`srcset`)
  - `<picture>` elements
  - CSS background images (inline styles)
- **🛡️ Smart Duplicate Detection** - MD5 hash-based deduplication
- **📊 Real-time Progress Tracking** - Visual progress bar with tqdm
- **📁 Automatic Organization** - Images sorted by domain
- **📝 Detailed Logging** - Comprehensive logs and download reports
- **🔄 Robust Error Handling** - Graceful handling of failed downloads
- **⚙️ Highly Configurable** - Command-line arguments for customization

## Requirements 📋

- Python 3.6 or higher
- pip (Python package manager)

## Installation 🔧

1. Clone the repository:
```bash
git clone https://github.com/JanVogt06/PicHunter.git
cd PicHunter
```

2. Create a virtual environment (recommended):
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/macOS
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install requests beautifulsoup4 tqdm
```

## Usage 🚀

### Basic Usage
```bash
python image_downloader.py https://example.com
```

### Advanced Options
```bash
# Custom output directory
python image_downloader.py https://example.com -o my_images

# Increase parallel downloads (default: 5)
python image_downloader.py https://example.com -w 10

# Show help
python image_downloader.py -h
```

### Command Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `url` | The URL of the website to scrape | Required |
| `-o`, `--output` | Output directory for downloaded images | `downloaded_images` |
| `-w`, `--workers` | Number of parallel download threads | `5` |

## Output Structure 📂

```
downloaded_images/
└── example.com/
    ├── image_1.jpg
    ├── image_2.png
    ├── logo.svg
    ├── download_report.txt
    └── image_download_20250124_143022.log
```

## Example Output 📊

```
========== Download Completed ==========
Successfully downloaded: 42
Duplicates skipped: 7
Failed: 0
Total processed: 51
Output folder: downloaded_images/example.com
======================================
```

## Features in Detail 🔍

### Duplicate Detection
PicHunter uses MD5 hashing to detect and skip duplicate images, even if they have different filenames on the server.

### Smart Filename Generation
- Preserves original filenames when possible
- Sanitizes filenames for filesystem compatibility
- Adds incremental numbers to prevent overwrites

### Comprehensive Logging
- Console output with real-time progress
- Detailed log files for each session
- Download report with statistics

## Limitations ⚠️

- Cannot download images from pages requiring authentication
- JavaScript-rendered content requires additional tools (z.B., Selenium)

## License 📄

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments 🙏

- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) for HTML parsing
- [Requests](https://requests.readthedocs.io/) for HTTP operations
- [tqdm](https://github.com/tqdm/tqdm) for progress bars

## Author ✍️

**Jan Vogt** - [JanVogt06](https://github.com/JanVogt06)

---

⭐ If you find this tool useful, please consider giving it a star on GitHub!