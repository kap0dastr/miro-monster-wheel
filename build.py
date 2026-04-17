"""
build.py — собирает index.html из config.yaml + картинок монстров.
Запуск: python build.py
"""

import base64
import json
import mimetypes
import os
import sys
import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
MONSTERS_DIR = os.path.join(ROOT, "monsters")
CONFIG_PATH = os.path.join(ROOT, "config.yaml")
OUT_PATH = os.path.join(ROOT, "index.html")
GITHUB_PAGES_BASE = "https://kap0dastr.github.io/miro-monster-wheel/"

sys.stdout.reconfigure(encoding="utf-8")


def img_to_data_uri(path):
    if not path or not os.path.isfile(path):
        return None
    mime, _ = mimetypes.guess_type(path)
    mime = mime or "image/png"
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return f"data:{mime};base64,{data}"


def build():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    firebase = cfg.get("firebase", {})
    pins = cfg.get("pins", {"spin": "0202", "reset": "0909"})
    weapons = cfg.get("weapons", [])

    tasks_raw = cfg.get("tasks", [])
    tasks = []
    for t in tasks_raw:
        img_file = t.get("monster_image", "")
        img_path = os.path.join(MONSTERS_DIR, img_file) if img_file else None
        monster_uri = img_to_data_uri(img_path) if img_path else None

        banner_raw = t.get("banner_image", "")
        banner_uri = None
        banner_board_url = None  # публичный URL для вставки на доску
        if banner_raw:
            if banner_raw.startswith("http"):
                banner_uri = banner_raw
                banner_board_url = banner_raw
            else:
                banner_uri = img_to_data_uri(os.path.join(ROOT, banner_raw))
                banner_board_url = GITHUB_PAGES_BASE + banner_raw.replace("\\", "/")

        # Чистим список воинов — убираем пустые строки
        warriors_raw = t.get("warriors", [])
        warriors = [w for w in warriors_raw if w and w.strip()]

        monster_board_url = (GITHUB_PAGES_BASE + "monsters/" + img_file) if img_file else None

        tasks.append({
            "monster_image": monster_uri,
            "monster_board_url": monster_board_url,
            "task_number": t.get("task_number", ""),
            "task_link": t.get("task_link", ""),
            "task_name": t.get("task_name", ""),
            "score": t.get("score", 0),
            "banner_image": banner_uri,
            "banner_board_url": banner_board_url,
            "warriors": warriors,
        })

    data_js = json.dumps({
        "firebase": firebase,
        "pins": pins,
        "weapons": weapons,
        "tasks": tasks,
    }, ensure_ascii=False, indent=2)

    html = HTML_TEMPLATE.replace("__APP_DATA__", data_js)

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Готово! Файл: {OUT_PATH}")
    print(f"  Задач: {len(tasks)}")
    print(f"  Оружий: {len(weapons)}")
    print(f"  Firebase: {firebase.get('projectId', '???')}")


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Колесо монстров</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html { height: 100%; }
  body {
    height: 100%;
    margin: 0;
    overflow: hidden;                /* body не скроллится; скроллит #scroller */
    background: #1a1a2e;
    color: #eee;
    font-family: 'Segoe UI', sans-serif;
  }
  #scroller {
    height: 100%;
    width: 100%;
    overflow-y: scroll;              /* всегда показывать вертикальный скролл */
    overflow-x: hidden;
    -webkit-overflow-scrolling: touch;
    overscroll-behavior: contain;    /* не отдавать скролл родителю (Miro) */
  }
  /* Делаем скроллбар видимым */
  #scroller::-webkit-scrollbar { width: 10px; }
  #scroller::-webkit-scrollbar-track { background: #0d1b2a; }
  #scroller::-webkit-scrollbar-thumb { background: #f0a500; border-radius: 5px; }
  #scroller::-webkit-scrollbar-thumb:hover { background: #ffb820; }

  #content {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 10px 8px 30px;
    gap: 10px;
    min-height: 100%;
  }

  h1 {
    font-size: 1rem;
    color: #f0a500;
    text-shadow: 0 0 20px #f0a50088;
    letter-spacing: 1px;
  }

  /* ─── WHEEL ─── */
  #wheel-container {
    position: relative;
    width: 300px;
    height: 300px;
  }

  #wheel-canvas {
    border-radius: 50%;
    box-shadow: 0 0 40px #f0a50055;
  }

  #pointer {
    position: absolute;
    top: 50%;
    right: -20px;
    transform: translateY(-50%);
    width: 0;
    height: 0;
    border-top: 18px solid transparent;
    border-bottom: 18px solid transparent;
    border-right: 36px solid #f0a500;
    filter: drop-shadow(0 0 8px #f0a500);
  }

  /* ─── BUTTONS ─── */
  .btn-row {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    justify-content: center;
  }

  button {
    padding: 7px 14px;
    border: none;
    border-radius: 8px;
    font-size: .82rem;
    cursor: pointer;
    font-weight: 600;
    transition: transform .1s, opacity .2s;
  }
  button:active { transform: scale(0.96); }
  button:disabled { opacity: .4; cursor: default; }

  #btn-spin {
    background: linear-gradient(135deg, #f0a500, #e05c00);
    color: #fff;
    font-size: .9rem;
    padding: 9px 20px;
  }
  #btn-reset { background: #444; color: #ccc; }
  #btn-next  { background: #2a6b3a; color: #fff; display: none; }

  /* ─── RESULT CARD ─── */
  #result-card {
    display: none;
    background: #16213e;
    border: 2px solid #f0a500;
    border-radius: 10px;
    padding: 12px 14px;
    max-width: 320px;
    width: 100%;
    box-shadow: 0 0 30px #f0a50033;
    animation: pop .35s ease;
  }
  @keyframes pop {
    from { transform: scale(.85); opacity: 0; }
    to   { transform: scale(1);   opacity: 1; }
  }

  #result-card .monster-img {
    width: 70px;
    height: 70px;
    object-fit: contain;
    float: left;
    margin-right: 10px;
    border-radius: 6px;
  }

  #result-card h2 {
    color: #f0a500;
    font-size: 1.3rem;
    margin-bottom: 6px;
  }
  #result-card .meta { font-size: .9rem; color: #aaa; line-height: 1.7; }
  #result-card .meta a { color: #5cb8ff; text-decoration: none; }
  #result-card .meta a:hover { text-decoration: underline; }
  #result-card .score-badge {
    display: inline-block;
    background: #f0a500;
    color: #1a1a2e;
    font-weight: 800;
    border-radius: 6px;
    padding: 2px 10px;
    font-size: 1rem;
    margin-left: 6px;
  }
  #result-card .warriors-section {
    margin-top: 10px;
    font-size: .95rem;
  }
  #result-card .warriors-section strong {
    color: #f0a500;
  }
  #result-card .warriors-list {
    margin-top: 4px;
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }
  #result-card .warrior-tag {
    background: #2a3f5f;
    border: 1px solid #4a6fa5;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: .85rem;
    color: #b0c4de;
  }
  #result-card .banner-img {
    width: 100%;
    margin-top: 10px;
    border-radius: 8px;
    max-height: 300px;
    object-fit: contain;
  }
  .btn-to-board {
    margin-top: 8px;
    width: 100%;
    background: #1a3a5c;
    color: #5cb8ff;
    border: 1px solid #4a6fa5;
    border-radius: 8px;
    padding: 7px 14px;
    font-size: .85rem;
    cursor: pointer;
    font-weight: 600;
  }
  .btn-to-board:hover { background: #1e4a7a; }
  .clearfix::after { content: ''; display: block; clear: both; }

  /* ─── WEAPONS ─── */
  #weapons-panel {
    max-width: 320px;
    width: 100%;
  }
  #weapons-panel h3 {
    color: #888;
    font-size: .85rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 10px;
  }
  #weapons-list {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
  }
  .weapon-chip {
    background: #2a2a4a;
    border: 1px solid #4a4a7a;
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 1.1rem;
    cursor: grab;
    user-select: none;
    transition: background .15s;
  }
  .weapon-chip:hover { background: #3a3a6a; }

  /* ─── STATUS ─── */
  #status {
    font-size: .85rem;
    color: #666;
    min-height: 18px;
  }
  #status.online { color: #4caf50; }
  #status.error  { color: #f44336; }

  /* ─── PIN MODAL ─── */
  #pin-overlay {
    display: none;
    position: fixed;
    inset: 0;
    background: #000a;
    z-index: 100;
    align-items: center;
    justify-content: center;
  }
  #pin-overlay.visible { display: flex; }
  #pin-box {
    background: #16213e;
    border: 2px solid #f0a500;
    border-radius: 16px;
    padding: 28px 32px;
    text-align: center;
    min-width: 280px;
  }
  #pin-box h3 { color: #f0a500; margin-bottom: 16px; font-size: 1.2rem; }
  #pin-input {
    width: 100%;
    font-size: 1.4rem;
    text-align: center;
    letter-spacing: 8px;
    padding: 10px;
    background: #0d1b2a;
    border: 1px solid #555;
    border-radius: 8px;
    color: #fff;
    margin-bottom: 14px;
    outline: none;
  }
  #pin-input:focus { border-color: #f0a500; }
  .pin-btn-row { display: flex; gap: 10px; justify-content: center; }
  #pin-ok  { background: #f0a500; color: #1a1a2e; }
  #pin-cancel { background: #444; color: #ccc; }
  #pin-error { color: #f44336; font-size: .85rem; margin-top: 8px; min-height: 18px; }
