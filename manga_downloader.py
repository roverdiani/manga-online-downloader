#!/usr/bin/env python3
import os
import re
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from urllib.error import URLError
from urllib.parse import urlparse
import inquirer
import mechanize
from bs4 import BeautifulSoup
from tqdm import tqdm


def validate_url(_, current):
    """Validate the manga URL format"""
    pattern = r'^https://mangaonline\.biz/manga/[^/]+/$'
    return bool(re.fullmatch(pattern, current))


def get_user_input():
    """Get user input using inquirer"""
    questions = [
        inquirer.Text('manga_url',
                      message='Enter the Manga Online URL',
                      validate=validate_url),
        inquirer.Confirm('create_cbz',
                         message='Create CBZ files for chapters?',
                         default=True),
        inquirer.Confirm('clean_folders',
                         message='Remove image folders after CBZ creation?',
                         default=False),
        inquirer.Confirm('download_all',
                         message='Download all chapters?',
                         default=True),
        inquirer.Text('start_chapter',
                      message='Start from chapter number (leave empty for first)',
                      default=""),
        inquirer.Text('max_workers',
                      message='Number of concurrent downloads (1-10)',
                      default="3",
                      validate=lambda _, x: x.isdigit() and 1 <= int(x) <= 10)
    ]
    return inquirer.prompt(questions)


def create_directory(path):
    """Create directory if it doesn't exist"""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating directory {path}: {e}", file=sys.stderr)
        return False

def get_file_extension(url):
    """Extract file extension from URL"""
    path = urlparse(url).path
    return os.path.splitext(path)[1][1:].lower()


def get_manga_title(soup):
    """Extract manga title from page"""
    try:
        return soup.select_one('div.sheader > div > h1').text.strip()
    except AttributeError:
        print("Could not find manga title on page", file=sys.stderr)
        sys.exit(1)


def get_chapters(soup):
    """Get list of all chapters"""
    chapters = []
    chapter_tags = soup.find_all('div', 'episodiotitle')

    for tag in chapter_tags:
        link = tag.find('a')
        if link:
            title = re.sub(r'\s*\d{2}/\d{2}/\d{4}$', '', link.text).strip()
            url = link.get('href')
            if url and title:
                chapters.append(Chapter(title, url))

    return list(reversed(chapters))  # Return in chronological order


def sanitize_filename(name):
    """Sanitize filenames to remove invalid characters"""
    return re.sub(r'[<>:"/\\|?*]', '_', name).strip()


def create_chapter_cbz(chapter, chapter_folder, output_path, clean, show_messages):
    """Create CBZ archive from chapter folder"""
    if show_messages:
        print(f"Creating CBZ for {chapter.title}")

    cbz_path = os.path.join(output_path, sanitize_filename(chapter.title))

    try:
        shutil.make_archive(cbz_path, 'zip', chapter_folder)
        os.rename(f"{cbz_path}.zip", f"{cbz_path}.cbz")

        if clean:
            shutil.rmtree(chapter_folder)
    except OSError as e:
        print(f"Error creating CBZ: {e}", file=sys.stderr)


