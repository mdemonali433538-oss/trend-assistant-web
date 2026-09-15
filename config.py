"""
সব এনভায়রনমেন্ট ভ্যারিয়েবল/সেটিংস এই ফাইলে থাকবে।
Render ডিপ্লয়মেন্টে এই ভ্যালুগুলো Environment Variables হিসেবে সেট করতে হবে।
"""
import os
import secrets

from dotenv import load_dotenv

load_dotenv()

# --- ফিলিং রিকয়ার্ড কী ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- ঐচ্ছিক ---
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
YOUTUBE_REGION_CODE = os.environ.get("YOUTUBE_REGION_CODE", "BD")
TREND_CHECK_INTERVAL_HOURS = float(os.environ.get("TREND_CHECK_INTERVAL_HOURS", "6"))
CONTENT_NICHE = os.environ.get("CONTENT_NICHE", "general")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")

# তোমার পেজটা যদি পাবলিক ইন্টারনেটে খোলা থাকে, চাইলে একটা সিম্পল পাসওয়ার্ড
# দিয়ে প্রোটেক্ট করতে পারো। সেট না করলে সবাই তোমার পেজ খুলতে পারবে।
ACCESS_PASSWORD = os.environ.get("ACCESS_PASSWORD")

# Flask সেশন এনক্রিপ্ট করতে ব্যবহৃত হয়। Render-এ এনভায়রনমেন্ট ভ্যারিয়েবল হিসেবে
# নিজে একটা র‍্যান্ডম স্ট্রিং সেট করে দেওয়াই ভালো, না দিলে প্রতি রিস্টার্টে
# নতুন করে জেনারেট হবে (তখন আগের লগইন সেশন উড়ে যাবে, কিন্তু সমস্যা নেই)।
SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_hex(16))

PORT = int(os.environ.get("PORT", "10000"))


def validate_config():
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY সেট করা নেই। Render Dashboard -> Environment ট্যাবে গিয়ে সেট করো।"
        )
