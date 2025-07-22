# TikTok-Fetch-All
TikTok Auto Downloader is a Python script that scrapes and downloads videos and photos from any public TikTok profile. It uses browser automation, supports cookie-based login, saves media with timestamps, and lets you choose how many recent posts to download (10–100 or all).


## 📘 `README.md`

````markdown
# 🎬 TikTok Auto Downloader (Profile Scraper + Media Grabber)

A Python-based tool to **automatically extract and download all videos and photo posts from any public TikTok profile**, using browser automation and multithreaded downloading.

---

## ✅ Features

- 🔐 Cookie-based login (no TikTok API required)
- 🔍 Scrapes all videos and photos from a public profile
- 🕐 Sorts by timestamp (based on TikTok ID)
- 📂 Saves media with readable timestamped filenames
- ⚡ Supports multithreaded downloads for speed
- 🎛️ Menu: download all or only the latest 10, 25, 50, 75, or 100 posts
- 🧠 Automatically detects expired sessions and reloads cookies

---

## 💻 Requirements

- Python 3.8+
- Chromium (automatically handled by Playwright)

---

## 📦 Installation

```bash
git clone https://github.com/your-username/tiktok-auto-downloader.git
cd tiktok-auto-downloader
pip install -r requirements.txt
playwright install chromium
````

---

## 🔐 Step 1: Export TikTok Cookies

Use a browser extension to export cookies from [https://www.tiktok.com](https://www.tiktok.com):

* Chrome: [EditThisCookie](https://chrome.google.com/webstore/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg)
* Firefox: [Cookie Quick Manager](https://addons.mozilla.org/en-US/firefox/addon/cookie-quick-manager/)

Export the cookies as a JSON file and name it:

```
tiktok_cookies.json
```

Place it in the **same folder as the script**.

---

## ▶️ Step 2: Run the Script

```bash
python tiktok_fetch_all.py https://www.tiktok.com/@username
```

You will be asked to choose how many posts you want to download:

```
1. All posts
2. Last 50
3. Last 25
4. Last 10
5. Last 75
6. Last 100
```

Media will be downloaded to the `downloads/` folder.

---

## 🧠 How It Works

* First run: loads `tiktok_cookies.json`, logs you in, and creates a session file
* Future runs: reuses session unless expired
* Automatically scrolls through the profile and extracts all valid video/photo URLs
* Each media file is named with: `@username_postID_timestamp`
* Photos and videos are downloaded via `tiktok-downloader` (snaptik wrapper)

---

## 📁 Folder Structure

```
tiktok_fetch_all.py
tiktok_cookies.json       # Your exported TikTok cookies
tiktok_session.json       # Auto-generated session state
urls.txt                  # Extracted media URLs (auto-generated)
downloads/                # All downloaded videos/photos
```

---

## ⚠️ Legal Notice

This script is intended for **personal use only**. Respect content creators and **do not share or redistribute downloaded content** without permission. You are responsible for complying with TikTok's [Terms of Service](https://www.tiktok.com/legal/page/row/terms-of-service/en).

---

## 📮 Feedback & Contributions

Pull requests, ideas, and improvements are welcome!

