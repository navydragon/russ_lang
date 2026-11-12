"use strict";
const API = window.ANALYZER_CONFIG.apiBaseUrl;
const TASK_ID = "lesson5_classroom_questions", TASK_CODE = "AI_5_6";
const CARDS = [
  { image: "images/water_glass.png", alt: "Стакан с водой стоит на столе", supports: ["стакан", "вода", "стол"] },
  { image: "images/cat_sofa.png", alt: "Кошка сидит на диване", supports: ["кошка", "диван", "сидеть"] },
  { image: "images/boy_bed.png", alt: "Мальчик спит в кровати", supports: ["мальчик", "кровать", "спать"] },
];
const state = CARDS.map(() => ({ question: "", answer: "", blob: null, audioUrl: null, written: null, oral: null }));
const el = id => document.getElementById(id);
let current = 0, recorder = null, stream = null, chunks = [], timer = null, recordStarted = 0, busy = false;
function studentCode() { const m = document.cookie.match(/(?:^|;\s*)student_code=([^;]*)/); try { return m ? decodeURIComponent(m[1]) : ""; } catch (_) { return ""; } }
function clock(seconds) { return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`; }
function currentState() { return state[current]; }
function pairText(mode) { return `Режим: ${mode === "written" ? "письменный" : "устный"}. Вопрос: ${currentState().question}. Ответ: ${currentState().answer}.`; }
function renderGrade(target, data) {
  const lines = [`${data.score} / 100 — ${data.ok ? "Зачёт" : "Незачёт"}`, data.feedback || ""];
  if (data.quality_notes) lines.push(data.quality_notes);
  for (const issue of [...(data.errors || []).map(item => item.message), ...(data.recommendations || [])]) lines.push(`• ${issue}`);
  if (data.recognized) lines.push(`Распознано: ${data.recognized}`);
  if (data.saved === false) lines.push("Попытка не сохранена: откройте задание со страницы ученика.");
  target.textContent = lines.filter(Boolean).join("\n");
}
function render() {
  const card = CARDS[current], item = currentState();
  el("pictureHeading").textContent = `Картинка ${current + 1} из ${CARDS.length}`;
  el("progressText").textContent = `Проверено ${state.filter(x => x.written && x.oral).length} из ${CARDS.length}`;
  el("picture").src = card.image; el("picture").alt = card.alt;
  const chips = el("supportWords"); chips.replaceChildren();
  for (const word of card.supports) { const chip = document.createElement("span"); chip.className = "chip"; chip.textContent = word; chips.appendChild(chip); }
  el("question").value = item.question; el("answer").value = item.answer;
  const recording = !!recorder && recorder.state === "recording";
  el("previous").disabled = current === 0 || busy || recording;
  el("next").disabled = !(item.written && item.oral) || busy;
  el("next").textContent = current === CARDS.length - 1 ? "Завершить" : "Следующая картинка";
  el("check").disabled = busy || !item.question.trim() || !item.answer.trim() || !item.blob || !!(item.written && item.oral);
  el("writtenResult").textContent = item.written ? "" : "Ещё не проверено";
  if (item.written) renderGrade(el("writtenResult"), item.written);
  el("oralResult").textContent = item.oral ? "" : "Ещё не проверено";
  if (item.oral) renderGrade(el("oralResult"), item.oral);
  el("player").hidden = !item.blob;
  if (item.blob) el("player").src = item.audioUrl;
  else el("player").removeAttribute("src");
  el("record").disabled = busy || recording;
  el("stop").disabled = busy || !recorder || recorder.state !== "recording";
  el("finish").hidden = !state.every(x => x.written && x.oral);
}
el("question").addEventListener("input", event => { currentState().question = event.target.value; currentState().written = null; render(); });
el("answer").addEventListener("input", event => { currentState().answer = event.target.value; currentState().written = null; render(); });
el("previous").addEventListener("click", () => { if (current > 0 && !busy && (!recorder || recorder.state !== "recording")) { current--; el("status").textContent = "Продолжите составлять пару для этой картинки."; render(); } });
el("next").addEventListener("click", () => { if (currentState().written && currentState().oral && !busy) { if (current < CARDS.length - 1) { current++; el("status").textContent = "Продолжите составлять пару для этой картинки."; render(); } else { el("status").textContent = "Вы проверили устные и письменные пары ко всем картинкам."; el("finish").hidden = false; } } });
el("record").addEventListener("click", async () => {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true }); chunks = [];
    if (currentState().audioUrl) URL.revokeObjectURL(currentState().audioUrl);
    currentState().blob = null; currentState().audioUrl = null; currentState().oral = null;
    const mime = MediaRecorder.isTypeSupported("audio/webm;codecs=opus") ? "audio/webm;codecs=opus" : "audio/webm";
    recorder = new MediaRecorder(stream, { mimeType: mime });
    recorder.ondataavailable = event => { if (event.data.size) chunks.push(event.data); };
    recorder.onstop = () => { clearInterval(timer); stream.getTracks().forEach(track => track.stop()); currentState().blob = new Blob(chunks, { type: recorder.mimeType }); currentState().audioUrl = URL.createObjectURL(currentState().blob); render(); };
    recordStarted = Date.now(); recorder.start(); el("status").textContent = "Идёт запись вопроса и ответа…"; render();
    timer = setInterval(() => { el("timer").textContent = clock(Math.floor((Date.now() - recordStarted) / 1000)); }, 250);
  } catch (_) { el("status").textContent = "Не удалось получить доступ к микрофону."; if (stream) stream.getTracks().forEach(track => track.stop()); }
});
el("stop").addEventListener("click", () => { if (recorder && recorder.state === "recording") recorder.stop(); });
async function sendCheck(mode) {
  const form = new FormData();
  form.append("task_id", TASK_ID); form.append("task_code", TASK_CODE); form.append("student_code", studentCode());
  form.append("mode", mode); form.append("picture_index", String(current + 1));
  if (mode === "written") { form.append("question", currentState().question); form.append("answer", currentState().answer); }
  else form.append("file", currentState().blob, "pair.webm");
  const response = await fetch(API + "/api/picture-question/check", { method: "POST", body: form });
  const raw = await response.text(); let data;
  try { data = JSON.parse(raw); } catch (_) { data = { error: raw }; }
  if (!response.ok) throw new Error(data.error || `Ошибка сервера: ${response.status}`);
  return data;
}
el("check").addEventListener("click", async () => {
  if (busy || !currentState().blob || !currentState().question.trim() || !currentState().answer.trim()) return;
  busy = true; render(); el("status").textContent = "ИИ проверяет письменный ответ…";
  try {
    if (!currentState().written) { currentState().written = await sendCheck("written"); renderGrade(el("writtenResult"), currentState().written); }
    if (!currentState().oral) { el("status").textContent = "Теперь ИИ проверяет устную пару…"; currentState().oral = await sendCheck("oral"); renderGrade(el("oralResult"), currentState().oral); }
    el("status").textContent = "Письменная и устная пары проверены. Посмотрите обратную связь и переходите дальше.";
  } catch (error) { el("status").textContent = error.message; }
  finally { busy = false; render(); }
});
render();