</style>
</head>
<body>

<div id="scroller">
  <div id="content">

    <h1>⚔️ Колесо монстров</h1>

    <div id="wheel-container">
      <canvas id="wheel-canvas" width="300" height="300"></canvas>
      <div id="pointer"></div>
    </div>

    <div id="status">Подключение...</div>

    <div class="btn-row">
      <button id="btn-spin">🎲 Крутить колесо</button>
      <button id="btn-next" style="display:none">➡️ Следующий монстр</button>
      <button id="btn-reset">🔄 Сброс</button>
    </div>

    <div id="result-card"></div>

  </div>
</div>

<!-- PIN MODAL -->
<div id="pin-overlay">
  <div id="pin-box">
    <h3 id="pin-title">Введи PIN</h3>
    <input id="pin-input" type="password" maxlength="6" inputmode="numeric" autocomplete="off">
    <div class="pin-btn-row">
      <button id="pin-ok">OK</button>
      <button id="pin-cancel">Отмена</button>
    </div>
    <div id="pin-error"></div>
  </div>
</div>

<script src="https://miro.com/app/static/sdk/v2/miro.js"></script>
<script type="module">
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import { getDatabase, ref, onValue, set, get } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-database.js";

// ─── CONFIG (baked in by build.py) ───────────────────────────────
const APP_DATA = __APP_DATA__;
const { firebase: fbCfg, pins, weapons, tasks } = APP_DATA;