class MangaDownloader:
    def __init__(self):
        self.output_folder = "manga_downloads"
        self.retry_count = 3
        self.delay_between_requests = 1 # seconds
        self.browser = mechanize.Browser()
        self.browser.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')]
        self.browser.set_handle_robots(False)
        self.progress_lock = Lock()  # Lock for thread-safe progress updates
        self.global_progress = None  # Will hold our master progress bar

    def download_with_retry(self, url, filename):
        """Download file with retry mechanism"""
        for attempt in range(self.retry_count):
            try:
                response = self.browser.open(url)
                with open(filename, 'wb') as f:
                    f.write(response.read())
                return True
            except (URLError, mechanize.HTTPError) as e:
                if attempt == self.retry_count - 1:
                    print(f"Failed to download {url} after {self.retry_count} attempts: {e}", file=sys.stderr)
                    return False
                time.sleep(self.delay_between_requests)
                return None
        return None

    def parse_manga_page(self, url):
        """Parse the manga main page"""
        print(f"Fetching manga page: {url}")
        try:
            html = self.browser.open(url)
            return BeautifulSoup(html, 'html.parser')
        except Exception as e:
            print(f"Error parsing manga page: {e}", file=sys.stderr)
            sys.exit(1)

    def get_chapter_images(self, url):
        """Get all image URLs from a chapter page"""
        try:
            html = self.browser.open(url)
            soup = BeautifulSoup(html, 'html.parser')
            return [img.get('src') for img in soup.select('div.content > p > img') if img.get('src')]
        except Exception as e:
            print(f"Error getting images for chapter {url}: {e}", file=sys.stderr)
            return []

    def download_chapter(self, chapter, output_path, create_cbz, clean_folder, single_download=True):
        """Download all images for a single chapter"""
        chapter_folder = os.path.join(output_path, sanitize_filename(chapter.title))

        if os.path.exists(chapter_folder):
            if single_download:
                print(f"Chapter '{chapter.title}' already exists - skipping")
            return True

        if single_download:
            print(f"\nDownloading chapter: {chapter.title}")

        images = self.get_chapter_images(chapter.url)

        if not images:
            if single_download:
                print(f"No images found for chapter {chapter.title}")
            return False

        if not create_directory(chapter_folder):
            return False

        if single_download:
            with tqdm(total=len(images), desc=chapter.title[:20], leave=False) as pbar:
                for i, img_url in enumerate(images):
                    ext = get_file_extension(img_url) or 'jpg'
                    filename = os.path.join(chapter_folder, f"{i:04d}.{ext}")
                    if not self.download_with_retry(img_url, filename):
                        return False
                    pbar.update(1)
                    # Update global progress if it exists
                    if self.global_progress:
                        with self.progress_lock:
                            self.global_progress.update(1)
        else:
            for i, img_url in enumerate(images):
                ext = get_file_extension(img_url) or 'jpg'
                filename = os.path.join(chapter_folder, f"{i:04d}.{ext}")
                if not self.download_with_retry(img_url, filename):
                    return False
                if self.global_progress:
                    with self.progress_lock:
                        self.global_progress.update(1)

        if create_cbz:
            create_chapter_cbz(chapter, chapter_folder, output_path, clean_folder, single_download)

        return True

    def run(self):
        print("\n=== Manga Online Downloader ===\n")

        answers = get_user_input()
        if not answers:
            return

        if not create_directory(self.output_folder):
            return

        soup = self.parse_manga_page(answers['manga_url'])
        manga_title = get_manga_title(soup)
        manga_folder = os.path.join(self.output_folder, sanitize_filename(manga_title))

        if not create_directory(manga_folder):
            return

        chapters = get_chapters(soup)
        if not chapters:
            print("No chapters found", file=sys.stderr)
            return

        if answers['start_chapter']:
            try:
                start_num = float(answers['start_chapter'])
                chapters = [ch for ch in chapters if float(re.search(r'\d+\.?\d*', ch.title).group()) >= start_num]
            except (ValueError, AttributeError):
                print("Invalid chapter number format", file=sys.stderr)
                return

        if not answers['download_all']:
            chapters = [chapters[0]]  # Download only first chapter

        max_workers = min(int(answers['max_workers']), 10)
        total_images = sum(len(self.get_chapter_images(ch.url)) for ch in chapters)

        if max_workers > 1:
            with tqdm(total=total_images, desc="Total Progress") as self.global_progress:
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = []
                    for chapter in chapters:
                        futures.append(executor.submit(
                            self.download_chapter,
                            chapter,
                            manga_folder,
                            answers['create_cbz'],
                            answers['clean_folders'],
                            single_download=False
                        ))

                    for future in as_completed(futures):
                        if not future.result():
                            print("Some downloads failed", file=sys.stderr)
        else:
            for chapter in chapters:
                success = self.download_chapter(
                    chapter,
                    manga_folder,
                    answers['create_cbz'],
                    answers['clean_folders'],
                    single_download=True
                )
                if not success:
                    print(f"Failed to download chapter {chapter.title}", file=sys.stderr)

        print("\nDownload completed!")

class Chapter:
    """Simple class to store chapter information"""

    def __init__(self, title, url):
        self.title = title
        self.url = url

if __name__ == "__main__":
    try:
        downloader = MangaDownloader()
        downloader.run()
    except KeyboardInterrupt:
        print("\nDownload canceled by user")
        sys.exit(1)