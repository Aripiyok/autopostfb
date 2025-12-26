import os
import random
import requests
import asyncio
import time
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

# 🔥 DELAY DARI ENV (MENIT → DETIK)
POST_DELAY_MINUTES = int(os.getenv("POST_DELAY_MINUTES", "60"))
POST_DELAY_SECONDS = POST_DELAY_MINUTES * 60

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
# LOAD LAST ID
# ===============================
def load_last_id():
    if not os.path.exists(LAST_ID_FILE):
        return 0
    return int(open(LAST_ID_FILE).read().strip() or 0)

def save_last_id(msg_id):
    with open(LAST_ID_FILE, "w") as f:
        f.write(str(msg_id))

# ===============================
# LOAD LAST POST TIME
# ===============================
def load_last_post_time():
    if not os.path.exists(LAST_TIME_FILE):
        return 0
    return int(open(LAST_TIME_FILE).read().strip() or 0)

def save_last_post_time(ts):
    with open(LAST_TIME_FILE, "w") as f:
        f.write(str(ts))

# ===============================
# LOAD CAPTION
# ===============================
def load_caption():
    if not os.path.exists(CAPTION_FILE):
        return ""
    with open(CAPTION_FILE, "r", encoding="utf-8") as f:
        caps = [x.strip() for x in f if x.strip()]
    return random.choice(caps) if caps else ""

# ===============================
# FACEBOOK UPLOAD
# ===============================
def upload_to_fb(img_path, caption):
    url = f"https://graph.facebook.com/v24.0/{FB_PAGE_ID}/photos"
    with open(img_path, "rb") as img:
        r = requests.post(
            url,
            files={"source": img},
            data={
                "caption": caption,
                "access_token": FB_PAGE_TOKEN
            },
            timeout=60
        )
    print("📤 FB RESPONSE:", r.text)
    return r.ok

# ===============================
# MAIN
# ===============================
async def run():
    now = int(time.time())
    last_post_time = load_last_post_time()

    # 🔥 CEK DELAY
    if now - last_post_time < POST_DELAY_SECONDS:
        wait = POST_DELAY_SECONDS - (now - last_post_time)
        print(f"⏳ Belum waktunya posting. Tunggu {wait//60} menit lagi.")
        return

    client = TelegramClient(SESSION_PATH, TG_API_ID, TG_API_HASH)
    await client.start()
    print("✅ Telegram login OK")

    last_id = load_last_id()
    print("🔁 Last posted ID:", last_id)

    caption = load_caption()

    async for msg in client.iter_messages(TG_CHANNEL, reverse=True):
        if msg.id <= last_id:
            continue

        if isinstance(msg.media, MessageMediaPhoto):
            print(f"📸 Posting MSG ID {msg.id}")

            img_path = await msg.download_media(file=IMG_DIR)
            success = upload_to_fb(img_path, caption)
            os.remove(img_path)

            if success:
                save_last_id(msg.id)
                save_last_post_time(int(time.time()))
                print("✅ POST BERHASIL, DELAY DIMULAI")
                break

    await client.disconnect()
    print("🔌 Telegram disconnected")

# ===============================
# RUN
# ===============================
asyncio.run(run())
