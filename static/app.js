const $ = (sel) => document.querySelector(sel);

const state = {
  sessionId: null,
  chart: null,
  questions: [],
};

function show(el, yes) {
  el.classList.toggle("hidden", !yes);
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderPillars(chart) {
  const pillars = chart.pillars;
  const map = [
    ["year", "年柱"],
    ["month", "月柱"],
    ["day", "日柱"],
    ["time", "時柱"],
  ];
  $("#pillars").innerHTML = map
    .map(([k, label]) => {
      const p = pillars[k];
      return `
        <div class="pillar">
          <div class="name">${label}</div>
          <div class="gz">${escapeHtml(p.text)}</div>
          <div class="detail">
            天干：${escapeHtml(p.gan)}（${escapeHtml(p.ganElement)}）<br/>
            地支：${escapeHtml(p.zhi)}（${escapeHtml(p.zhiElement)}）
          </div>
        </div>
      `;
    })
    .join("");
}

function renderElements(chart) {
  const counts = chart.fiveElements.counts;
  const percent = chart.fiveElements.percent;
  const order = ["木", "火", "土", "金", "水"];
  $("#elements").innerHTML = order
    .map((e) => {
      const p = percent[e] ?? 0;
      const c = counts[e] ?? 0;
      return `
        <div class="bar">
          <div class="row"><span>${escapeHtml(e)}</span><span>${c}（${p}%）</span></div>
          <div class="track"><div class="fill" style="width:${p}%"></div></div>
        </div>
      `;
    })
    .join("");
}

function renderQuestions(questions) {
  $("#questions").innerHTML = questions
    .map((q, idx) => {
      const id = q.id;
      return `
        <div class="q" data-qid="${escapeHtml(id)}">
          <div class="text">${idx + 1}. ${escapeHtml(q.text)}</div>
          <div class="opts">
            <label class="pill">
              <input type="radio" name="${escapeHtml(id)}" value="yes" />
              是
            </label>
            <label class="pill">
              <input type="radio" name="${escapeHtml(id)}" value="no" />
              否
            </label>
          </div>
        </div>
      `;
    })
    .join("");
}

function gatherAnswers() {
  const answers = {};
  for (const q of state.questions) {
    const yes = document.querySelector(`input[name="${CSS.escape(q.id)}"][value="yes"]:checked`);
    const no = document.querySelector(`input[name="${CSS.escape(q.id)}"][value="no"]:checked`);
    if (yes) answers[q.id] = true;
    if (no) answers[q.id] = false;
  }
  return answers;
}

function renderResult(payload) {
  const past = payload.pastReview;
  const future = payload.future;
  const sum = future.summary;

  const focus = (sum.focus || []).map((x) => `<li>${escapeHtml(x)}</li>`).join("");
  const tips = (sum.tips || []).map((x) => `<li>${escapeHtml(x)}</li>`).join("");

  const timelineRows = (future.timeline || [])
    .map((y) => {
      const badge =
        y.level === "順勢"
          ? `<span class="badge ok">順勢</span>`
          : y.level === "保守"
          ? `<span class="badge no">保守</span>`
          : `<span class="badge">平穩</span>`;
      return `
        <tr>
          <td>${escapeHtml(y.year)}</td>
          <td>${escapeHtml(y.yearElement)}</td>
          <td>${badge}</td>
          <td>${escapeHtml(y.advice)}</td>
        </tr>
      `;
    })
    .join("");

  const reviewRows = (past.items || [])
    .map((it, idx) => {
      const b = it.matched ? `<span class="badge ok">符合</span>` : `<span class="badge no">不符</span>`;
      const exp = it.expectedYes ? "是" : "否";
      const ans = it.yourAnswer ? "是" : "否";
      return `
        <tr>
          <td>${idx + 1}</td>
          <td>${escapeHtml(it.question)}</td>
          <td>${escapeHtml(exp)} / ${escapeHtml(ans)} ${b}</td>
          <td>${escapeHtml(it.rationale)}</td>
        </tr>
      `;
    })
    .join("");

  $("#result").innerHTML = `
    <div class="panel">
      <div class="kpi">
        <span class="tag">作答：${past.answered}/${past.total}</span>
        <span class="tag">符合：${past.matched}/${past.total}</span>
        <span class="tag">匹配分數：${past.matchScore}</span>
        <span class="tag">可信度：${escapeHtml(future.confidence)}</span>
        <span class="tag">日主：${escapeHtml(sum.dayMasterElement)}（${escapeHtml(sum.dayMasterStrength)}）</span>
      </div>
    </div>

    <div class="panel">
      <h3>核心解讀</h3>
      <ul>${focus}</ul>
      <h3>行動建議</h3>
      <ul>${tips}</ul>
      <p class="hint">${escapeHtml(future.note || "")}</p>
    </div>

    <div class="panel">
      <h3>未來 5 年趨勢</h3>
      <table class="table">
        <thead>
          <tr>
            <th style="width:86px">年份</th>
            <th style="width:72px">年五行</th>
            <th style="width:86px">強弱</th>
            <th>建議</th>
          </tr>
        </thead>
        <tbody>
          ${timelineRows}
        </tbody>
      </table>
    </div>

    <div class="panel">
      <h3>過去 5 年驗證回顧</h3>
      <table class="table">
        <thead>
          <tr>
            <th style="width:56px">題</th>
            <th>問題</th>
            <th style="width:180px">預期 / 你的回答</th>
            <th>推演理由</th>
          </tr>
        </thead>
        <tbody>
          ${reviewRows}
        </tbody>
      </table>
    </div>
  `;
}

async function postJson(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return await res.json();
}

function setBusy(btn, yes, textWhenBusy) {
  btn.disabled = !!yes;
  if (yes) {
    btn.dataset.prevText = btn.textContent;
    btn.textContent = textWhenBusy || "處理中…";
  } else if (btn.dataset.prevText) {
    btn.textContent = btn.dataset.prevText;
    delete btn.dataset.prevText;
  }
}

function resetAll() {
  state.sessionId = null;
  state.chart = null;
  state.questions = [];
  $("#pillars").innerHTML = "";
  $("#elements").innerHTML = "";
  $("#questions").innerHTML = "";
  $("#result").innerHTML = "";
  show($("#step1"), true);
  show($("#step2"), false);
  show($("#step3"), false);
}

window.addEventListener("DOMContentLoaded", () => {
  const form = $("#form");
  const btnChart = $("#btnChart");
  const btnResult = $("#btnResult");

  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    try {
      setBusy(btnChart, true, "排盤中…");
      const payload = await postJson("/api/chart", {
        birthDate: $("#birthDate").value,
        birthTime: $("#birthTime").value,
        gender: $("#gender").value,
        city: $("#city").value || "",
      });
      state.sessionId = payload.sessionId;
      state.chart = payload.chart;
      state.questions = payload.verificationQuestions || [];

      renderPillars(state.chart);
      renderElements(state.chart);
      renderQuestions(state.questions);

      show($("#step1"), false);
      show($("#step2"), true);
      show($("#step3"), false);
    } catch (e) {
      alert(`排盤失敗：${e.message || e}`);
    } finally {
      setBusy(btnChart, false);
    }
  });

  $("#btnBack").addEventListener("click", () => {
    show($("#step1"), true);
    show($("#step2"), false);
    show($("#step3"), false);
  });

  btnResult.addEventListener("click", async () => {
    if (!state.sessionId) {
      alert("找不到 session，請重新排盤。");
      return;
    }
    try {
      setBusy(btnResult, true, "生成中…");
      const answers = gatherAnswers();
      const payload = await postJson("/api/result", { sessionId: state.sessionId, answers });
      renderResult(payload);

      show($("#step1"), false);
      show($("#step2"), false);
      show($("#step3"), true);
    } catch (e) {
      alert(`生成失敗：${e.message || e}`);
    } finally {
      setBusy(btnResult, false);
    }
  });

  $("#btnRestart").addEventListener("click", () => resetAll());
});

