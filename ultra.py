import os
import time
import random
import requests
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto

# ===============================
# LOAD ENV
# ===============================
load_dotenv(dotenv_path="/root/autopostfb/.env", override=True)

TG_API_ID = int(os.getenv("TG_API_ID"))
TG_API_HASH = os.getenv("TG_API_HASH")
TG_CHANNEL = int(os.getenv("TG_CHANNEL"))

FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN")

POST_DELAY_MINUTES = int(os.getenv("POST_DELAY_MINUTES", "60"))
POST_DELAY_SECONDS = POST_DELAY_MINUTES * 60

# ===============================
# PATHS
# ===============================
BASE_DIR = "/root/autopostfb"
SESSION_DIR = os.path.join(BASE_DIR, "session")
IMG_DIR = os.path.join(BASE_DIR, "images")
CAPTION_FILE = os.path.join(BASE_DIR, "caption.txt")
LAST_ID_FILE = os.path.join(BASE_DIR, "last_id.txt")
LAST_TIME_FILE = os.path.join(BASE_DIR, "last_post_time.txt")

os.makedirs(SESSION_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

SESSION_PATH = os.path.join(SESSION_DIR, "ultra")

# ===============================
# HELPERS
# ===============================
def load_last_id():
    if not os.path.exists(LAST_ID_FILE):
        return 0
    return int(open(LAST_ID_FILE).read().strip() or 0)

def save_last_id(msg_id):
    with open(LAST_ID_FILE, "w") as f:
        f.write(str(msg_id))

def load_last_post_time():
    if not os.path.exists(LAST_TIME_FILE):
        return 0
    return int(open(LAST_TIME_FILE).read().strip() or 0)

def save_last_post_time(ts):
    with open(LAST_TIME_FILE, "w") as f:
        f.write(str(ts))

def load_safe_caption():
    if not os.path.exists(CAPTION_FILE):
        return "Link ada di komentar 👇"
    with open(CAPTION_FILE, "r", encoding="utf-8") as f:
        lines = [x.strip() for x in f if x.strip()]
    return random.choice(lines) if lines else "Link ada di komentar 👇"

# ===============================
# FACEBOOK API
# ===============================
def upload_photo_to_fb(image_path, caption):
    url = f"https://graph.facebook.com/v24.0/{FB_PAGE_ID}/photos"
    with open(image_path, "rb") as img:
        r = requests.post(
            url,
            files={"source": img},
            data={
                "caption": caption,
                "access_token": FB_PAGE_TOKEN
            },
            timeout=60
        )
    print("📤 FB PHOTO RESPONSE:", r.text)
    return r

def post_fb_comment(post_id, text):
    url = f"https://graph.facebook.com/v24.0/{post_id}/comments"
    r = requests.post(
        url,
        data={
            "message": text,
            "access_token": FB_PAGE_TOKEN
        },
        timeout=30
    )
    print("💬 FB COMMENT RESPONSE:", r.text)

# ===============================
# MAIN LOGIC
# ===============================
async def run():
    now = int(time.time())
    last_post_time = load_last_post_time()

    # ⏳ CHECK DELAY
    if now - last_post_time < POST_DELAY_SECONDS:
        wait = POST_DELAY_SECONDS - (now - last_post_time)
        print(f"⏳ Belum waktunya posting. Tunggu {wait // 60} menit lagi.")
        return

    client = TelegramClient(SESSION_PATH, TG_API_ID, TG_API_HASH)
    await client.start()
    print("✅ Telegram login OK")

    last_id = load_last_id()
    print("🔁 Last posted ID:", last_id)

    safe_caption = load_safe_caption()

    async for msg in client.iter_messages(TG_CHANNEL, reverse=True):
        if msg.id <= last_id:
            continue

        if isinstance(msg.media, MessageMediaPhoto):
            print(f"📸 Proses MSG ID {msg.id}")

            # Ambil text Telegram (caption + link)
            tg_text = (msg.text or msg.message or "").strip()

            # Download foto
            img_path = await msg.download_media(file=IMG_DIR)
            print("⬇️ Downloaded:", img_path)

            # Upload foto ke FB (caption aman)
            r = upload_photo_to_fb(img_path, safe_caption)
            os.remove(img_path)

            if r.ok:
                data = r.json()
                post_id = data.get("post_id")

                # Post komentar (isi caption + link Telegram)
                if post_id and tg_text:
                    post_fb_comment(post_id, tg_text)

                save_last_id(msg.id)
                save_last_post_time(int(time.time()))
                print("✅ POST BERHASIL, MENUNGGU DELAY BERIKUTNYA")
                break
            else:
                print("⚠️ Upload gagal, lanjut ke pesan berikutnya")

    await client.disconnect()
    print("🔌 Telegram disconnected")

# ===============================
# RUN
# ===============================
asyncio.run(run())
