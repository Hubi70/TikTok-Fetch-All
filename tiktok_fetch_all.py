import time
import random
import re
import os
import sys
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright
from tiktok_downloader import snaptik

# === CONFIGURATION ===
DEFAULT_CONFIG = {
    "threads": 4,
    "download_folder": "downloads",
    "skip_existing": True
}
SESSION_FILE = "tiktok_session.json"
COOKIE_FILE = "tiktok_cookies.json"

# === HELPER FUNCTIONS ===
def extract_timestamp_from_id(content_id):
    try:
        return int(content_id) >> 32
    except:
        return 0

def format_timestamp(unix_timestamp):
    try:
        return datetime.utcfromtimestamp(unix_timestamp).strftime("%Y%m%d_%H%M%S")
    except:
        return "unknown_time"

def extract_username(profile_url):
    match = re.search(r"tiktok\.com/@([a-zA-Z0-9_.]+)", profile_url)
    return match.group(1) if match else None

def get_timestamp_from_url(url):
    match = re.search(r'/(video|photo)/(\d+)', url)
    if not match:
        return 0
    content_id = match.group(2)
    return extract_timestamp_from_id(content_id)

# === COOKIE SESSION HANDLING ===
def load_real_browser_cookies_into_playwright():
    if not os.path.exists(COOKIE_FILE):
        print(f"❌ Cookie file '{COOKIE_FILE}' not found.")
        sys.exit(1)

    with open(COOKIE_FILE, "r", encoding="utf-8") as f:
        cookies = json.load(f)

    valid_same_sites = {"Strict", "Lax", "None"}

    formatted = []
    for cookie in cookies:
        same_site = cookie.get("sameSite", "Lax")
        if same_site not in valid_same_sites:
            same_site = "Lax"

        formatted.append({
            "name": cookie["name"],
            "value": cookie["value"],
            "domain": cookie["domain"],
            "path": cookie.get("path", "/"),
            "expires": cookie.get("expires", -1),
            "httpOnly": cookie.get("httpOnly", False),
            "secure": cookie.get("secure", True),
            "sameSite": same_site
        })

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        context.add_cookies(formatted)
        context.storage_state(path=SESSION_FILE)
        print("✅ Cookies imported and session saved.")
        browser.close()

# === SESSION CHECK ===
def ensure_session_is_valid():
    def session_works():
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(storage_state=SESSION_FILE)
            page = context.new_page()
            page.goto("https://www.tiktok.com/")
            try:
                page.wait_for_selector('a[href*="/inbox"]', timeout=5000)
                return True
            except:
                return False
            finally:
                browser.close()

    if not os.path.exists(SESSION_FILE) or not session_works():
        print("🔐 Session invalid or expired. Reloading cookies...")
        load_real_browser_cookies_into_playwright()
    else:
        print("✅ Valid TikTok session found.")

