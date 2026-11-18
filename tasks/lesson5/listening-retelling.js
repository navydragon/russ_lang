const textEl = document.getElementById("text");
const btnSend = document.getElementById("btnSend");
const btnClear = document.getElementById("btnClear");
const highlightedEl = document.getElementById("highlighted");
const errorsEl = document.getElementById("errors");
const hintEl = document.getElementById("hint");
const resultHintEl = document.getElementById("resultHint");
const resultHeaderEl = document.getElementById("resultHeader");
const resultStatusEl = document.getElementById("resultStatus");
const resultMetaEl = document.getElementById("resultMeta");
const resultScoreEl = document.getElementById("resultScore");
const resultFeedbackEl = document.getElementById("resultFeedback");
const resultQualityEl = document.getElementById("resultQuality");
const resultRecommendationsWrapEl = document.getElementById("resultRecommendationsWrap");
const resultRecommendationsEl = document.getElementById("resultRecommendations");
const resultCardEl = document.getElementById("resultCard");
const errorsCardEl = document.getElementById("errorsCard");

const referenceAudio = document.getElementById("referenceAudio");
const listenButton = document.getElementById("listenReference");
const listenCount = document.getElementById("listenCount");
const LISTEN_STORAGE_KEY = `${TASK_CODE}_plays_v1`;
let plays = Number(sessionStorage.getItem(LISTEN_STORAGE_KEY) || 0);
function updatePlays() { listenCount.textContent = `Прослушиваний: ${plays} из 2`; listenButton.disabled = plays >= 2 || !referenceAudio.paused; }
listenButton.addEventListener("click", async () => {
  if (plays >= 2) return;
  try { referenceAudio.currentTime = 0; await referenceAudio.play(); plays += 1; sessionStorage.setItem(LISTEN_STORAGE_KEY, String(plays)); updatePlays(); }
  catch (_) { listenCount.textContent = "Не удалось воспроизвести запись. Попробуйте ещё раз."; }
});
document.getElementById("restartListening").addEventListener("click", () => {
  referenceAudio.pause();
  referenceAudio.currentTime = 0;
  plays = 0;
  sessionStorage.removeItem(LISTEN_STORAGE_KEY);
  updatePlays();
});
referenceAudio.addEventListener("ended", updatePlays);
referenceAudio.addEventListener("pause", updatePlays);
updatePlays();
const SEND_BTN_LABEL = "Отправить";
const API = window.ANALYZER_CONFIG.apiBaseUrl;

function getStudentCode() {
  const match = document.cookie.match(/(?:^|;\s*)student_code=([^;]*)/);
  if (!match) return "";
  try {
    return decodeURIComponent(match[1].trim());
  } catch (_) {
    return match[1].trim();
  }
}

function panelLoader(message) {
  return `<div class="panel-loader d-flex flex-column align-items-center justify-content-center text-muted py-4" aria-busy="true">
    <div class="spinner-border text-primary mb-2" role="status" style="width: 2rem; height: 2rem;">
      <span class="visually-hidden">Загрузка…</span>
    </div>
    <div class="small">${escapeHtml(message)}</div>
  </div>`;
}

function setLoading(b) {
  btnSend.disabled = b;
  btnClear.disabled = b;
  textEl.disabled = b;
  if (resultCardEl) resultCardEl.classList.toggle("is-loading", b);
  if (errorsCardEl) errorsCardEl.classList.toggle("is-loading", b);
  if (b) {
    btnSend.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Проверка…';
    hintEl.innerHTML = '<span class="badge rounded-pill text-bg-info d-inline-flex align-items-center gap-1"><span class="spinner-grow spinner-grow-sm" aria-hidden="true"></span>Обработка…</span>';
  } else {
    btnSend.textContent = SEND_BTN_LABEL;
    hintEl.innerHTML = "";
  }
}