// Не отдавать wheel-события доске Miro, когда крутим панель
(() => {
  const scroller = document.getElementById("scroller");
  if (!scroller) return;
  const stop = e => e.stopPropagation();
  scroller.addEventListener("wheel", stop, { passive: true });
  scroller.addEventListener("touchmove", stop, { passive: true });
})();

// ─── FIREBASE ────────────────────────────────────────────────────
const app = initializeApp(fbCfg);
const db  = getDatabase(app);
const STATE_REF = ref(db, "miro-wheel/state");

const statusEl = document.getElementById("status");
function setStatus(msg, cls = "") {
  statusEl.textContent = msg;
  statusEl.className = cls;
}

// ─── WHEEL ───────────────────────────────────────────────────────
const canvas = document.getElementById("wheel-canvas");
const ctx = canvas.getContext("2d");
const CX = canvas.width / 2;
const CY = canvas.height / 2;
const R  = CX - 10;

const PALETTE = [
  "#c0392b","#27ae60","#2980b9","#8e44ad",
  "#e67e22","#16a085","#d35400","#2c3e50",
  "#1abc9c","#e74c3c","#3498db","#f39c12",
];

// Pre-load monster images
const monsterImgs = tasks.map(t => {
  if (!t.monster_image) return null;
  const img = new Image();
  img.src = t.monster_image;
  return img;
});

