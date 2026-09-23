import os
import sys
import time
import json
import re
import cloudscraper
import requests.cookies
import zipfile
import inquirer
import img2pdf
import shutil
import tempfile
from pathlib import Path
from PIL import Image
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.firefox import GeckoDriverManager
from urllib.parse import urljoin, quote

# --- Цвета и Стили ---
CYAN = '\033[96m'
YELLOW = '\033[93m'
GREY = '\033[90m'
MAGENTA_BG = '\033[45m'
BLACK_FG = '\033[30m'
BOLD = '\033[1m'
RED = '\033[91m'
GREEN = '\033[92m'
ENDC = '\033[0m'
SEPARATOR = f"\n{GREY}────────────────────────────────────────────────────────────{ENDC}"

def clear_console():
    # Use ANSI escape codes for better compatibility with inquirer
    # \033[2J - Clear entire screen
    # \033[H - Move cursor to home position (top-left)
    if os.name == 'nt':
        os.system('cls')
    else:
        print('\033[2J\033[H', end='', flush=True)

def print_menu():
    title = f"{MAGENTA_BG}{BLACK_FG}{BOLD} COM-X.LIFE Downloader{ENDC}"
    author = f"{BOLD}Fork: https://github.com/Forsash3451k/comx-downloader{ENDC}"
    print(f"\n{title}  {author}\n")

