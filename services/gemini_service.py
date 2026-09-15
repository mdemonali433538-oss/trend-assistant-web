"""
এই মডিউল Google Gemini API-এর সাথে কথা বলে।

দুইটা কাজ করে:
1. generate_trend_suggestions() -> Gemini-এর Google Search grounding tool ব্যবহার করে
   বর্তমানে সোশ্যাল মিডিয়া ও ইউটিউবে কী ট্রেন্ডিং চলছে সেটা রিসার্চ করে, তার সাথে
   YouTube Data API থেকে পাওয়া ডেটা মিলিয়ে ভিডিও টাইটেল/টপিক সাজেস্ট করে।
2. chat_reply() -> ইউজারের সাথে বন্ধুত্বপূর্ণভাবে কথা বলে, দরকার হলে লাইভ সার্চ করে উত্তর দেয়।

নোট: google-genai SDK এখনো দ্রুত পরিবর্তনশীল, তাই ডিপ্লয় করার আগে
https://ai.google.dev/gemini-api/docs দেখে নেওয়া ভালো, method নাম বদলে থাকলে
এখানে আপডেট করে নিও।
"""
import logging

from google import genai
from google.genai import types

import config

logger = logging.getLogger(__name__)

_client: genai.Client | None = None

FRIENDLY_PERSONA = """
তুমি একজন বন্ধুত্বপূর্ণ, উৎসাহী কনটেন্ট স্ট্র্যাটেজিস্ট অ্যাসিস্ট্যান্ট। তোমার কাজ হলো
ইউজারকে তার ইউটিউব চ্যানেলের জন্য ট্রেন্ডিং টপিক ও ভিডিও টাইটেল খুঁজে দেওয়া।

নিয়মাবলি:
- সবসময় বাংলায়, আন্তরিক ও উৎসাহব্যঞ্জক টোনে কথা বলবে (দরকার হলে ইংরেজি টার্মও ব্যবহার করবে)।
- ইমোজি মাঝেমধ্যে ব্যবহার করতে পারো, কিন্তু বেশি না।
- যখন ট্রেন্ড নিয়ে কথা বলবে, নির্দিষ্ট ও কার্যকর সাজেশন দেবে — শুধু সাধারণ কথা নয়।
- প্রতিটা টপিক সাজেশনের সাথে ২-৩টা সম্ভাব্য ভিডিও টাইটেলও দেবে।
- সততার সাথে বলবে যদি কোনো তথ্য নিশ্চিত না হও।
"""


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not config.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY সেট করা নেই।")
        _client = genai.Client(api_key=config.GEMINI_API_KEY)
    return _client


def _search_enabled_config(system_instruction: str) -> types.GenerateContentConfig:
    """Google Search grounding চালু রেখে একটা config বানায়, যাতে Gemini
    রিয়েল-টাইম তথ্য (বর্তমান ট্রেন্ড) নিয়ে উত্তর দিতে পারে।"""
    return types.GenerateContentConfig(
        system_instruction=system_instruction,
        tools=[types.Tool(google_search=types.GoogleSearch())],
        temperature=0.9,
    )


def generate_trend_suggestions(youtube_trends: list[dict], niche: str) -> str:
    """
    YouTube trending ডেটা + Gemini-এর লাইভ সার্চ ব্যবহার করে
    ভিডিও টাইটেল ও টপিক সাজেশন তৈরি করে (বাংলায়, ফ্রেন্ডলি টোনে)।
    """
    client = _get_client()

    trend_lines = "\n".join(
        f"- {v['title']} (চ্যানেল: {v['channel']}, ভিউ: {v['views']:,})"
        for v in youtube_trends[:10]
    ) or "কোনো YouTube ডেটা পাওয়া যায়নি।"

    prompt = f"""
নিচে এখন YouTube-এ ({config.YOUTUBE_REGION_CODE} অঞ্চলে) সবচেয়ে জনপ্রিয় কিছু ভিডিওর লিস্ট দেওয়া হলো:

{trend_lines}

আমার চ্যানেলের বিষয়/niche হলো: "{niche}"

তোমার কাজ:
1. উপরের ট্রেন্ড এবং তোমার নিজের লাইভ সার্চের মাধ্যমে এখন সোশ্যাল মিডিয়া
   (YouTube, Facebook, TikTok/Reels, X/Twitter) জুড়ে কী কী বিষয় ট্রেন্ডিং চলছে
   সেটা সংক্ষেপে বের করো।
2. আমার niche-এর সাথে মিলিয়ে ৪-৫টা ভিডিও টপিক আইডিয়া দাও।
3. প্রতিটা টপিকের জন্য ২-৩টা আকর্ষণীয়, ক্লিকযোগ্য ভিডিও টাইটেল সাজেস্ট করো।
4. বন্ধুর মতো আন্তরিকভাবে লেখো, বুলেট পয়েন্ট ব্যবহার করো যাতে সহজে পড়া যায়।
"""

    response = client.models.generate_content(
        model=config.GEMINI_MODEL,
        contents=prompt,
        config=_search_enabled_config(FRIENDLY_PERSONA),
    )
    return response.text or "দুঃখিত, এই মুহূর্তে কোনো সাজেশন তৈরি করতে পারলাম না। আবার চেষ্টা করো।"


def chat_reply(user_message: str, history: list[dict]) -> str:
    """
    ইউজারের সাথে সাধারণ কথোপকথনের জন্য ব্যবহৃত হয়। প্রয়োজনে লাইভ সার্চও করতে পারবে
    (যেমন ইউজার যদি জিজ্ঞেস করে "আজকে কী ট্রেন্ডিং চলছে?")।

    history: [{"role": "user"/"model", "text": "..."}] ফরম্যাটে আগের কথোপকথন।
    """
    client = _get_client()

    contents = []
    for turn in history[-10:]:  # শুধু শেষ ১০টা মেসেজ কনটেক্সট হিসেবে রাখা হচ্ছে
        contents.append(
            types.Content(role=turn["role"], parts=[types.Part.from_text(text=turn["text"])])
        )
    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_message)]))

    response = client.models.generate_content(
        model=config.GEMINI_MODEL,
        contents=contents,
        config=_search_enabled_config(FRIENDLY_PERSONA),
    )
    return response.text or "উফ, বুঝতে একটু সমস্যা হলো। আরেকবার বলবে?"