let currentAngle = 0;  // current rotation in radians
let spinning = false;
let removedIndices = new Set();

function activeTasks() {
  return tasks.map((t, i) => ({ t, i })).filter(({ i }) => !removedIndices.has(i));
}

function drawWheel(angle) {
  const active = activeTasks();
  if (active.length === 0) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#333";
    ctx.beginPath();
    ctx.arc(CX, CY, R, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#fff";
    ctx.font = "bold 20px Segoe UI";
    ctx.textAlign = "center";
    ctx.fillText("Все задачи выполнены!", CX, CY);
    return;
  }
  const slice = (Math.PI * 2) / active.length;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  active.forEach(({ t, i }, idx) => {
    const start = angle + idx * slice;
    const end   = start + slice;
    const color = PALETTE[i % PALETTE.length];

    // Sector
    ctx.beginPath();
    ctx.moveTo(CX, CY);
    ctx.arc(CX, CY, R, start, end);
    ctx.closePath();
    ctx.fillStyle = color;
    ctx.fill();
    ctx.strokeStyle = "#1a1a2e";
    ctx.lineWidth = 2;
    ctx.stroke();

    // Monster image
    const img = monsterImgs[i];
    const mid = start + slice / 2;
    const imgR = R * 0.62;
    const ix = CX + imgR * Math.cos(mid);
    const iy = CY + imgR * Math.sin(mid);
    const sz = Math.min(60, (2 * Math.PI * R / active.length) * 0.55);

    ctx.save();
    ctx.translate(ix, iy);
    ctx.rotate(mid + Math.PI / 2);
    if (img && img.complete) {
      ctx.drawImage(img, -sz / 2, -sz / 2, sz, sz);
    } else {
      ctx.fillStyle = "#ffffffaa";
      ctx.font = `${sz * 0.45}px Segoe UI`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("?", 0, 0);
    }
    ctx.restore();

    // Task number label
    if (t.task_number) {
      const labelR = R * 0.88;
      const lx = CX + labelR * Math.cos(mid);
      const ly = CY + labelR * Math.sin(mid);
      ctx.save();
      ctx.translate(lx, ly);
      ctx.rotate(mid + Math.PI / 2);
      ctx.fillStyle = "#ffffffcc";
      ctx.font = "bold 11px Segoe UI";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(t.task_number, 0, 0);
      ctx.restore();
    }
  });

  // Center circle
  ctx.beginPath();
  ctx.arc(CX, CY, 28, 0, Math.PI * 2);
  ctx.fillStyle = "#1a1a2e";
  ctx.fill();
  ctx.strokeStyle = "#f0a500";
  ctx.lineWidth = 3;
  ctx.stroke();
  ctx.fillStyle = "#f0a500";
  ctx.font = "bold 16px Segoe UI";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText("⚔️", CX, CY);
}

function getWinnerIndex(angle) {
  const active = activeTasks();
  if (active.length === 0) return null;
  const slice = (Math.PI * 2) / active.length;
  // Pointer is at angle = 0 (right side, 3 o'clock), canvas grows clockwise
  // normalise angle to [0, 2π)
  let a = ((-angle) % (Math.PI * 2) + Math.PI * 2) % (Math.PI * 2);
  const idx = Math.floor(a / slice) % active.length;
  return active[idx].i;
}

// ─── SPIN ANIMATION ──────────────────────────────────────────────
function spinTo(targetAngle, duration, onDone) {
  const start = performance.now();
  const startAngle = currentAngle;
  const delta = targetAngle - startAngle;

  function frame(now) {
    const t = Math.min((now - start) / duration, 1);
    const ease = 1 - Math.pow(1 - t, 4);
    currentAngle = startAngle + delta * ease;
    drawWheel(currentAngle);
    if (t < 1) requestAnimationFrame(frame);
    else onDone();
  }
  requestAnimationFrame(frame);
}