function showAwaitingResults() {
  clearStatus();
  if (resultHintEl) {
    resultHintEl.innerHTML = '<span class="d-inline-flex align-items-center gap-2 text-primary"><span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span><span>Проверяем рассказ с помощью ИИ…</span></span>';
  }
  highlightedEl.innerHTML = panelLoader("Анализируем текст…");
  errorsEl.innerHTML = `<li class="list-unstyled">${panelLoader("Ищем ошибки…")}</li>`;
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function mergeErrorSpans(errors, textLen) {
  const clean = (Array.isArray(errors) ? errors : [])
    .map(e => ({
      start: Number(e.start),
      end: Number(e.end),
      message: String(e.message || ""),
      code: String(e.code || "")
    }))
    .filter(e => Number.isFinite(e.start) && Number.isFinite(e.end) && e.start >= 0 && e.end > e.start && e.end <= textLen)
    .sort((a, b) => (a.start - b.start) || (b.end - a.end));

  const merged = [];
  for (const e of clean) {
    const last = merged[merged.length - 1];
    if (!last || e.start > last.end) {
      merged.push({ start: e.start, end: e.end, items: [e] });
      continue;
    }
    // overlap/adjacent: merge
    last.end = Math.max(last.end, e.end);
    last.items.push(e);
  }
  return merged;
}

function renderHighlightedText(text, errors) {
  const t = String(text || "");
  const spans = mergeErrorSpans(errors, t.length);
  if (!t) return "";
  if (!spans.length) return escapeHtml(t);

  let out = "";
  let cur = 0;
  for (const s of spans) {
    if (s.start > cur) out += escapeHtml(t.slice(cur, s.start));
    const frag = t.slice(s.start, s.end);
    const title = s.items.map(x => x.message).filter(Boolean).join(" • ");
    out += `<span class="err" title="${escapeHtml(title)}">${escapeHtml(frag)}</span>`;
    cur = s.end;
  }
  if (cur < t.length) out += escapeHtml(t.slice(cur));
  return out;
}

function renderErrorsList(errors) {
  const items = Array.isArray(errors) ? errors : [];
  if (!items.length) {
    errorsEl.innerHTML = '<li class="text-success fw-semibold">Ошибок не найдено</li>';
    return;
  }
  const html = items
    .slice(0, 200)
    .map((e) => {
      const msg = escapeHtml(e.message || "");
      const code = escapeHtml(e.code || "");
      return `<li><span class="badge text-bg-danger me-2">${code || "err"}</span>${msg}</li>`;
    })
    .join("");
  errorsEl.innerHTML = html;
}

function setResultHeaderState(_state) { /* no-op: шапку не раскрашиваем */ }

function setStatusOk() {
  if (!resultStatusEl) return;
  resultStatusEl.classList.remove("d-none", "text-bg-warning");
  resultStatusEl.classList.add("badge", "rounded-pill", "text-bg-success", "status-badge");
  resultStatusEl.innerHTML = `<i class="bi bi-check-circle-fill" aria-hidden="true"></i><span>Успешно</span>`;
}

function setStatusWarn() {
  if (!resultStatusEl) return;
  resultStatusEl.classList.remove("d-none", "text-bg-success");
  resultStatusEl.classList.add("badge", "rounded-pill", "text-bg-warning", "status-badge");
  resultStatusEl.innerHTML = `<i class="bi bi-exclamation-triangle-fill" aria-hidden="true"></i><span>Есть ошибки</span>`;
}

function clearResultMeta() {
  if (resultMetaEl) resultMetaEl.classList.add("d-none");
  if (resultScoreEl) resultScoreEl.textContent = "";
  if (resultFeedbackEl) resultFeedbackEl.textContent = "";
  if (resultQualityEl) resultQualityEl.textContent = "";
  if (resultRecommendationsWrapEl) resultRecommendationsWrapEl.classList.add("d-none");
  if (resultRecommendationsEl) resultRecommendationsEl.innerHTML = "";
}

function renderResultMeta(data) {
  if (!resultMetaEl) return;
  resultMetaEl.classList.remove("d-none");
  if (resultScoreEl) resultScoreEl.textContent = String(data.score ?? "—");
  if (resultFeedbackEl) resultFeedbackEl.textContent = data.feedback || "";
  if (resultQualityEl) resultQualityEl.textContent = data.quality_notes || "";
  const recs = Array.isArray(data.recommendations) ? data.recommendations.filter(Boolean) : [];
  if (resultRecommendationsWrapEl && resultRecommendationsEl) {
    if (recs.length) {
      resultRecommendationsWrapEl.classList.remove("d-none");
      resultRecommendationsEl.innerHTML = recs
        .map((r) => `<li>${escapeHtml(r)}</li>`)
        .join("");
    } else {
      resultRecommendationsWrapEl.classList.add("d-none");
      resultRecommendationsEl.innerHTML = "";
    }
  }
}

function clearStatus() {
  if (resultStatusEl) {
    resultStatusEl.classList.add("d-none");
    resultStatusEl.innerHTML = "";
    resultStatusEl.classList.remove("badge", "rounded-pill", "text-bg-success", "text-bg-warning");
  }
  if (resultHintEl) resultHintEl.textContent = "";
  clearResultMeta();
  setResultHeaderState("neutral");
}

async function sendToApi() {
  try {
    const text = (textEl.value || "").trim();
    if (!text) {
      highlightedEl.innerHTML = '<span class="text-muted">Введите текст.</span>';
      renderErrorsList([]);
      clearStatus();
      return;
    }

    setLoading(true);
    showAwaitingResults();

    const payload = {
      task_id: TASK_ID,
      task_code: TASK_CODE,
      student_code: getStudentCode(),
      text,
    };

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 45000);
    let res;
    try { res = await fetch(API + "/api/story/check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: controller.signal,
    }); } finally { clearTimeout(timeoutId); }
    const raw = await res.text();
    let data; try { data = JSON.parse(raw); } catch (_) { data = { raw }; }

    if (!res.ok) {
      const errMsg = data.error || raw;
      highlightedEl.innerHTML = `<pre class="text-danger mb-0">HTTP ${res.status}\n${escapeHtml(errMsg)}</pre>`;
      renderErrorsList([]);
      clearResultMeta();
      return;
    }

    const normalized = data.normalized || text;
    const errors = data.errors || [];
    highlightedEl.innerHTML = renderHighlightedText(normalized, errors);
    renderErrorsList(errors);
    renderResultMeta(data);
    const ok = Boolean(data.ok);
    if (ok) {
      setResultHeaderState("ok");
      setStatusOk();
      if (resultHintEl) resultHintEl.textContent = "";
    } else {
      setResultHeaderState("warn");
      setStatusWarn();
      if (resultHintEl) {
        resultHintEl.textContent =
          "Наведите мышкой на выделенные слова для подробностей.";
      }
    }
    if (data.saved === false && resultHintEl) {
      const reason = data.save_error ? ` (${data.save_error})` : "";
      const warn = `Проверка выполнена, но попытка не сохранена${reason}.`;
      resultHintEl.textContent = resultHintEl.textContent
        ? `${resultHintEl.textContent} ${warn}`
        : warn;
    }
  } catch (e) {
    highlightedEl.innerHTML = `<pre class="text-danger mb-0">Не удалось получить результат. Попробуйте ещё раз.</pre>`;
    renderErrorsList([]);
    clearStatus();
  } finally {
    setLoading(false);
  }
}

btnSend.addEventListener("click", sendToApi);
btnClear.addEventListener("click", () => {
  textEl.value = "";
  highlightedEl.innerHTML = "";
  errorsEl.innerHTML = "";
  hintEl.textContent = "";
  clearStatus();
});
