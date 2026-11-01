"use strict";
const selected = {genitive_plural: new Set(), time: new Set()};
const spans = [];
const sourceEl = document.getElementById("source");
let mode = "genitive_plural";
document.querySelectorAll('input[name="mode"]').forEach(input => input.addEventListener("change", () => { if (input.checked) mode = input.value; }));
function paint(index) {
  const span = spans[index];
  span.classList.toggle("genitive_plural", selected.genitive_plural.has(index));
  span.classList.toggle("time", selected.time.has(index));
  span.setAttribute("aria-pressed", String(selected[mode].has(index)));
}
function addText(paragraphs) {
  sourceEl.replaceChildren();
  const wordPattern = /[А-Яа-яЁёA-Za-z0-9]+/g;
  for (const paragraph of paragraphs) {
    const p = document.createElement("p");
    let previous = 0;
    for (const match of paragraph.matchAll(wordPattern)) {
      p.appendChild(document.createTextNode(paragraph.slice(previous, match.index)));
      const index = spans.length;
      const span = document.createElement("span");
      span.className = "word";
      span.textContent = match[0];
      span.tabIndex = 0;
      span.setAttribute("role", "button");
      span.setAttribute("aria-label", `Отметить слово ${match[0]}`);
      const toggle = () => { selected[mode].has(index) ? selected[mode].delete(index) : selected[mode].add(index); paint(index); };
      span.addEventListener("click", toggle);
      span.addEventListener("keydown", event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); toggle(); } });
      p.appendChild(span);
      spans.push(span);
      previous = match.index + match[0].length;
    }
    p.appendChild(document.createTextNode(paragraph.slice(previous)));
    sourceEl.appendChild(p);
  }
}
document.getElementById("clear").addEventListener("click", () => { selected.genitive_plural.clear(); selected.time.clear(); spans.forEach((_, i) => paint(i)); document.getElementById("result").textContent = "—"; });
document.getElementById("check").addEventListener("click", async () => {
  const button = document.getElementById("check"); button.disabled = true;
  document.getElementById("error").textContent = "";
  try {
    const response = await fetch(API + "/api/excursion/highlight/check", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({task_code:TASK_CODE, student_code:studentCode(), selected:{genitive_plural:[...selected.genitive_plural],time:[...selected.time]}})});
    const raw = await response.text(); if (!response.ok) throw new Error(apiError(response, raw));
    const data = JSON.parse(raw), g = data.categories.genitive_plural, t = data.categories.time;
    document.getElementById("result").textContent = `${data.score} / 100 — ${data.ok ? "Зачёт" : "Незачёт"}\nРодительный множественного: ${g.points}/50, найдено ${g.correct} из ${g.total}, лишних ${g.extra}.\nВыражения времени: ${t.points}/50, найдено ${t.correct} из ${t.total}, лишних ${t.extra}.` + (data.saved ? "\nРезультат сохранён." : "\nРезультат не сохранён: откройте задание из страницы ученика.");
  } catch (error) { document.getElementById("error").textContent = error.message; }
  finally { button.disabled = false; }
});
loadExcursion().then(data => addText(data.paragraphs)).catch(error => {document.getElementById("error").textContent = error.message;});