// ─── RESULT CARD ─────────────────────────────────────────────────
function showResult(taskIdx) {
  const t = tasks[taskIdx];
  const card = document.getElementById("result-card");

  let warriorsHtml = "";
  if (t.warriors && t.warriors.length > 0) {
    const tags = t.warriors.map(w => `<span class="warrior-tag">${escHtml(w)}</span>`).join("");
    warriorsHtml = `
      <div class="warriors-section">
        <strong>⚔️ Воины:</strong>
        <div class="warriors-list">${tags}</div>
      </div>`;
  }

  let bannerHtml = "";
  if (t.banner_image) {
    bannerHtml = `<img class="banner-img" src="${escAttr(t.banner_image)}" alt="banner">`;
  }

  let monsterHtml = "";
  if (t.monster_image) {
    monsterHtml = `<img class="monster-img" src="${escAttr(t.monster_image)}" alt="monster">`;
  }

  let taskLinkHtml = "";
  if (t.task_link) {
    const label = t.task_number || t.task_link;
    taskLinkHtml = `<a href="${escAttr(t.task_link)}" target="_blank" rel="noopener">${escHtml(label)}</a>`;
  } else if (t.task_number) {
    taskLinkHtml = escHtml(t.task_number);
  }

  const scoreHtml = t.score ? `<span class="score-badge">${t.score} SP</span>` : "";

  card.innerHTML = `
    <div class="clearfix">
      ${monsterHtml}
      <h2>${escHtml(t.task_name || "Монстр появился!")}</h2>
      <div class="meta">
        ${taskLinkHtml}${scoreHtml}<br>
      </div>
    </div>
    ${warriorsHtml}
    ${bannerHtml}
    <button class="btn-to-board" id="btn-add-board">📌 Добавить на доску</button>
  `;
  card.style.display = "block";

  document.getElementById("btn-add-board").onclick = () => addCardToBoard(taskIdx);
}

function hideResult() {
  document.getElementById("result-card").style.display = "none";
}

