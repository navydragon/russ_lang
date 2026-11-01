"use strict";
async function loadExcursion() {
  const response = await fetch("../excursion_text.json");
  if (!response.ok) throw new Error("Не удалось загрузить текст задания.");
  return response.json();
}
function studentCode() {
  const match = document.cookie.match(/(?:^|;\s*)student_code=([^;]*)/);
  try { return match ? decodeURIComponent(match[1]) : ""; } catch (_) { return ""; }
}
function renderParagraphs(container, paragraphs) {
  container.replaceChildren();
  for (const paragraph of paragraphs) {
    const p = document.createElement("p");
    p.textContent = paragraph;
    container.appendChild(p);
  }
}
function apiError(response, raw) {
  try { const data = JSON.parse(raw); return data.error || data.detail || `HTTP ${response.status}`; }
  catch (_) { return `Сервер вернул ошибку HTTP ${response.status}.`; }
}
