"""
এই ফাইলটা Render-এ Web Service হিসেবে রান হবে।
এটা একটা ব্রাউজার-বেসড চ্যাট ইন্টারফেস দেয় (Telegram বা কোনো অ্যাপ লাগবে না) —
তুমি শুধু তোমার Render URL ব্রাউজারে খুললেই অ্যাসিস্ট্যান্টের সাথে কথা বলতে পারবে।

এছাড়া এটা ব্যাকগ্রাউন্ডে নির্দিষ্ট সময় পরপর ট্রেন্ড চেক করে, এবং তুমি পেজ
রিফ্রেশ/ওপেন করলেই সবশেষ সাজেশনটা দেখতে পাবে।

রান করার কমান্ড: python app.py
"""
import logging
from functools import wraps

from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from apscheduler.schedulers.background import BackgroundScheduler

import config
from services import gemini_service, youtube_service

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# --- সবশেষ ট্রেন্ড সাজেশন মেমোরিতে রাখা হচ্ছে (সিম্পল ক্যাশ) ---
# নোট: Render রিস্টার্ট/রিডিপ্লয় হলে এই ডেটা মুছে যাবে — এটা একটা সিম্পল
# in-memory ক্যাশ, ডাটাবেস নয়।
_latest_trends_cache = {"text": None, "generated_at": None}


# ---------------------------------------------------------------------------
# ঐচ্ছিক পাসওয়ার্ড প্রোটেকশন (ACCESS_PASSWORD সেট করা থাকলেই চালু হবে)
# ---------------------------------------------------------------------------
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if config.ACCESS_PASSWORD and not session.get("authenticated"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


@app.route("/login", methods=["GET", "POST"])
def login():
    if not config.ACCESS_PASSWORD:
        return redirect(url_for("index"))

    error = None
    if request.method == "POST":
        if request.form.get("password") == config.ACCESS_PASSWORD:
            session["authenticated"] = True
            return redirect(url_for("index"))
        error = "পাসওয়ার্ড ভুল হয়েছে, আবার চেষ্টা করো।"
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.pop("authenticated", None)
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# মূল পেজ
# ---------------------------------------------------------------------------
@app.route("/")
@login_required
def index():
    return render_template("index.html", niche=config.CONTENT_NICHE)


# ---------------------------------------------------------------------------
# API: চ্যাট
# ---------------------------------------------------------------------------
@app.route("/api/chat", methods=["POST"])
@login_required
def api_chat():
    data = request.get_json(force=True) or {}
    user_message = (data.get("message") or "").strip()
    history = data.get("history") or []  # ব্রাউজার নিজেই আগের কথোপকথন পাঠাবে

    if not user_message:
        return jsonify({"error": "মেসেজ খালি থাকতে পারবে না।"}), 400

    try:
        reply = gemini_service.chat_reply(user_message, history)
    except Exception as exc:  # noqa: BLE001
        logger.error("চ্যাট রিপ্লাই তৈরি করতে সমস্যা: %s", exc)
        return jsonify({"error": "উত্তর তৈরি করতে সমস্যা হয়েছে, একটু পরে আবার চেষ্টা করো।"}), 500

    return jsonify({"reply": reply})


# ---------------------------------------------------------------------------
# API: এখনই ট্রেন্ড চেক করা (অন-ডিমান্ড বাটনের জন্য)
# ---------------------------------------------------------------------------
@app.route("/api/trends", methods=["POST"])
@login_required
def api_trends():
    data = request.get_json(silent=True) or {}
    niche = (data.get("niche") or config.CONTENT_NICHE).strip()

    try:
        result = _run_trend_check(niche)
    except Exception as exc:  # noqa: BLE001
        logger.error("ট্রেন্ড চেক করতে সমস্যা: %s", exc)
        return jsonify({"error": "ট্রেন্ড আনতে সমস্যা হয়েছে, একটু পরে আবার চেষ্টা করো।"}), 500

    return jsonify(result)


# ---------------------------------------------------------------------------
# API: শেষবার (ব্যাকগ্রাউন্ডে) জেনারেট হওয়া ট্রেন্ড দেখা, পেজ লোড হলে ব্যবহৃত হয়
# ---------------------------------------------------------------------------
@app.route("/api/latest-trends")
@login_required
def api_latest_trends():
    return jsonify(_latest_trends_cache)


def _run_trend_check(niche: str) -> dict:
    yt_trends = youtube_service.get_trending_videos()
    suggestion = gemini_service.generate_trend_suggestions(yt_trends, niche)

    from datetime import datetime

    result = {"text": suggestion, "generated_at": datetime.utcnow().isoformat() + "Z"}
    _latest_trends_cache.update(result)
    return result


# ---------------------------------------------------------------------------
# ব্যাকগ্রাউন্ড শিডিউলার — নির্দিষ্ট সময় পরপর অটোমেটিক ট্রেন্ড চেক
# ---------------------------------------------------------------------------
def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        lambda: _run_trend_check(config.CONTENT_NICHE),
        "interval",
        hours=config.TREND_CHECK_INTERVAL_HOURS,
        next_run_time=None,  # অ্যাপ চালু হবার সাথে সাথে প্রথমবার রান করবে না, নিচে ম্যানুয়ালি ট্রিগার করা হচ্ছে
    )
    scheduler.start()
    logger.info(
        "ব্যাকগ্রাউন্ড শিডিউলার চালু হয়েছে — প্রতি %s ঘণ্টা পরপর ট্রেন্ড চেক হবে।",
        config.TREND_CHECK_INTERVAL_HOURS,
    )
    return scheduler


# মডিউল লোড হবার সাথে সাথেই কনফিগ চেক ও শিডিউলার চালু হয়ে যায় — এটা `python app.py`
# এবং `gunicorn app:app` দুই ক্ষেত্রেই কাজ করার জন্য দরকার (gunicorn __main__ ব্লক
# চালায় না, শুধু module import করে)।
config.validate_config()
start_scheduler()

if __name__ == "__main__":
    logger.info("ওয়েব সার্ভার চালু হচ্ছে http://0.0.0.0:%s -এ", config.PORT)
    app.run(host="0.0.0.0", port=config.PORT, debug=False, use_reloader=False)
