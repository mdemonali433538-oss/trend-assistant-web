const chatLog = document.getElementById("chat-log");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const trendsContent = document.getElementById("trends-content");
const trendsMeta = document.getElementById("trends-meta");
const refreshBtn = document.getElementById("refresh-trends-btn");
const nicheInput = document.getElementById("niche-input");

// ব্রাউজারেই কথোপকথনের হিস্টোরি রাখা হচ্ছে (রিফ্রেশ দিলে মুছে যাবে)
let history = [];

function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = "msg " + (role === "user" ? "msg-user" : "msg-model");
  div.textContent = text;
  chatLog.appendChild(div);
  chatLog.scrollTop = chatLog.scrollHeight;
}

chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;

  addMessage("user", message);
  chatInput.value = "";
  chatInput.disabled = true;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history }),
    });
    const data = await res.json();
    if (data.error) {
      addMessage("model", "⚠️ " + data.error);
    } else {
      addMessage("model", data.reply);
      history.push({ role: "user", text: message });
      history.push({ role: "model", text: data.reply });
      history = history.slice(-20); // বেশি বড় না হয়ে যায়
    }
  } catch (err) {
    addMessage("model", "⚠️ সার্ভারে সংযোগ করতে সমস্যা হয়েছে।");
  } finally {
    chatInput.disabled = false;
    chatInput.focus();
  }
});

function formatTime(isoString) {
  if (!isoString) return "";
  const date = new Date(isoString);
  return date.toLocaleString("bn-BD", { hour: "2-digit", minute: "2-digit", day: "2-digit", month: "short" });
}

async function loadLatestTrends() {
  try {
    const res = await fetch("/api/latest-trends");
    const data = await res.json();
    if (data.text) {
      trendsContent.textContent = data.text;
      trendsMeta.textContent = "সর্বশেষ আপডেট: " + formatTime(data.generated_at);
    }
  } catch (err) {
    // চুপচাপ থাকা — প্রথমবার হয়তো এখনও কিছু জেনারেট হয়নি
  }
}

refreshBtn.addEventListener("click", async () => {
  refreshBtn.disabled = true;
  refreshBtn.textContent = "খুঁজছি...";
  trendsContent.textContent = "একটু অপেক্ষা করো, ট্রেন্ড রিসার্চ করা হচ্ছে... 🔍";

  try {
    const res = await fetch("/api/trends", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ niche: nicheInput.value.trim() }),
    });
    const data = await res.json();
    if (data.error) {
      trendsContent.textContent = "⚠️ " + data.error;
    } else {
      trendsContent.textContent = data.text;
      trendsMeta.textContent = "সর্বশেষ আপডেট: " + formatTime(data.generated_at);
    }
  } catch (err) {
    trendsContent.textContent = "⚠️ সার্ভারে সংযোগ করতে সমস্যা হয়েছে।";
  } finally {
    refreshBtn.disabled = false;
    refreshBtn.textContent = "এখনই চেক করো 🔍";
  }
});

loadLatestTrends();
