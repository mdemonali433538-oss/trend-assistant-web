# ট্রেন্ড রিসার্চ অ্যাসিস্ট্যান্ট — ব্রাউজার ভার্সন 🤖📈

এটা একটা পাইথন-ভিত্তিক এআই অ্যাসিস্ট্যান্ট যেটা তুমি **সরাসরি ব্রাউজারে** খুলে
ব্যবহার করবে — কোনো অ্যাপ ইনস্টল বা Telegram লাগবে না। Render-এ ডিপ্লয় করার পর
তুমি একটা লিংক পাবে (যেমন `https://trend-assistant-web.onrender.com`), সেটা
খুললেই চ্যাট ইন্টারফেস চলে আসবে।

## এটা কী করে
- Google Gemini API (Google Search grounding সহ) ব্যবহার করে বর্তমানে YouTube ও
  সোশ্যাল মিডিয়ায় কী ট্রেন্ডিং চলছে তা রিসার্চ করে
- YouTube Data API থেকে সরাসরি জনপ্রিয় ভিডিওর তথ্য নেয়
- ভিডিও টাইটেল ও টপিক সাজেস্ট করে
- "এখনই চেক করো" বাটনে চাপলে সাথে সাথে নতুন সাজেশন দেয়
- ব্যাকগ্রাউন্ডে প্রতি কয়েক ঘণ্টা পরপর (ডিফল্ট ৬ ঘণ্টা) নিজে থেকেই নতুন ট্রেন্ড
  চেক করে রাখে, তুমি পেজ খুললেই সবশেষটা দেখতে পাবে
- নিচে একটা চ্যাট বক্সও আছে যেখানে ফ্রি-ফর্মে কথা বলা যায়

## ফাইল স্ট্রাকচার

```
trend-assistant-web/
├── app.py                     # Flask সার্ভার — চ্যাট ও ট্রেন্ড API + ব্যাকগ্রাউন্ড শিডিউলার
├── config.py                  # এনভায়রনমেন্ট ভ্যারিয়েবল লোড করে
├── requirements.txt
├── render.yaml                # Render ডিপ্লয়মেন্ট ব্লুপ্রিন্ট (Web Service হিসেবে)
├── .env.example
├── .gitignore
├── README.md
├── services/
│   ├── __init__.py
│   ├── gemini_service.py      # Gemini API কল (ট্রেন্ড সাজেশন + চ্যাট রিপ্লাই)
│   └── youtube_service.py     # YouTube Data API থেকে ট্রেন্ডিং ভিডিও আনে
├── templates/
│   ├── index.html             # মূল চ্যাট পেজ
│   └── login.html             # ঐচ্ছিক পাসওয়ার্ড-লগইন পেজ
└── static/
    ├── style.css
    └── app.js
```

---

## ধাপ ১ — API Key সংগ্রহ (এবার Telegram লাগবে না, মাত্র ২টা key)

### ১.১ Gemini API Key
1. যাও: https://aistudio.google.com/apikey
2. "Create API key" চাপো, কপি করো — এটা `GEMINI_API_KEY`।

### ১.২ YouTube Data API Key
1. যাও: https://console.cloud.google.com/
2. নতুন প্রজেক্ট বানাও।
3. "APIs & Services" → "Library" → **YouTube Data API v3** সার্চ করে Enable করো।
4. "Credentials" → "Create Credentials" → "API key" — এটা `YOUTUBE_API_KEY`।

> চাইলে `ACCESS_PASSWORD` নামে একটা এনভায়রনমেন্ট ভ্যারিয়েবলও সেট করতে পারো —
> সেট করলে পেজ খোলার আগে পাসওয়ার্ড চাইবে (যেহেতু Render-এর URL সবার জন্য
> পাবলিকলি খোলা থাকে, এটা সেট করে রাখাই ভালো)।

---

## ধাপ ২ — লোকালি টেস্ট করা (ঐচ্ছিক)

```bash
cd trend-assistant-web
python -m venv venv
source venv/bin/activate      # Windows-এ: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# .env ফাইল খুলে নিজের আসল key বসাও

python app.py
```

