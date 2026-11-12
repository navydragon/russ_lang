"use strict";
const TASK_ID = "lesson7_fairytale_reading", MAX_SECONDS = 120;
const el = id => document.getElementById(id);
let recorder, stream, chunks = [], blob, started, timer, checking = false;
function clock(seconds) { return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2,"0")}`; }
function buttons() { el("record").disabled = !!recorder && recorder.state === "recording" || checking; el("stop").disabled = !recorder || recorder.state !== "recording" || checking; el("check").disabled = !blob || checking || (recorder && recorder.state === "recording"); }
function stop() { if (recorder && recorder.state === "recording") recorder.stop(); }
el("record").addEventListener("click", async () => {
  try {
    stream = await navigator.mediaDevices.getUserMedia({audio:true}); chunks = []; blob = null;
    el("player").hidden = true; el("result").textContent = "—";
    const mime = MediaRecorder.isTypeSupported("audio/webm;codecs=opus") ? "audio/webm;codecs=opus" : "audio/webm";
    recorder = new MediaRecorder(stream, {mimeType:mime});
    recorder.ondataavailable = event => {if(event.data.size) chunks.push(event.data);};
    recorder.onstop = () => {
      clearInterval(timer); stream.getTracks().forEach(track => track.stop());
      blob = new Blob(chunks, {type:recorder.mimeType}); el("player").src = URL.createObjectURL(blob);
      el("player").hidden = false; el("status").textContent = "Запись готова"; buttons();
    };
    started = Date.now(); recorder.start(); el("status").textContent = "Идёт запись"; buttons();
    timer = setInterval(() => { const elapsed = Math.floor((Date.now()-started)/1000); el("timer").textContent = `${clock(Math.min(elapsed,MAX_SECONDS))} / 2:00`; if(elapsed >= MAX_SECONDS) stop(); },250);
  } catch (_) {el("status").textContent = "Не удалось получить доступ к микрофону."; if(stream) stream.getTracks().forEach(track => track.stop());}
});
el("stop").addEventListener("click", stop);
el("check").addEventListener("click", async () => {
  if(!blob || checking) return; checking = true; buttons(); el("status").textContent = "Проверяем чтение…";
  try {
    const form = new FormData(); form.append("file", blob, "reading.webm"); form.append("task_id", TASK_ID); form.append("language","ru");
    const response = await fetch(API + "/api/reading/check", {method:"POST",body:form}); const raw = await response.text();
    if(!response.ok) throw new Error(apiError(response,raw)); const data = JSON.parse(raw);
    const coverage = Math.round((data.coverage?.ratio || 0)*100), duration = Number(data.duration || 0).toFixed(1), breakdown = data.score_breakdown || {};
    el("result").textContent = `${data.score} / 100 — ${data.ok ? "Зачёт" : "Незачёт"}\nПолнота: ${coverage}%\nВремя: ${duration} с (лимит 120 с)\nСлова: ${breakdown.words ?? "—"} баллов, паузы: ${breakdown.pauses ?? "—"} баллов.\nРаспознано: ${data.recognized || "—"}`;
    {
      const savedResponse = await fetch(API + "/api/reading/complete", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({task_id:TASK_ID,task_code:TASK_CODE,student_code:studentCode(),result:data})});
      const saved = await savedResponse.json(); el("result").textContent += saved.saved ? "\nРезультат сохранён." : "\nРезультат не сохранён: откройте задание со страницы ученика.";
    }
    el("status").textContent = "Проверка завершена";
  } catch(error) {el("status").textContent = "Ошибка проверки"; el("result").textContent = error.message;}
  finally {checking = false; buttons();}
});
loadText().then(data => renderParagraphs(el("source"), data.paragraphs)).catch(error => {el("status").textContent = error.message;});
