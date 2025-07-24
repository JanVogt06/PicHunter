#!/usr/bin/env python3
"""
Image Downloader - Lädt alle Bilder von einer Webseite herunter
Verwendung: python image_downloader.py https://example.com
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import sys
import argparse
import hashlib
import logging
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import mimetypes


class ImageDownloader:
    def __init__(self, url, output_dir='downloaded_images', max_workers=5):
        self.url = url
        self.output_dir = output_dir
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.downloaded_hashes = set()

        # Logging einrichten
        self.setup_logging()

    def setup_logging(self):
        """Logging-Konfiguration"""
        log_file = f"image_download_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def create_output_directory(self):
        """Erstellt den Ausgabeordner mit Unterordner für die Domain"""
        domain = urlparse(self.url).netloc.replace('www.', '')
        self.output_path = os.path.join(self.output_dir, domain)
        os.makedirs(self.output_path, exist_ok=True)
        self.logger.info(f"Ausgabeordner erstellt: {self.output_path}")

    def get_page_content(self):
        """Lädt den HTML-Inhalt der Seite"""
        try:
            response = self.session.get(self.url, timeout=30)
            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            self.logger.error(f"Fehler beim Abrufen der Seite: {e}")
            sys.exit(1)

    def extract_image_urls(self, soup):
        """Extrahiert alle Bild-URLs aus der Seite"""
        image_urls = set()

        # Standard img tags
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if src:
                image_urls.add(src)

            # srcset für responsive Bilder
            srcset = img.get('srcset') or img.get('data-srcset')
            if srcset:
                for src in srcset.split(','):
                    url = src.strip().split(' ')[0]
                    if url:
                        image_urls.add(url)

        # Picture elements
        for picture in soup.find_all('picture'):
            for source in picture.find_all('source'):
                srcset = source.get('srcset')
                if srcset:
                    url = srcset.split(',')[0].strip().split(' ')[0]
                    image_urls.add(url)

        # CSS Background Images (inline styles)
        for element in soup.find_all(style=True):
            style = element.get('style', '')
            if 'background-image' in style:
                import re
                urls = re.findall(r'url\(["\']?(.*?)["\']?\)', style)
                image_urls.update(urls)

        # Konvertiere relative zu absoluten URLs
        absolute_urls = []
        for url in image_urls:
            absolute_url = urljoin(self.url, url)
            if self.is_valid_image_url(absolute_url):
                absolute_urls.append(absolute_url)

        return list(set(absolute_urls))

    def is_valid_image_url(self, url):
        """Prüft ob die URL wahrscheinlich ein Bild ist"""
        # Prüfe Dateiendung
        path = urlparse(url).path.lower()
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico']

        if any(path.endswith(ext) for ext in image_extensions):
            return True

        # Prüfe auf data URLs
        if url.startswith('data:image'):
            return True

        return False

    def get_file_hash(self, content):
        """Berechnet den Hash des Bildinhalts zur Duplikat-Erkennung"""
        return hashlib.md5(content).hexdigest()

    def generate_filename(self, url, content, index):
        """Generiert einen sinnvollen Dateinamen"""
        # Versuche Original-Dateinamen zu extrahieren
        parsed = urlparse(url)
        original_name = os.path.basename(parsed.path)

        if not original_name or original_name == '/':
            # Fallback: Verwende Content-Type
            content_type = mimetypes.guess_type(url)[0]
            if content_type:
                ext = mimetypes.guess_extension(content_type) or '.jpg'
            else:
                ext = '.jpg'
            original_name = f"image_{index}{ext}"

        # Entferne ungültige Zeichen
        safe_name = "".join(c for c in original_name if c.isalnum() or c in '.-_')

        # Stelle sicher, dass der Name nicht zu lang ist
        if len(safe_name) > 100:
            name, ext = os.path.splitext(safe_name)
            safe_name = name[:100] + ext

        return safe_name

    def download_image(self, url, index):
        """Lädt ein einzelnes Bild herunter"""
        try:
            response = self.session.get(url, timeout=30, stream=True)
            response.raise_for_status()

            content = response.content

            # Prüfe auf Duplikate
            file_hash = self.get_file_hash(content)
            if file_hash in self.downloaded_hashes:
                return f"Duplikat übersprungen: {url}"

            self.downloaded_hashes.add(file_hash)

            # Generiere Dateinamen
            filename = self.generate_filename(url, content, index)
            filepath = os.path.join(self.output_path, filename)

            # Stelle sicher, dass der Dateiname eindeutig ist
            counter = 1
            base, ext = os.path.splitext(filepath)
            while os.path.exists(filepath):
                filepath = f"{base}_{counter}{ext}"
                counter += 1

            # Speichere das Bild
            with open(filepath, 'wb') as f:
                f.write(content)

            file_size = len(content) / 1024  # KB
            return f"Erfolgreich: {filename} ({file_size:.1f} KB)"

        except requests.RequestException as e:
            return f"Fehler bei {url}: {str(e)}"
        except Exception as e:
            return f"Unerwarteter Fehler bei {url}: {str(e)}"

    def download_all_images(self, image_urls):
        """Lädt alle Bilder parallel herunter"""
        self.logger.info(f"Starte Download von {len(image_urls)} Bildern...")

        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Erstelle Tasks
            future_to_url = {
                executor.submit(self.download_image, url, i): (url, i)
                for i, url in enumerate(image_urls)
            }

            # Progress Bar
            with tqdm(total=len(image_urls), desc="Downloading") as pbar:
                for future in as_completed(future_to_url):
                    result = future.result()
                    results.append(result)
                    self.logger.info(result)
                    pbar.update(1)

        return results

    def generate_report(self, results):
        """Erstellt einen Abschlussbericht"""
        successful = sum(1 for r in results if r.startswith("Erfolgreich"))
        duplicates = sum(1 for r in results if "Duplikat" in r)
        failed = sum(1 for r in results if "Fehler" in r)

        report = f"""
        ========== Download Abgeschlossen ==========
        Erfolgreich heruntergeladen: {successful}
        Duplikate übersprungen: {duplicates}
        Fehlgeschlagen: {failed}
        Gesamt verarbeitet: {len(results)}
        Ausgabeordner: {self.output_path}
        ==========================================
        """

        self.logger.info(report)

        # Speichere detaillierten Bericht
        report_file = os.path.join(self.output_path, 'download_report.txt')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"Download Report - {datetime.now()}\n")
            f.write(f"URL: {self.url}\n")
            f.write(report)
            f.write("\nDetaillierte Ergebnisse:\n")
            for result in results:
                f.write(f"{result}\n")

    def run(self):
        """Hauptmethode - führt den kompletten Download-Prozess aus"""
        self.logger.info(f"Starte Image Downloader für: {self.url}")

        # Erstelle Ausgabeordner
        self.create_output_directory()

        # Lade Seiteninhalt
        self.logger.info("Lade Webseite...")
        content = self.get_page_content()

        # Parse HTML
        soup = BeautifulSoup(content, 'html.parser')

        # Extrahiere Bild-URLs
        self.logger.info("Extrahiere Bild-URLs...")
        image_urls = self.extract_image_urls(soup)

        if not image_urls:
            self.logger.warning("Keine Bilder auf der Seite gefunden!")
            return

        self.logger.info(f"{len(image_urls)} Bilder gefunden")

        # Lade Bilder herunter
        results = self.download_all_images(image_urls)

        # Erstelle Bericht
        self.generate_report(results)


def main():
    parser = argparse.ArgumentParser(
        description='Lädt alle Bilder von einer Webseite herunter',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python image_downloader.py https://example.com
  python image_downloader.py https://example.com -o meine_bilder -w 10
  python image_downloader.py https://example.com --max-size 5
        """
    )

    parser.add_argument('url', help='Die URL der Webseite')
    parser.add_argument('-o', '--output', default='downloaded_images',
                        help='Ausgabeordner (Standard: downloaded_images)')
    parser.add_argument('-w', '--workers', type=int, default=5,
                        help='Anzahl paralleler Downloads (Standard: 5)')
    parser.add_argument('--max-size', type=float,
                        help='Maximale Bildgröße in MB (optional)')

    args = parser.parse_args()

    # Validiere URL
    if not args.url.startswith(('http://', 'https://')):
        args.url = 'https://' + args.url

    # Starte Downloader
    downloader = ImageDownloader(args.url, args.output, args.workers)

    try:
        downloader.run()
    except KeyboardInterrupt:
        print("\n\nDownload durch Benutzer abgebrochen!")
        sys.exit(0)
    except Exception as e:
        print(f"\nFehler: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()