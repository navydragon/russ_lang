const API = window.ANALYZER_CONFIG.apiBaseUrl;
const form = document.getElementById("description-form");
const description = document.getElementById("description");
const submit = form.querySelector("button");
const status = document.getElementById("check-status");
const feedback = document.getElementById("feedback");

function getStudentCode() {
  const code = document.cookie.match(/(?:^|;\s*)student_code=([^;]*)/)?.[1] || "";
  try {
    return decodeURIComponent(code);
  } catch {
    return code;
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = description.value.trim();
  feedback.replaceChildren();
  feedback.hidden = true;
  if (!text) {
    status.textContent = "Введите описание.";
    return;
  }

  submit.disabled = true;
  description.readOnly = true;
  status.textContent = "Проверяем описание…";
  try {
    const response = await fetch(API + "/api/story/check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        task_id: form.dataset.taskId,
        task_code: TASK_CODE,
        student_code: getStudentCode(),
        text,
      }),
      signal: AbortSignal.timeout(45000),
    });
    if (!response.ok) throw new Error("Проверка недоступна");
    const result = await response.json();
    status.textContent = `${result.ok ? "Зачёт" : "Незачёт"} · ${result.score}/100`;
    if (result.saved === false) status.textContent += ". Попытка не сохранена.";
    const rubric = result.rubric;
    const messages = [
      result.feedback,
      rubric && `Содержание — ${rubric.content}/60. ${rubric.content_reason}`,
      rubric && `Связность — ${rubric.coherence}/25. ${rubric.coherence_reason}`,
      rubric && `Грамотность — ${rubric.literacy}/15. ${rubric.literacy_reason}`,
      result.sentence_limit_applied && `Минимум предложений — ${form.dataset.minSentences}. Итог ограничен 59 баллами.`,
    ].filter(Boolean);
    for (const message of new Set(messages)) {
      const item = document.createElement("li");
      item.textContent = message;
      feedback.append(item);
    }
    feedback.hidden = !feedback.childElementCount;
  } catch {
    status.textContent = "Не удалось проверить описание. Попробуйте ещё раз.";
  } finally {
    submit.disabled = false;
    description.readOnly = false;
  }
});