টার্মিনালে "ওয়েব সার্ভার চালু হচ্ছে..." দেখলে ব্রাউজারে যাও:
`http://localhost:10000`

---

## ধাপ ৩ — GitHub-এ আপলোড করা

```bash
cd trend-assistant-web
git init
git add .
git commit -m "Initial commit: browser-based trend assistant"

git remote add origin https://github.com/<তোমার-ইউজারনেম>/trend-assistant-web.git
git branch -M main
git push -u origin main
```

---

## ধাপ ৪ — Render.com-এ ডিপ্লয় করা (এবার Web Service, Background Worker না)

### পদ্ধতি A: render.yaml দিয়ে
1. https://dashboard.render.com/ এ GitHub দিয়ে লগইন করো।
2. "New +" → **"Blueprint"** সিলেক্ট করো, তোমার রিপোজিটরি বেছে নাও।
3. Render নিজে থেকেই `render.yaml` পড়বে (এবার এটা `type: web`, তাই একটা পাবলিক
   URL দেবে)।
4. `GEMINI_API_KEY`, `YOUTUBE_API_KEY` (এবং চাইলে `ACCESS_PASSWORD`, `SECRET_KEY`)
   বসিয়ে "Apply" চাপো।

### পদ্ধতি B: ম্যানুয়ালি
1. "New +" → **"Web Service"** সিলেক্ট করো, রিপোজিটরি কানেক্ট করো।
2. সেটিংস:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn -w 1 --threads 4 -b 0.0.0.0:$PORT app:app`
3. "Environment" ট্যাবে গিয়ে `GEMINI_API_KEY`, `YOUTUBE_API_KEY` (ও ঐচ্ছিক ভ্যারিয়েবল) যোগ করো।
4. "Create Web Service" চাপো।

বিল্ড শেষ হলে Render তোমাকে একটা URL দেবে (যেমন `https://trend-assistant-web.onrender.com`)।
সেটা ব্রাউজারে খুললেই তোমার অ্যাসিস্ট্যান্ট রেডি!

---

## গুরুত্বপূর্ণ নোট

- **`-w 1` মানে ১টা gunicorn worker** — ইচ্ছাকৃতভাবে ১ রাখা হয়েছে, কারণ ব্যাকগ্রাউন্ড
  শিডিউলার ও ট্রেন্ড ক্যাশ মেমোরিতে থাকে; একাধিক worker চালালে প্রতিটা worker
  আলাদা করে শিডিউলার চালাবে, যেটা অপ্রয়োজনীয় বাড়তি Gemini/YouTube API কল করবে।
- **ফ্রি প্ল্যানে Render Web Service** কিছুক্ষণ ব্যবহার না হলে ঘুমিয়ে যায় (spin down),
  পরের রিকোয়েস্টে জেগে উঠতে ৩০-৫০ সেকেন্ড লাগতে পারে। পুরোপুরি ২৪/৭ সবসময়
  সচল রাখতে চাইলে Render-এর Paid প্ল্যান লাগবে।
- **চ্যাট হিস্টোরি ব্রাউজারে (in-memory) থাকে** — পেজ রিফ্রেশ দিলে মুছে যাবে।
- **URL পাবলিক** — যে কেউ লিংক পেলে খুলতে পারবে, তাই `ACCESS_PASSWORD` সেট করে
  রাখাটা রেকমেন্ড করছি।
- ট্রেন্ড ক্যাশ ও সাজেশন মেমোরিতে থাকে, রিডিপ্লয়/রিস্টার্ট হলে মুছে যায়।

## ভবিষ্যতে যা যোগ করতে পারো
- ট্রেন্ড হিস্টোরি ডেটাবেসে (SQLite/Postgres) সেভ করা
- চ্যাট হিস্টোরি সার্ভার-সাইডে সেভ রাখা
- একাধিক niche-এর জন্য আলাদা ট্যাব
- Google Trends ডেটা যোগ করা (`pytrends` লাইব্রেরি দিয়ে)
