import os
import random
import requests
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto

# ===============================
# LOAD ENV
# ===============================
load_dotenv()

# ===============================
# TELEGRAM
# ===============================
TG_API_ID = int(os.getenv("TG_API_ID"))
TG_API_HASH = os.getenv("TG_API_HASH")
TG_CHANNEL = int(os.getenv("TG_CHANNEL"))

# ===============================
# FACEBOOK
# ===============================
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN")

# ===============================
# PATH SETUP (ABSOLUTE – FIX SQLITE)
# ===============================
BASE_DIR = "/root/autopostfb"
SESSION_DIR = os.path.join(BASE_DIR, "session")
IMG_DIR = os.path.join(BASE_DIR, "images")
CAPTION_FILE = os.path.join(BASE_DIR, "caption.txt")

os.makedirs(SESSION_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

SESSION_PATH = os.path.join(SESSION_DIR, "ultra")

# ===============================
# LOAD CAPTION
# ===============================
def load_caption():
    if not os.path.exists(CAPTION_FILE):
        return ""
    with open(CAPTION_FILE, "r", encoding="utf-8") as f:
        captions = [x.strip() for x in f if x.strip()]
    return random.choice(captions) if captions else ""

# ===============================
# TELETHON CLIENT
# ===============================
client = TelegramClient(SESSION_PATH, TG_API_ID, TG_API_HASH)

# ===============================
# MAIN LOGIC
# ===============================
async def run():
    await client.start()
    print("✅ Telegram login OK")

    caption = load_caption()
    print("📝 Caption:", caption if caption else "(kosong)")

    posted = False

    async for msg in client.iter_messages(TG_CHANNEL, limit=10):
        print(f"🔍 DEBUG MSG ID {msg.id} | media={type(msg.media)}")

        # ===============================
        # FOTO TUNGGAL
        # ===============================
        if msg.media and isinstance(msg.media, MessageMediaPhoto):
            print("📸 FOTO TUNGGAL DITEMUKAN")

            img_path = await msg.download_media(file=IMG_DIR)
            print("⬇️ Downloaded:", img_path)

            url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
            with open(img_path, "rb") as f:
                r = requests.post(
                    url,
                    data={
                        "caption": caption,
                        "access_token": FB_PAGE_TOKEN
                    },
                    files={"source": f},
                    timeout=30
                )

            print("📤 FB RESPONSE:", r.text)
            os.remove(img_path)
            posted = True
            break

        # ===============================
        # FOTO DARI ALBUM
        # ===============================
        if msg.grouped_id and msg.photo:
            print("📸 FOTO ALBUM DITEMUKAN")

            img_path = await msg.download_media(file=IMG_DIR)
            print("⬇️ Downloaded:", img_path)

            url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
            with open(img_path, "rb") as f:
                r = requests.post(
                    url,
                    data={
                        "caption": caption,
                        "access_token": FB_PAGE_TOKEN
                    },
                    files={"source": f},
                    timeout=30
                )

            print("📤 FB RESPONSE:", r.text)
            os.remove(img_path)
            posted = True
            break

    if not posted:
        print("⚠️ TIDAK ADA FOTO YANG BISA DIPOST")

    await client.disconnect()
    print("🔌 Telegram disconnected")

# ===============================
# RUN
# ===============================
with client:
    client.loop.run_until_complete(run())
