"use strict";
const storageKey = "dictation:" + API + ":" + TASK_CODE;
const el = id => document.getElementById(id);
let run = null;
let busy = false;

function studentCode() {
  const match = document.cookie.match(/(?:^|;\s*)student_code=([^;]*)/);
  try { return match ? decodeURIComponent(match[1]) : ""; } catch (_) { return ""; }
}
function storeRun(id) { try { localStorage.setItem(storageKey, id); } catch (_) {} }
function previousRun() { try { return localStorage.getItem(storageKey); } catch (_) { return null; } }
async function request(path, body) {
  const response = await fetch(API + "/api/dictation/" + path, body === undefined ? {} : {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Не удалось выполнить запрос.");
  return data;
}
function feedbackText(item) {
  if (run.task_code === 'AI_3_10') {
    return "Эталон: " + item.expected + " Зачтено слов: " + item.correct_words + "/" + item.word_count
      + "; ошибок: " + item.word_errors + ".";
  }
  if (run.task_code === 'AI_3_9') {
    return item.singular + " → " + item.expected + ". Итого: " + item.score + "/10.";
  }
  const details = run.task_code === 'AI_3_8'
    ? "Первое слово: " + item.first_points + "/10; второе: " + item.second_points + "/10."
    : "Существительное: " + item.noun_points + "/5; местоимение: " + item.pronoun_points + "/5.";
  return "Правильно: " + item.expected + ". " + details + " Итого: " + item.score + "/" + run.item_max_score + ".";
}
function renderSummary() {
  el("total").textContent = run.score + " / 100";
  if (run.task_code === 'AI_3_10') el("total").textContent += " · слова: " + run.correct_words + "/" + run.total_words;
  el("progress").textContent = "Проверено " + run.answered + " из " + run.word_count;
  el("outcome").textContent = run.completed ? (run.ok ? "Зачёт!" : "Незачёт. Для зачёта нужно 60 баллов.") : "";
  el("outcome").className = "fw-semibold " + (run.ok ? "text-success" : "text-danger");
  el("saved").textContent = run.completed ? (run.saved ? "Результат сохранён." : "Результат не сохранён. Для сохранения откройте диктант со страницы запуска ученика.") : "";
  el("history").replaceChildren();
  for (const item of run.answers) {
    const li = document.createElement("li");
    li.textContent = (item.answer || "Пропущено") + " — " + feedbackText(item);
    el("history").appendChild(li);
  }
  el("start").hidden = !run.completed;
  el("start").textContent = "Начать заново";
  el("intro").hidden = true;
}
function showCurrent() {
  renderSummary();
  el("next").hidden = true;
  el("wordFeedback").textContent = "";
  el("error").textContent = "";
  el("question").hidden = run.completed;
  if (run.completed) { el("stepTitle").textContent = "Диктант завершён"; return; }
  el("stepTitle").textContent = (run.task_code === "AI_3_10" ? "Предложение " : "Позиция ") + (run.current.index + 1) + " из " + run.word_count;
  el("audio").src = API + run.current.audio_path + "?v=singular-pairs-11";
  el("answer").value = "";
  el("answer").disabled = false;
  el("check").disabled = false;
  el("skip").disabled = false;
  el("answer").focus();
}
async function begin() {
  if (busy) return;
  busy = true; el("start").disabled = true;
  try {
    run = await request("start", { task_code: TASK_CODE, student_code: studentCode() });
    storeRun(run.run_id);
    showCurrent();
  } catch (error) { el("error").textContent = error.message; }
  finally { busy = false; el("start").disabled = false; }
}
async function submit(text) {
  if (busy || !run || !run.current) return;
  busy = true; el("check").disabled = true; el("skip").disabled = true;
  el("error").textContent = "";
  try {
    run = await request("answer", { run_id: run.run_id, index: run.current.index, answer: text });
    renderSummary();
    const f = run.feedback;
    el("wordFeedback").textContent = feedbackText(f);
    el("answer").disabled = true;
    el("next").hidden = run.completed;
    if (run.completed) el("stepTitle").textContent = "Диктант завершён";
  } catch (error) {
    el("error").textContent = error.message;
    el("check").disabled = false; el("skip").disabled = false;
  } finally { busy = false; }
}
el("start").addEventListener("click", begin);
el("next").addEventListener("click", showCurrent);
el("answerForm").addEventListener("submit", event => {
  event.preventDefault();
  if (!el("answer").value.trim()) { el("error").textContent = "Введите ответ или нажмите «Пропустить»."; return; }
  submit(el("answer").value.trim());
});
el("skip").addEventListener("click", () => { el("answer").value = ""; submit(""); });
el("listen").addEventListener("click", async () => {
  try { el("audio").currentTime = 0; await el("audio").play(); el("error").textContent = ""; }
  catch (_) { el("error").textContent = "Не удалось воспроизвести слово. Проверьте звук и попробуйте ещё раз."; }
});
(async () => {
  const id = previousRun();
  if (!id) return;
  el("start").disabled = true;
  try {
    const existing = await request("state?run_id=" + encodeURIComponent(id));
    if (existing.student_code === studentCode() && existing.task_code === TASK_CODE) { run = existing; showCurrent(); }
  } catch (_) { /* Истёкший набор заменяется новым по кнопке начала. */ }
  finally { el("start").disabled = false; }
})();