# === SCRAPE PROFILE ===
def scrape_profile(profile_url, output_file='urls.txt'):
    username = extract_username(profile_url)
    if not username:
        print("❌ Invalid TikTok URL.")
        return []

    print(f"📥 Scraping profile: @{username}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=SESSION_FILE)
        page = context.new_page()
        page.goto(profile_url)
        time.sleep(random.uniform(5, 6))

        for i in range(12):
            page.mouse.wheel(0, random.randint(2500, 3500))
            print(f"🧭 Scrolling... ({i+1}/12)")
            time.sleep(random.uniform(2.5, 4.5))

        print("🔍 Collecting links...")
        urls = set()
        links = page.query_selector_all('a[href*="/video/"], a[href*="/photo/"]')
        for el in links:
            href = el.get_attribute("href")
            if href and re.match(r"^https://www\.tiktok\.com/@[\w\._-]+/(video|photo)/\d+$", href):
                urls.add(href)

        with open(output_file, "w", encoding="utf-8") as f:
            for url in sorted(urls):
                f.write(url + "\n")

        print(f"✅ {len(urls)} links saved to '{output_file}'")
        browser.close()

    return sorted(urls)

# === DOWNLOAD VIDEO ===
def download_tiktok_video(url, index, total, config):
    username = re.search(r'/@([^/]+)', url).group(1) if re.search(r'/@([^/]+)', url) else "unknown"
    video_id = re.search(r'/video/(\d+)', url).group(1) if re.search(r'/video/(\d+)', url) else "unknown"
    ts = format_timestamp(extract_timestamp_from_id(video_id))

    try:
        downloader = snaptik(url)
        if not downloader:
            print(f"[{index}/{total}] ⚠️ No video found for {url}")
            return

        video = downloader[0]
        fname = f"{username}_{video_id}_{ts}.mp4"
        fname = re.sub(r'[^\w\-_\.]', '_', fname)
        path = os.path.join(config['download_folder'], fname)

        if config['skip_existing'] and os.path.exists(path):
            print(f"[{index}/{total}] ⏭️ File already exists: {fname}")
            return

        video.download(path)
        print(f"[{index}/{total}] ✅ Video saved: {fname}")
    except Exception as e:
        print(f"[{index}/{total}] ❌ Error: {e}")

# === DOWNLOAD PHOTO ===
def download_tiktok_photo(url, index, total, config):
    username = re.search(r'/@([^/]+)', url).group(1) if re.search(r'/@([^/]+)', url) else "unknown"
    photo_id = re.search(r'/photo/(\d+)', url).group(1) if re.search(r'/photo/(\d+)', url) else "unknown"
    ts = format_timestamp(extract_timestamp_from_id(photo_id))

    try:
        downloader = snaptik(url)
        if not downloader:
            print(f"[{index}/{total}] ⚠️ No photo found for {url}")
            return

        for i, item in enumerate(downloader, start=1):
            ext = ".jpg"
            try:
                url_attr = getattr(item, 'url', None)
                if url_attr:
                    ext = os.path.splitext(url_attr)[1] or ".jpg"
            except:
                pass

            base = f"{username}_{photo_id}_{ts}"
            fname = f"{base}_{i}{ext}" if len(downloader) > 1 else f"{base}{ext}"
            fname = re.sub(r'[^\w\-_\.]', '_', fname)
            path = os.path.join(config['download_folder'], fname)

            if config['skip_existing'] and os.path.exists(path):
                print(f"[{index}/{total}] ⏭️ File already exists: {fname}")
                continue

            item.download(path)
            print(f"[{index}/{total}] ✅ Photo saved: {fname}")
    except Exception as e:
        print(f"[{index}/{total}] ❌ Error: {e}")

# === DOWNLOAD MANAGER ===
def download_from_file(file_path, config):
    if not os.path.exists(config['download_folder']):
        os.makedirs(config['download_folder'])

    with open(file_path, 'r', encoding='utf-8') as f:
        all_urls = [line.strip() for line in f if line.strip()]

    if not all_urls:
        print("⚠️ No links found in file.")
        return

    print("\nWhat would you like to download?")
    print("1. All posts")
    print("2. Latest 50 posts")
    print("3. Latest 25 posts")
    print("4. Latest 10 posts")
    print("5. Latest 75 posts")
    print("6. Latest 100 posts")
    choice = input("➡️ Choose (1/2/3/4/5/6): ").strip()

    urls_with_time = [(url, get_timestamp_from_url(url)) for url in all_urls]
    urls_with_time.sort(key=lambda x: x[1], reverse=True)

    if choice == "2":
        urls = [url for url, _ in urls_with_time[:50]]
    elif choice == "3":
        urls = [url for url, _ in urls_with_time[:25]]
    elif choice == "4":
        urls = [url for url, _ in urls_with_time[:10]]
    elif choice == "5":
        urls = [url for url, _ in urls_with_time[:75]]
    elif choice == "6":
        urls = [url for url, _ in urls_with_time[:100]]
    else:
        urls = [url for url, _ in urls_with_time]

    total = len(urls)
    print(f"\n🔽 Starting download of {total} item(s)...\n")

    with ThreadPoolExecutor(max_workers=config['threads']) as executor:
        futures = []
        for i, url in enumerate(urls):
            if "/video/" in url:
                futures.append(executor.submit(download_tiktok_video, url, i+1, total, config))
            elif "/photo/" in url:
                futures.append(executor.submit(download_tiktok_photo, url, i+1, total, config))
            else:
                print(f"[{i+1}/{total}] ⚠️ Unknown TikTok link: {url}")

        for future in as_completed(futures):
            future.result()

    print("\n✅ All selected content has been processed.")

# === MAIN ===
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("⚠️ Usage: python tiktok_fetch_all.py <TikTok profile URL>")
        sys.exit(1)

    profile_url = sys.argv[1]
    ensure_session_is_valid()
    scrape_profile(profile_url, output_file="urls.txt")
    download_from_file("urls.txt", DEFAULT_CONFIG)

