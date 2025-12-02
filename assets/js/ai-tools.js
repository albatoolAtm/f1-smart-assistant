// assets/ai-tools.js

// الباكند عندنا على /api
const API_BASE = "http://127.0.0.1:8000/api";

// Helper: استدعاء API عام
async function callApi(endpoint, payload) {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }
  return res.json();
}

/* ==========================
   Sentiment Page (dashboard/sentiment.html)
   ========================== */
const sentimentForm = document.getElementById("sentiment-form");
const sentimentInput = document.getElementById("sentiment-text");
const sentimentLang = document.getElementById("sentiment-language");
const sentimentResult = document.getElementById("sentiment-result");
const sentimentStatus = document.getElementById("sentiment-status");
const sentimentExtra = document.getElementById("sentiment-extra");
const sentimentLabelBadge = document.getElementById("sentiment-label-badge");
const sentimentScoreValue = document.getElementById("sentiment-score-value");
const sentimentExplanation = document.getElementById("sentiment-explanation");

if (sentimentForm && sentimentInput && sentimentResult) {
  sentimentForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const text = sentimentInput.value.trim();
    const language = sentimentLang ? sentimentLang.value : "auto";

    if (!text) {
      sentimentResult.textContent = "Please paste some text first.";
      if (sentimentStatus) {
        sentimentStatus.textContent = "Paste text and click “Analyze mood”.";
      }
      return;
    }

    sentimentResult.textContent = "Analyzing mood…";
    if (sentimentStatus) {
      sentimentStatus.textContent = "Contacting sentiment agent...";
    }

    try {
      // ✅ انتبهي: الآن نستخدم /ai/sentiment
      const data = await callApi("/ai/sentiment", { text, language });

      const label = data.label || data.sentiment || "neutral";
      const score = typeof data.score === "number" ? data.score : 0;
      const explanationText = data.explanation || "";

      // النتيجة الأساسية
      sentimentResult.classList.remove("empty-state");
      sentimentResult.textContent = `Detected sentiment: ${label}`;

      // إظهار معلومات إضافية
      if (sentimentExtra) {
        sentimentExtra.classList.remove("hidden");
      }
      if (sentimentLabelBadge) {
        sentimentLabelBadge.textContent = label;
      }
      if (sentimentScoreValue) {
        const pct = Math.round(Math.abs(score) * 100);
        sentimentScoreValue.textContent =
          score === 0 ? "–" : `${pct}% (${score.toFixed(2)})`;
      }
      if (sentimentExplanation) {
        sentimentExplanation.textContent = explanationText;
      }
      if (sentimentStatus) {
        sentimentStatus.textContent = "Sentiment analyzed successfully.";
      }
    } catch (err) {
      console.error(err);
      sentimentResult.textContent = "Error calling sentiment API.";
      if (sentimentStatus) {
        sentimentStatus.textContent =
          "Error: could not contact sentiment backend.";
      }
      if (sentimentExtra) {
        sentimentExtra.classList.add("hidden");
      }
    }
  });
}

/* ==========================
   Simple Summary Page (لو استخدمتيها)
   ========================== */
const summaryForm = document.getElementById("summary-form");
const summaryInput = document.getElementById("summary-text");
const summaryOutput = document.getElementById("summary-result");

if (summaryForm && summaryInput && summaryOutput) {
  summaryForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const text = summaryInput.value.trim();
    if (!text) {
      summaryOutput.textContent = "Please paste some text first.";
      return;
    }

    summaryOutput.textContent = "Summarizing…";

    try {
      // ✅ نوجّه على /ai/summary عشان يطابق الباكند
      const data = await callApi("/ai/summary", {
        text,
        language: "en",
        length: "medium",
      });
      summaryOutput.textContent = data.summary || "No summary returned.";
    } catch (err) {
      console.error(err);
      summaryOutput.textContent = "Error calling summary API.";
    }
  });
}

/* ==========================
   Simple Q&A Page (لو استخدمتيها)
   ========================== */
const qaForm = document.getElementById("qa-form");
const qaInput = document.getElementById("qa-text");
const qaResult = document.getElementById("qa-result");

if (qaForm && qaInput && qaResult) {
  qaForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const text = qaInput.value.trim();
    if (!text) {
      qaResult.textContent = "Please write your question.";
      return;
    }

    qaResult.textContent = "Thinking like an F1 engineer…";

    try {
      // ✅ نربط /ai/qa بالـ planner + agents
      const data = await callApi("/ai/qa", {
        context: "",
        question: text,
        language: "auto",
      });
      qaResult.textContent =
        data.answer || data.result || "No answer returned.";
    } catch (err) {
      console.error(err);
      qaResult.textContent = "Error calling Q&A API.";
    }
  });
}