class ComXLifeDownloader:
    def __init__(self, browser_choice='chrome', debug=False):
        self.debug = debug
        self.base_url = "https://com-x.life"
        self.session = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False},
            delay=1
        )
        self.cookies = {}
        self.browser_choice = browser_choice
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': self.base_url
        }

    def get_cookies_via_selenium(self):
        print(SEPARATOR)
        print("АВТОРИЗАЦИЯ")
        driver = None
        browser_name_display = self.browser_choice.capitalize()
        try:
            if self.browser_choice == 'chrome':
                chrome_options = ChromeOptions()
                chrome_options.add_argument("--disable-blink-features=AutomationControlled")
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                service = ChromeService(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
            elif self.browser_choice == 'firefox':
                ff_options = FirefoxOptions()
                ff_options.set_preference("dom.webdriver.enabled", False)
                ff_options.set_preference('useAutomationExtension', False)
                ff_options.set_preference("general.useragent.override", self.headers['User-Agent'])
                service = FirefoxService(GeckoDriverManager().install())
                driver = webdriver.Firefox(service=service, options=ff_options)
            else:
                 print(f"✗ Неподдерживаемый браузер: {self.browser_choice}")
                 return False
        except Exception as e:
            print(f"✗ Ошибка запуска {browser_name_display}: {e}")
            print(f"\nПопробуйте установить {browser_name_display} или проверьте { 'ChromeDriver' if self.browser_choice == 'chrome' else 'GeckoDriver' }")
            return False
        if not driver:
             print("✗ Не удалось инициализировать драйвер")
             return False
        try:
            driver.get(self.base_url)
            print(f"\n⚠ Сейчас {browser_name_display} открыт")
            print("📝 Войдите в свой аккаунт на сайте com-x.life")
            print("⏳ Скрипт *автоматически* продолжит работу после обнаружения входа...")
            while True:
                try:
                    _ = driver.current_url
                    if driver.get_cookie("dle_user_id"):
                        print("\n✓ Обнаружен вход! Получаем cookies...")
                        cookies_list = driver.get_cookies()
                        for cookie in cookies_list:
                            self.cookies[cookie['name']] = cookie['value']
                        # Create a new cookie jar to completely replace session cookies (avoids duplicates)
                        new_jar = requests.cookies.RequestsCookieJar()
                        for name, value in self.cookies.items():
                            new_jar.set(name, value, domain='com-x.life')
                        self.session.cookies = new_jar
                        if self.cookies:
                            self.save_cookies()
                            print(f"✓ Получено {len(self.cookies)} cookies\n")
                            return True
                        else:
                            print("✗ Не удалось извлечь cookies, хотя вход был обнаружен.")
                            return False
                    time.sleep(1)
                except Exception:
                    print("\n✗ Браузер был закрыт пользователем до завершения авторизации.")
                    return False
        except Exception as e:
            print(f"✗ Ошибка во время ожидания авторизации: {e}")
            return False
        finally:
            try:
                driver.quit()
            except Exception:
                pass
        return False

    def save_cookies(self):
        cookies_file = Path('comx_cookies.json')
        with open(cookies_file, 'w', encoding='utf-8') as f:
            json.dump(self.cookies, f)
        print(f"✓ Cookies сохранены в {cookies_file}")

    def load_cookies(self):
        cookies_file = Path('comx_cookies.json')
        if cookies_file.exists():
            try:
                with open(cookies_file, 'r', encoding='utf-8') as f:
                    self.cookies = json.load(f)
                    # Create a new cookie jar to completely replace session cookies (avoids duplicates)
                    new_jar = requests.cookies.RequestsCookieJar()
                    for name, value in self.cookies.items():
                        new_jar.set(name, value, domain='com-x.life')
                    self.session.cookies = new_jar
                print("✓ Cookies загружены из файла")
                return True
            except Exception:
                pass
        return False

    def get_manga_id_from_url(self, url):
        match = re.search(r'/(\d+)-', url)
        if match:
            return match.group(1)
        return None

    def _perform_search_page(self, query, page=1):
        try:
            encoded_query = quote(query)
            search_url = f"{self.base_url}/search/{encoded_query}/page/{page}/" if page > 1 else f"{self.base_url}/search/{encoded_query}"
            response = self.session.get(search_url, headers=self.headers)
            if response.status_code != 200:
                return []
            soup = BeautifulSoup(response.content, 'lxml')
            content = soup.find('div', id='dle-content')
            if not content:
                return []
            results = []
            title_tags = content.find_all('h3', class_='readed__title')
            if not title_tags:
                return []
            for title_tag in title_tags:
                if title_tag.a:
                    title = title_tag.a.text.strip()
                    url = title_tag.a['href']
                    if not url.startswith('http'):
                        url = urljoin(self.base_url, url)
                    results.append({'title': title, 'url': url})
            return results
        except Exception:
            return []

    def fetch_search_results_sync(self, query):
        all_results = []
        current_page = 1
        limit = 30
        while len(all_results) < limit:
            page_results = self._perform_search_page(query, page=current_page)
            if not page_results:
                break
            all_results.extend(page_results)
            current_page += 1
        return all_results[:limit]

    def get_chapters_list(self, manga_url):
        print(SEPARATOR)
        print("ПОЛУЧЕНИЕ СПИСКА ГЛАВ")
        clean_url = manga_url.split('#')[0]
        response = self.session.get(clean_url, headers=self.headers)
        if response.status_code != 200:
            print(f"✗ Ошибка при загрузке страницы: {response.status_code}")
            if "Just a moment..." in response.text or response.status_code == 403:
                 print("✗ Похоже на защиту Cloudflare или бан. Попробуйте удалить comx_cookies.json и авторизоваться заново.")
            return None, None
        soup = BeautifulSoup(response.content, 'lxml')
        script_data = None
        for script in soup.find_all('script'):
            if script.string and 'window.__DATA__' in script.string:
                script_data = script.string
                break
        if not script_data:
            print("✗ Не удалось найти данные о главах (window.__DATA__)")
            return None, None
        try:
            json_match = re.search(r'window\.__DATA__\s*=\s*({.+?});', script_data, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
                chapters = data.get('chapters', [])
                chapters.sort(key=lambda x: x.get('posi', 0))
                manga_title_raw = data.get("title", "Unknown Manga")
                manga_title = self.sanitize_filename(manga_title_raw)
                print(f"✓ Найдено глав: {len(chapters)}")
                print(f"✓ Название манги: {manga_title}\n")
                return chapters, manga_title
        except Exception as e:
            print(f"✗ Ошибка парсинга данных: {e}")
        return None, None

    def download_chapter(self, chapter, base_manga_folder, news_id, manga_url):
        start_time = time.time()
        chapter_id = chapter['id']
        chapter_title_raw = chapter.get('title', f"Глава {chapter.get('number', '?')}")
        chapter_posi = chapter.get('posi', 0)

        match = re.match(r'^\s*([\d\.]+)\s*-\s*([\d\.]+)\s*(.*)', chapter_title_raw)
        if match:
            vol = match.group(1).strip()
            ch = match.group(2).strip()
            title = match.group(3).strip()
            chapter_name = f"Vol. {vol} Ch. {ch} - {title}"
        else:
            chapter_name = f"Ch. {chapter_posi:03d} - {chapter_title_raw}"

        chapter_title_safe = self.sanitize_filename(chapter_name)
        chapter_folder = base_manga_folder / chapter_title_safe
        completion_marker = chapter_folder / ".complete"

        if completion_marker.exists():
            print(f"  ⊘ {chapter_title_safe} (пропущено)")
            return True

        if chapter_folder.exists():
            shutil.rmtree(chapter_folder, ignore_errors=True)

        chapter_folder.mkdir(parents=True, exist_ok=True)

        if self.debug:
            print(f"  🔗 Скачиваю: {chapter_title_safe}...")
        else:
            print(f"  🔗 Скачиваю: {chapter_title_safe}...", end="", flush=True)

        try:
            reader_url = f"{self.base_url}/reader/{news_id}/{chapter_id}"
            resp = self.session.get(reader_url, headers=self.headers, timeout=30)

            if resp.status_code != 200:
                time_taken_s = f"({time.time() - start_time:.2f} сек)"
                msg = f"Ошибка страницы главы: {resp.status_code}"
                if self.debug:
                    print(f"  ✗ {msg} {time_taken_s}")
                else:
                    print(f"\r  ✗ {msg} {time_taken_s}")
                return False

            soup = BeautifulSoup(resp.content, 'lxml')
            script_data = None
            for script in soup.find_all('script'):
                if script.string and 'window.__DATA__' in script.string:
                    script_data = script.string
                    break

            images = []
            host = 'img.com-x.life'
            host_ru = 'rus.com-x.life'

            if script_data:
                json_match = re.search(
                    r'window\.__DATA__\s*=\s*({.+?});', script_data, re.DOTALL
                )
                if json_match:
                    try:
                        data = json.loads(json_match.group(1))
                        images = data.get('images', []) or []
                        host = data.get('host', host) or host
                        host_ru = data.get('host_ru', host_ru) or host_ru
                    except Exception:
                        pass

            if not images:
                img_tags = soup.select('.reader-view img.reader__item')
                for img in img_tags:
                    src = img.get('src') or img.get('data-src')
                    if not src:
                        continue
                    m = re.search(r'/comix/(.+)$', src)
                    if m:
                        images.append(m.group(1))
                if images:
                    first_src = img_tags[0].get('src') or img_tags[0].get('data-src') or ''
                    m_host = re.match(r'https://([^/]+)/', first_src)
                    if m_host:
                        host = m_host.group(1)

            if not images:
                time_taken_s = f"({time.time() - start_time:.2f} сек)"
                msg = "Не найдено изображений в window.__DATA__"
                if self.debug:
                    print(f"  ✗ {msg} {time_taken_s}")
                else:
                    print(f"\r  ✗ {msg} {time_taken_s}")
                return False

            total = len(images)
            downloaded = 0
            current_host = host

            for idx, img_path in enumerate(images, 1):
                if self.debug:
                    print(f"    [{idx}/{total}] {img_path}")
                else:
                    progress = f"{idx}/{total}"
                    print(f"\r  🔗 {chapter_title_safe} [{progress}]", end="", flush=True)

                for try_host in dict.fromkeys((current_host, host, host_ru)):
                    img_url = f"https://{try_host}/comix/{img_path}"
                    try:
                        img_resp = self.session.get(
                            img_url,
                            headers={**self.headers, 'Referer': reader_url},
                            timeout=30,
                        )
                        content_type = img_resp.headers.get('Content-Type', '').split(';', 1)[0].strip().lower()
                        if img_resp.status_code == 200 and content_type.startswith('image/'):
                            ext = Path(img_path).suffix.lower() or '.jpg'
                            filename = chapter_folder / f"{idx:03d}{ext}"
                            with open(filename, 'wb') as f:
                                f.write(img_resp.content)
                            downloaded += 1
                            current_host = try_host
                            break
                    except Exception:
                        continue

                time.sleep(0.05)

            time_taken_s = f"({time.time() - start_time:.2f} сек)"
            if downloaded == total:
                completion_marker.write_text(str(total), encoding='utf-8')
                if self.debug:
                    print(f"  ✓ {chapter_title_safe} ({downloaded}/{total}) {time_taken_s}")
                else:
                    print(f"\r  ✓ {chapter_title_safe} ({downloaded}/{total}){' ' * 20} {time_taken_s}")
                return True
            else:
                msg = f"{downloaded}/{total} — неполная глава, папка удалена"
                if self.debug:
                    print(f"  ✗ {chapter_title_safe} ({msg}) {time_taken_s}")
                else:
                    print(f"\r  ✗ {chapter_title_safe} ({msg}){' ' * 20} {time_taken_s}")
                try:
                    shutil.rmtree(chapter_folder, ignore_errors=True)
                except Exception:
                    pass
                return False

        except Exception as e:
            time_taken_s = f"({time.time() - start_time:.2f} сек)"
            if self.debug:
                print(f"  ✗ Ошибка: {chapter_title_safe} ({e}) {time_taken_s}")
            else:
                print(f"\r  ✗ Ошибка: {chapter_title_safe} ({e}){' ' * 20} {time_taken_s}")
            try:
                shutil.rmtree(chapter_folder, ignore_errors=True)
            except Exception:
                pass
            return False
        except KeyboardInterrupt:
            try:
                shutil.rmtree(chapter_folder, ignore_errors=True)
            except Exception:
                pass
            raise

    def download_manga(self, manga_url, output_dir="manga", start_chapter=None, end_chapter=None,
                        output_format=None, delete_sources=None, quiet=False):
        if not self.load_cookies():
            if not self.get_cookies_via_selenium():
                print(f"\n{RED}✗ ОШИБКА: Не удалось авторизоваться{ENDC}")
                return False

        if not quiet:
            clear_console()
            print_menu()
        news_id = self.get_manga_id_from_url(manga_url)
        if not news_id:
            print(f"\n{RED}✗ Не удалось определить ID манги из URL{ENDC}")
            return False

        print(f"\n📖 ID манги: {news_id}")
        chapters, manga_title = self.get_chapters_list(manga_url)

        if not chapters or not manga_title:
            print(f"\n{RED}✗ Не удалось получить список глав или название манги{ENDC}")
            print("💡 Попробуйте:")
            print("    1. Удалить файл comx_cookies.json и авторизоваться заново")
            print("    2. Проверить правильность URL манги")
            return False

        if start_chapter or end_chapter:
            start = start_chapter or 1
            end = end_chapter or 99999
            chapters = [ch for ch in chapters if start <= ch.get('posi', 0) <= end]
            print(f"📌 Выбран диапазон: главы {start}-{end} ({len(chapters)} шт.)\n")

        base_manga_folder = Path(output_dir) / manga_title
        base_manga_folder.mkdir(parents=True, exist_ok=True)

        print(SEPARATOR)
        print(f"{CYAN}{BOLD}СКАЧИВАНИЕ ГЛАВ{ENDC}")
        print(SEPARATOR)

        total_start_time = time.time()
        success_count = 0

        for idx, chapter in enumerate(chapters, 1):
            try:
                if self.download_chapter(chapter, base_manga_folder, news_id, manga_url):
                    success_count += 1
                time.sleep(1)
            except KeyboardInterrupt:
                print(f"\n\n{YELLOW}⚠ Прервано пользователем{ENDC}")
                break
            except Exception as e:
                print(f"  {RED}✗ Ошибка: {e}{ENDC}")
                continue

        total_time_taken = time.time() - total_start_time

        print(SEPARATOR)
        print(f"{GREEN}{BOLD}ЗАВЕРШЕНО{ENDC}")
        print(SEPARATOR)
        print(f"✓ Успешно скачано: {success_count}/{len(chapters)} глав")
        print(f"🕒 Общее время: {total_time_taken:.2f} сек")
        print(f"📁 Сохранено в: {base_manga_folder.absolute()}\n")

        if success_count > 0:
            if output_format is not None:
                self.process_output(base_manga_folder, manga_title, output_format, delete_sources)
            else:
                self.prompt_output_creation(base_manga_folder, manga_title)

        return True

    @staticmethod
    def sanitize_filename(filename):
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        filename = re.sub(r'[\s_]+', ' ', filename)
        return filename.strip()

    @staticmethod
    def parse_range(range_str):
        range_str = range_str.strip()
        if not range_str:
            return None, None
        if '-' in range_str:
            parts = range_str.split('-')
            try:
                start = int(parts[0]) if parts[0] else None
            except ValueError:
                start = None
            try:
                end = int(parts[1]) if parts[1] else None
            except ValueError:
                end = None
            return start, end
        else:
            try:
                num = int(range_str)
                return num, num
            except ValueError:
                return None, None

    @staticmethod
    def parse_chapter_sort_key(folder_name):
        """Extract volume/chapter numbers from folder name for sorting."""
        # Pattern: "Vol. X Ch. Y - Title"
        match = re.match(r'Vol\.\s*([\d.]+)\s*Ch\.\s*([\d.]+)', folder_name)
        if match:
            try:
                vol = float(match.group(1))
                ch = float(match.group(2))
                return (vol, ch)
            except ValueError:
                pass

        # Pattern: "Ch. X - Title"
        match = re.match(r'Ch\.\s*([\d.]+)', folder_name)
        if match:
            try:
                ch = float(match.group(1))
                return (0, ch)
            except ValueError:
                pass

        # Fallback: extract any number
        numbers = re.findall(r'[\d.]+', folder_name)
        if numbers:
            try:
                return (0, float(numbers[0]))
            except ValueError:
                pass

        return (0, 0)

    @staticmethod
    def get_sorted_chapter_folders(manga_folder):
        """Return chapter folders sorted by volume/chapter number."""
        folders = [f for f in manga_folder.iterdir() if f.is_dir()]
        folders.sort(key=lambda f: ComXLifeDownloader.parse_chapter_sort_key(f.name))
        return folders

    @staticmethod
    def get_sorted_images(chapter_folder):
        """Return image files sorted naturally (2.jpg before 10.jpg)."""
        image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
        images = [f for f in chapter_folder.iterdir()
                  if f.is_file() and f.suffix.lower() in image_extensions]

        def natural_sort_key(path):
            # Extract numbers for natural sorting
            parts = re.split(r'(\d+)', path.stem)
            return [int(p) if p.isdigit() else p.lower() for p in parts]

        images.sort(key=natural_sort_key)
        return images

    @staticmethod
    def convert_webp_to_jpeg(webp_path, temp_dir):
        """Convert WebP image to JPEG for img2pdf compatibility."""
        try:
            img = Image.open(webp_path)
            # Handle RGBA/alpha channel
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            jpeg_path = Path(temp_dir) / f"{webp_path.stem}.jpg"
            img.save(jpeg_path, 'JPEG', quality=95)
            return jpeg_path
        except Exception as e:
            print(f"    {YELLOW}⚠ Не удалось конвертировать {webp_path.name}: {e}{ENDC}")
            return None

    def create_pdf(self, manga_folder, output_pdf_path):
        """Create PDF from all chapter images."""
        print(f"\n{CYAN}📄 Создание PDF...{ENDC}")

        chapter_folders = self.get_sorted_chapter_folders(manga_folder)
        if not chapter_folders:
            print(f"{RED}✗ Не найдено папок с главами{ENDC}")
            return False

        all_images = []
        temp_dir = None

        try:
            # Collect all images
            for folder in chapter_folders:
                images = self.get_sorted_images(folder)
                if not images:
                    print(f"  {YELLOW}⚠ Пустая папка: {folder.name}{ENDC}")
                    continue
                all_images.extend(images)

            if not all_images:
                print(f"{RED}✗ Не найдено изображений для PDF{ENDC}")
                return False

            print(f"  Найдено {len(all_images)} изображений в {len(chapter_folders)} главах")

            # Process images (convert WebP if needed)
            temp_dir = tempfile.mkdtemp()
            image_paths = []

            for idx, img_path in enumerate(all_images):
                # Show progress
                progress = (idx + 1) / len(all_images) * 100
                print(f"\r  Обработка: {progress:.0f}%", end="", flush=True)

                if img_path.suffix.lower() == '.webp':
                    converted = self.convert_webp_to_jpeg(img_path, temp_dir)
                    if converted:
                        image_paths.append(str(converted))
                else:
                    image_paths.append(str(img_path))

            print("\r  Обработка: 100%   ")

            if not image_paths:
                print(f"{RED}✗ Нет изображений для включения в PDF{ENDC}")
                return False

            # Create PDF
            print("  Генерация PDF...")
            with open(output_pdf_path, 'wb') as f:
                f.write(img2pdf.convert(image_paths))

            # Report file size
            file_size = output_pdf_path.stat().st_size
            if file_size >= 1024 * 1024 * 1024:
                size_str = f"{file_size / (1024 * 1024 * 1024):.2f} ГБ"
            elif file_size >= 1024 * 1024:
                size_str = f"{file_size / (1024 * 1024):.2f} МБ"
            else:
                size_str = f"{file_size / 1024:.2f} КБ"

            print(f"{GREEN}✓ PDF создан: {output_pdf_path} ({size_str}){ENDC}")
            return True

        except KeyboardInterrupt:
            print(f"\n{YELLOW}⚠ Создание PDF прервано{ENDC}")
            if output_pdf_path.exists():
                output_pdf_path.unlink()
            return False
        except Exception as e:
            print(f"{RED}✗ Ошибка создания PDF: {e}{ENDC}")
            return False
        finally:
            # Clean up temp directory
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

    def delete_manga_folder(self, manga_folder):
        """Delete the entire manga folder with all images."""
        try:
            shutil.rmtree(manga_folder)
            print(f"✓ Удалена папка: {manga_folder.name}")
        except Exception as e:
            print(f"  {YELLOW}⚠ Не удалось удалить {manga_folder.name}: {e}{ENDC}")

    def create_cbz(self, manga_folder, output_cbz_path):
        """Create CBZ (Comic Book ZIP) from all chapter images."""
        print(f"\n{CYAN}📦 Создание CBZ...{ENDC}")

        chapter_folders = self.get_sorted_chapter_folders(manga_folder)
        if not chapter_folders:
            print(f"{RED}✗ Не найдено папок с главами{ENDC}")
            return False

        try:
            total_images = 0
            for folder in chapter_folders:
                total_images += len(self.get_sorted_images(folder))

            if total_images == 0:
                print(f"{RED}✗ Не найдено изображений для CBZ{ENDC}")
                return False

            print(f"  Найдено {total_images} изображений в {len(chapter_folders)} главах")

            processed = 0
            with zipfile.ZipFile(output_cbz_path, 'w', zipfile.ZIP_STORED) as zf:
                for ch_idx, folder in enumerate(chapter_folders):
                    chapter_num = f"{ch_idx + 1:03d}"
                    images = self.get_sorted_images(folder)

                    for img_idx, img_path in enumerate(images):
                        processed += 1
                        progress = processed / total_images * 100
                        print(f"\r  Упаковка: {progress:.0f}%", end="", flush=True)

                        arcname = f"{chapter_num}/{img_idx + 1:03d}{img_path.suffix.lower()}"
                        zf.write(img_path, arcname)

            print("\r  Упаковка: 100%   ")

            # Report file size
            file_size = output_cbz_path.stat().st_size
            if file_size >= 1024 * 1024 * 1024:
                size_str = f"{file_size / (1024 * 1024 * 1024):.2f} ГБ"
            elif file_size >= 1024 * 1024:
                size_str = f"{file_size / (1024 * 1024):.2f} МБ"
            else:
                size_str = f"{file_size / 1024:.2f} КБ"

            print(f"{GREEN}✓ CBZ создан: {output_cbz_path} ({size_str}){ENDC}")
            return True

        except KeyboardInterrupt:
            print(f"\n{YELLOW}⚠ Создание CBZ прервано{ENDC}")
            if output_cbz_path.exists():
                output_cbz_path.unlink()
            return False
        except Exception as e:
            print(f"{RED}✗ Ошибка создания CBZ: {e}{ENDC}")
            return False

    def prompt_output_creation(self, manga_folder, manga_title):
        """Ask user which output format to create and optionally delete originals."""
        try:
            questions = [
                inquirer.List('format',
                              message="📦 Выберите формат для сохранения",
                              choices=[
                                  ('CBZ (рекомендуется)', 'cbz'),
                                  ('PDF', 'pdf'),
                                  ('Не создавать', 'skip'),
                              ],
                              carousel=True),
            ]
            answers = inquirer.prompt(questions)

            if not answers or answers['format'] == 'skip':
                return

            output_path = manga_folder.parent / f"{manga_title}.{answers['format']}"

            if answers['format'] == 'cbz':
                success = self.create_cbz(manga_folder, output_path)
            else:
                success = self.create_pdf(manga_folder, output_path)

            if not success:
                return

            # Ask about deleting originals
            questions = [
                inquirer.Confirm('delete_originals',
                                 message="🗑  Удалить исходные изображения?",
                                 default=False),
            ]
            answers = inquirer.prompt(questions)

            if answers and answers['delete_originals']:
                self.delete_manga_folder(manga_folder)

        except KeyboardInterrupt:
            print(f"\n{YELLOW}⚠ Отменено{ENDC}")

    def process_output(self, manga_folder, manga_title, output_format, delete_sources):
        """Non-interactive output creation for batch mode."""
        if output_format == "none":
            return
        output_path = manga_folder.parent / f"{manga_title}.{output_format}"
        if output_format == "cbz":
            success = self.create_cbz(manga_folder, output_path)
        else:
            success = self.create_pdf(manga_folder, output_path)
        if success and delete_sources:
            self.delete_manga_folder(manga_folder)

def save_batch_file(filepath, urls, settings):
    """Write/update batch JSON file."""
    data = {"urls": urls, "settings": settings}
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_batch_file(filepath):
    """Read and return batch data from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    if sys.version_info < (3, 7):
        print(f"{RED}✗ Ошибка: Этот скрипт требует Python 3.7+.{ENDC}")
        sys.exit(1)

    clear_console()
    print_menu()

    try:
        questions = [
            inquirer.List('browser',
                          message="🔧 Выберите браузер для авторизации",
                          choices=['Chrome', 'Firefox'],
                          carousel=True),
        ]
        answers = inquirer.prompt(questions)
        if not answers:
            raise KeyboardInterrupt

        browser_name = answers['browser'].lower()
        downloader = ComXLifeDownloader(browser_choice=browser_name, debug=True)

        while True:
            clear_console()
            print_menu()

            input_str = input(f"{CYAN}📖 Введите URL, название манги или путь к batch .json (Enter для выхода): {ENDC}").strip()

            if not input_str:
                raise KeyboardInterrupt

            # --- Path A: Resume existing batch JSON ---
            if input_str.endswith('.json') and Path(input_str).is_file():
                try:
                    batch_data = load_batch_file(input_str)
                    batch_urls = batch_data["urls"]
                    settings = batch_data["settings"]
                    pending = [u for u in batch_urls if u["status"] != "done"]
                    if not pending:
                        print(f"{GREEN}✓ Все URL в этом батче уже обработаны.{ENDC}")
                        time.sleep(2)
                        continue
                    print(f"\n{YELLOW}📋 Возобновление батча: {len(pending)} из {len(batch_urls)} ожидают скачивания{ENDC}")
                    output_dir = settings.get("output_dir", "Manga")
                    range_str = settings.get("chapters", "")
                    start_chapter, end_chapter = ComXLifeDownloader.parse_range(range_str)
                    output_format = settings.get("format", "none")
                    delete_sources = settings.get("delete_sources", False)
                    batch_filepath = Path(input_str)

                    done_count = 0
                    fail_count = 0
                    for entry in batch_urls:
                        if entry["status"] == "done":
                            continue
                        print(f"\n{CYAN}{BOLD}▶ [{done_count + fail_count + 1}/{len(pending)}] {entry['url']}{ENDC}")
                        try:
                            ok = downloader.download_manga(
                                entry["url"], output_dir, start_chapter, end_chapter,
                                output_format=output_format, delete_sources=delete_sources, quiet=True
                            )
                            if ok:
                                entry["status"] = "done"
                                done_count += 1
                            else:
                                fail_count += 1
                        except KeyboardInterrupt:
                            print(f"\n{YELLOW}⚠ Батч прерван пользователем{ENDC}")
                            save_batch_file(batch_filepath, batch_urls, settings)
                            break
                        save_batch_file(batch_filepath, batch_urls, settings)

                    print(SEPARATOR)
                    print(f"{GREEN}{BOLD}ИТОГИ БАТЧА{ENDC}")
                    print(SEPARATOR)
                    print(f"  ✓ Успешно: {done_count}")
                    if fail_count:
                        print(f"  ✗ Ошибки: {fail_count}")
                    remaining = sum(1 for u in batch_urls if u["status"] != "done")
                    if remaining:
                        print(f"  ⏳ Осталось: {remaining}")
                    print(f"  📄 Батч-файл: {batch_filepath}")

                except Exception as e:
                    print(f"{RED}✗ Ошибка чтения батч-файла: {e}{ENDC}")
                    time.sleep(2)

                print(f"\n{CYAN}Нажмите Enter, чтобы продолжить...{ENDC}")
                input()
                continue

            # --- Path B: URL → build batch list ---
            if 'com-x.life' in input_str and 'http' in input_str:
                batch_urls_list = [input_str]
                print(f"\n{GREEN}  1. {input_str}{ENDC}")

                while True:
                    next_input = input(f"{CYAN}📖 Добавьте ещё URL или 'y' для начала скачивания: {ENDC}").strip()
                    if next_input.lower() == 'y':
                        break
                    if 'com-x.life' in next_input and 'http' in next_input:
                        batch_urls_list.append(next_input)
                        print(f"{GREEN}  {len(batch_urls_list)}. {next_input}{ENDC}")
                    elif not next_input:
                        continue
                    else:
                        print(f"{YELLOW}⚠ Введите URL com-x.life или 'y' для старта{ENDC}")

                # Collect settings once
                output_dir = input(f"{CYAN}📁 Папка для сохранения [Manga]: {ENDC}").strip() or 'Manga'
                range_str = input(f"{CYAN}💡 Укажите диапазон глав (Enter = все): {ENDC}").strip()
                start_chapter, end_chapter = ComXLifeDownloader.parse_range(range_str)

                fmt_questions = [
                    inquirer.List('format',
                                  message="📦 Формат для всех манг",
                                  choices=[
                                      ('CBZ (рекомендуется)', 'cbz'),
                                      ('PDF', 'pdf'),
                                      ('Не создавать', 'none'),
                                  ],
                                  carousel=True),
                ]
                fmt_answers = inquirer.prompt(fmt_questions)
                output_format = fmt_answers['format'] if fmt_answers else 'none'

                delete_sources = False
                if output_format != 'none':
                    del_questions = [
                        inquirer.Confirm('delete_sources',
                                         message="🗑  Удалить исходные изображения после создания?",
                                         default=False),
                    ]
                    del_answers = inquirer.prompt(del_questions)
                    delete_sources = del_answers['delete_sources'] if del_answers else False

                # Build batch tracking data
                batch_entries = [{"url": u, "status": "pending"} for u in batch_urls_list]
                settings = {
                    "output_dir": output_dir,
                    "chapters": range_str,
                    "format": output_format,
                    "delete_sources": delete_sources,
                }
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                batch_filepath = Path(output_dir) / f"batch_{timestamp}.json"
                Path(output_dir).mkdir(parents=True, exist_ok=True)
                save_batch_file(batch_filepath, batch_entries, settings)
                print(f"\n{GREY}📄 Батч-файл: {batch_filepath}{ENDC}")

                # Process each URL
                done_count = 0
                fail_count = 0
                for idx, entry in enumerate(batch_entries):
                    print(f"\n{CYAN}{BOLD}▶ [{idx + 1}/{len(batch_entries)}] {entry['url']}{ENDC}")
                    try:
                        ok = downloader.download_manga(
                            entry["url"], output_dir, start_chapter, end_chapter,
                            output_format=output_format, delete_sources=delete_sources, quiet=True
                        )
                        if ok:
                            entry["status"] = "done"
                            done_count += 1
                        else:
                            fail_count += 1
                    except KeyboardInterrupt:
                        print(f"\n{YELLOW}⚠ Батч прерван пользователем{ENDC}")
                        save_batch_file(batch_filepath, batch_entries, settings)
                        break
                    save_batch_file(batch_filepath, batch_entries, settings)

                # Summary
                print(SEPARATOR)
                print(f"{GREEN}{BOLD}ИТОГИ БАТЧА{ENDC}")
                print(SEPARATOR)
                print(f"  ✓ Успешно: {done_count}")
                if fail_count:
                    print(f"  ✗ Ошибки: {fail_count}")
                remaining = sum(1 for e in batch_entries if e["status"] != "done")
                if remaining:
                    print(f"  ⏳ Осталось: {remaining}")
                print(f"  📄 Батч-файл: {batch_filepath}")

                print(f"\n{CYAN}Нажмите Enter, чтобы продолжить...{ENDC}")
                input()
                continue

            # --- Path D: Search query (unchanged) ---
            manga_url = None
            clear_console()
            print_menu()
            print(f"\n{YELLOW}🔍 Ищу '{input_str}'...{ENDC}")
            results = downloader.fetch_search_results_sync(input_str)

            clear_console()
            print_menu()

            if not results:
                print(f"{RED}✗ Ничего не найдено по запросу '{input_str}'.{ENDC}")
                time.sleep(2)
                continue

            if len(results) == 1:
                manga_url = results[0]['url']
                print(f"✓ Найдена 1 манга: {results[0]['title']}")
            else:
                print(f"\n{YELLOW}📚 Найдено {len(results)} результатов. Выберите:{ENDC}")
                for i, res in enumerate(results, 1):
                    print(f"  {i:02d}: {res['title']}")

                print(f"\n{GREY}(Введите номер или нажмите Enter для нового поиска){ENDC}")
                choice_str = input(f"{CYAN}Выберите номер: {ENDC}").strip()

                if not choice_str:
                    continue

                try:
                    choice_idx = int(choice_str) - 1
                    if 0 <= choice_idx < len(results):
                        manga_url = results[choice_idx]['url']
                        print(f"✓ Выбрано: {results[choice_idx]['title']}")
                    else:
                        print(f"{RED}✗ Неверный номер.{ENDC}")
                        time.sleep(2)
                        continue
                except ValueError:
                    print(f"{RED}✗ Неверный ввод.{ENDC}")
                    time.sleep(2)
                    continue

            if not manga_url:
                 continue

            output_dir = input(f"{CYAN}📁 Папка для сохранения [Manga]: {ENDC}").strip() or 'Manga'
            range_str = input(f"{CYAN}💡 Укажите диапазон (Enter = все): {ENDC}").strip()
            start_chapter, end_chapter = ComXLifeDownloader.parse_range(range_str)

            downloader.download_manga(manga_url, output_dir, start_chapter, end_chapter)

            print(f"\n{CYAN}Нажмите Enter, чтобы начать новый поиск...{ENDC}")
            input()

    except KeyboardInterrupt:
        print()
        sys.exit(0)
    except Exception as e:
        print(f"\n{RED}✗ Критическая ошибка: {e}{ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
