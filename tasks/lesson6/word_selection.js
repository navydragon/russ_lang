"use strict";

const API = window.ANALYZER_CONFIG.apiBaseUrl;
const source = document.getElementById("source");
const check = document.getElementById("check");
const clear = document.getElementById("clear");
const result = document.getElementById("result");
const errorMessage = document.getElementById("error");
const selected = new Set();

function renderWords(paragraphs) {
  let index = 0;
  for (const paragraph of paragraphs) {
    const line = document.createElement("p");
    let previous = 0;
    for (const match of paragraph.matchAll(/[А-Яа-яЁё]+/g)) {
      const wordIndex = index++;
      line.append(paragraph.slice(previous, match.index));
      const word = document.createElement("button");
      word.type = "button";
      word.className = "word";
      word.textContent = match[0];
      word.setAttribute("aria-pressed", "false");
      word.addEventListener("click", () => {
        if (selected.has(wordIndex)) selected.delete(wordIndex);
        else selected.add(wordIndex);
        word.setAttribute("aria-pressed", String(selected.has(wordIndex)));
        result.textContent = "—";
      });
      line.append(word);
      previous = match.index + match[0].length;
    }
    line.append(paragraph.slice(previous));
    source.append(line);
  }
}

clear.addEventListener("click", () => {
  selected.clear();
  source.querySelectorAll('[aria-pressed="true"]').forEach(word => word.setAttribute("aria-pressed", "false"));
  result.textContent = "—";
  errorMessage.textContent = "";
});

check.addEventListener("click", async () => {
  check.disabled = true;
  clear.disabled = true;
  source.inert = true;
  errorMessage.textContent = "";
  try {
    const response = await fetch(API + CHECK_PATH, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task_code: TASK_CODE, student_code: studentCode(), selected: [...selected] })
    });
    const raw = await response.text();
    if (!response.ok) throw new Error(apiError(response, raw));
    const data = JSON.parse(raw);
    result.textContent = [
      `${data.score} / 100 — ${data.ok ? "Зачёт" : "Незачёт"}`,
      `Найдено ${data.correct} из ${data.total}. Лишних слов: ${data.extra}.`,
      data.saved ? "Результат сохранён." : "Результат не сохранён. Откройте задание со страницы ученика."
    ].join("\n");
  } catch (error) {
    errorMessage.textContent = error.message;
  } finally {
    source.inert = false;
    clear.disabled = false;
    check.disabled = false;
  }
});

async function loadSelectionText() {
  try {
    const response = await fetch("source.json");
    if (!response.ok) throw new Error("Не удалось загрузить текст.");
    const data = await response.json();
    renderWords(data.paragraphs);
    clear.disabled = false;
    check.disabled = false;
  } catch (error) {
    errorMessage.textContent = error.message;
  }
}

loadSelectionText();