// ─── ADD TO BOARD ────────────────────────────────────────────────
async function addCardToBoard(taskIdx) {
  const btn = document.getElementById("btn-add-board");
  const t = tasks[taskIdx];
  btn.disabled = true;
  btn.textContent = "Добавляю...";
  try {
    const vp = await miro.board.viewport.get();

    // Смещаем каждую следующую карточку вправо используя boardCount из Firebase
    const snap = await get(STATE_REF);
    const state = snap.val() || {};
    const boardCount = state.boardCount || 0;
    await set(STATE_REF, { ...state, boardCount: boardCount + 1 });

    const W = 1100, H = 820;
    const cx = vp.x + vp.width / 2 + 600 + boardCount * (W + 200);
    const cy = vp.y + vp.height / 2;

    const IMG_SIZE = 220;
    const textX = cx - W/2 + IMG_SIZE + 70;
    const textW = W - IMG_SIZE - 110;

    // Фон карточки — скруглённый прямоугольник с жёлтой рамкой
    await miro.board.createShape({
      shape: "round_rectangle",
      x: cx, y: cy,
      width: W, height: H,
      style: {
        fillColor: "#16213e",
        fillOpacity: 1,
        borderColor: "#f0a500",
        borderWidth: 4,
        borderOpacity: 1,
        borderStyle: "normal",
      },
    });

    // Картинка монстра (слева, в верхней части)
    if (t.monster_board_url) {
      await miro.board.createImage({
        url: t.monster_board_url,
        x: cx - W/2 + IMG_SIZE/2 + 30,
        y: cy - H/2 + IMG_SIZE/2 + 40,
        width: IMG_SIZE,
      });
    }

    // Название задачи
    let curY = cy - H/2 + 55;
    await miro.board.createText({
      content: escHtml(t.task_name || "Монстр"),
      x: textX + textW/2,
      y: curY,
      width: textW,
      style: { fontSize: 28, color: "#f0a500", textAlign: "left" },
    });
    curY += 90;

    // Номер задачи + SP — гиперссылка через HTML <a>
    if (t.task_number || t.score) {
      const numText = escHtml(t.task_number || "");
      const scoreText = t.score ? `${t.score} SP` : "";
      const numPart = t.task_link
        ? `<a href="${escAttr(t.task_link)}" target="_blank">${numText}</a>`
        : numText;
      const parts = [numPart, scoreText].filter(Boolean);
      const numItem = await miro.board.createText({
        content: parts.join("   |   "),
        x: textX + textW/2,
        y: curY,
        width: textW,
        style: { fontSize: 22, color: "#cccccc", textAlign: "left" },
      });
      if (t.task_link) {
        try { numItem.linkedTo = t.task_link; await numItem.sync(); } catch(e) {}
      }
    }

    // Воины — под картинкой монстра, во всю ширину
    let fullY = cy - H/2 + IMG_SIZE + 75;
    if (t.warriors && t.warriors.length > 0) {
      await miro.board.createText({
        content: "⚔️ Воины: " + t.warriors.map(escHtml).join("  •  "),
        x: cx,
        y: fullY,
        width: W - 80,
        style: { fontSize: 20, color: "#b0c4de", textAlign: "left" },
      });
      fullY += 55;
    }

    // Баннер — внутри прямоугольника
    if (t.banner_board_url) {
      const BANNER_W = W - 100;
      await miro.board.createImage({
        url: t.banner_board_url,
        x: cx,
        y: fullY + 70,
        width: BANNER_W,
      });
      fullY += 155;
    }

    // «Какие проблемы у нас возникли с этим монстром» — заголовок
    await miro.board.createText({
      content: "Какие проблемы у нас возникли с этим монстром",
      x: cx,
      y: fullY + 22,
      width: W - 80,
      style: { fontSize: 22, color: "#f0a500", textAlign: "center" },
    });
    fullY += 65;

    // Список 1. 2. 3. — пустые строки для заполнения на ретро
    for (let i = 1; i <= 3; i++) {
      await miro.board.createText({
        content: `${i}.`,
        x: cx,
        y: fullY + 20,
        width: W - 120,
        style: { fontSize: 20, color: "#eeeeee", textAlign: "left" },
      });
      fullY += 55;
    }

    // Арсенал — под карточкой, скруглённые прямоугольники с жёлтым текстом
    const arsenalY = cy + H/2 + 90;
    const WEAPON_W = 150, WEAPON_H = 64, GAP = 175;
    const startX = cx - (weapons.length - 1) * GAP / 2;
    for (let i = 0; i < weapons.length; i++) {
      const wx = startX + i * GAP;
      await miro.board.createShape({
        shape: "round_rectangle",
        x: wx, y: arsenalY,
        width: WEAPON_W, height: WEAPON_H,
        style: {
          fillColor: "#16213e",
          fillOpacity: 1,
          borderColor: "#f0a500",
          borderWidth: 2,
          borderOpacity: 1,
          borderStyle: "normal",
        },
      });
      await miro.board.createText({
        content: `${weapons[i].emoji} ${weapons[i].name}`,
        x: wx, y: arsenalY,
        width: WEAPON_W - 10,
        style: { fontSize: 20, color: "#f0a500", textAlign: "center" },
      });
    }

    btn.textContent = "✅ Добавлено!";
  } catch (err) {
    console.error("addCardToBoard failed:", err);
    btn.textContent = "❌ " + err.message;
    btn.disabled = false;
  }
}

// ─── PIN MODAL ───────────────────────────────────────────────────
let pinResolve = null;

function askPin(title) {
  return new Promise(resolve => {
    pinResolve = resolve;
    document.getElementById("pin-title").textContent = title;
    document.getElementById("pin-input").value = "";
    document.getElementById("pin-error").textContent = "";
    document.getElementById("pin-overlay").classList.add("visible");
    document.getElementById("pin-input").focus();
  });
}
function closePin(value) {
  document.getElementById("pin-overlay").classList.remove("visible");
  if (pinResolve) { pinResolve(value); pinResolve = null; }
}

document.getElementById("pin-ok").onclick = () => closePin(document.getElementById("pin-input").value);
document.getElementById("pin-cancel").onclick = () => closePin(null);
document.getElementById("pin-input").addEventListener("keydown", e => {
  if (e.key === "Enter") closePin(document.getElementById("pin-input").value);
  if (e.key === "Escape") closePin(null);
});

// ─── FIREBASE STATE SYNC ─────────────────────────────────────────
async function pushState(state) {
  await set(STATE_REF, { ...state, ts: Date.now() });
}

function applyState(state) {
  if (!state) return;
  removedIndices = new Set(state.removed || []);
  currentAngle = state.angle || 0;
  drawWheel(currentAngle);

  const winner = state.winner;
  document.getElementById("btn-next").style.display =
    (winner != null) ? "inline-block" : "none";

  if (winner != null) showResult(winner);
  else hideResult();
}

onValue(STATE_REF, snap => {
  if (!spinning) applyState(snap.val());
});

// ─── INITIAL DRAW ─────────────────────────────────────────────────
(async () => {
  const snap = await get(STATE_REF);
  applyState(snap.val());
  setStatus("Подключено к Firebase ✓", "online");
})().catch(e => setStatus("Ошибка Firebase: " + e.message, "error"));

// ─── SPIN BUTTON ─────────────────────────────────────────────────
document.getElementById("btn-spin").onclick = async () => {
  const pin = await askPin("PIN для кручения");
  if (!pin) return;
  if (pin !== pins.spin) {
    document.getElementById("pin-error").textContent = "Неверный PIN";
    return;
  }
  closePin(pin);

  const active = activeTasks();
  if (active.length === 0) return;

  spinning = true;
  document.getElementById("btn-spin").disabled = true;
  document.getElementById("btn-reset").disabled = true;
  hideResult();

  // Random full spins + land on random sector
  const extraSpins = (3 + Math.floor(Math.random() * 4)) * Math.PI * 2;
  const targetOffset = Math.random() * Math.PI * 2;
  const targetAngle = currentAngle - extraSpins - targetOffset;
  const duration = 3500 + Math.random() * 1500;

  spinTo(targetAngle, duration, async () => {
    currentAngle = targetAngle;
    const winner = getWinnerIndex(currentAngle);
    spinning = false;
    document.getElementById("btn-spin").disabled = false;
    document.getElementById("btn-reset").disabled = false;
    document.getElementById("btn-next").style.display = "inline-block";
    showResult(winner);
    await pushState({ removed: [...removedIndices], angle: currentAngle, winner });
  });
};

// ─── NEXT BUTTON ─────────────────────────────────────────────────
document.getElementById("btn-next").onclick = async () => {
  const snap = await get(STATE_REF);
  const state = snap.val() || {};
  const winner = state.winner;
  if (winner == null) return;

  const newRemoved = new Set(removedIndices);
  newRemoved.add(winner);
  removedIndices = newRemoved;
  currentAngle = currentAngle; // keep angle

  hideResult();
  document.getElementById("btn-next").style.display = "none";
  drawWheel(currentAngle);

  await pushState({ removed: [...newRemoved], angle: currentAngle, winner: null });
};

// ─── RESET BUTTON ────────────────────────────────────────────────
document.getElementById("btn-reset").onclick = async () => {
  const pin = await askPin("PIN для сброса");
  if (!pin) return;
  if (pin !== pins.reset) {
    document.getElementById("pin-error").textContent = "Неверный PIN";
    return;
  }
  closePin(pin);

  removedIndices = new Set();
  currentAngle = 0;
  hideResult();
  document.getElementById("btn-next").style.display = "none";
  drawWheel(currentAngle);
  await pushState({ removed: [], angle: 0, winner: null });
};

// (weapons panel removed — arsenal is added to board via "📌 Добавить на доску")

// ─── HELPERS ─────────────────────────────────────────────────────
function escHtml(s) {
  return String(s || "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
function escAttr(s) {
  return String(s || "").replace(/"/g, "&quot;");
}
</script>
</body>
</html>
"""


if __name__ == "__main__":
    build()
