/*
 * Career Navigator — frontend logic.
 * Ванильный JS, без сборки — можно просто задеплоить эту папку как
 * статический сайт (Vercel/Netlify), не возясь с npm-пайплайном во время хакатона.
 */

// !!! Перед деплоем замените на адрес вашего задеплоенного backend !!!
const BACKEND_URL = window.CAREER_NAV_BACKEND_URL || "http://localhost:8000";

// --- Telegram WebApp init -----------------------------------------------
const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
}

function getTelegramId() {
  const fromTg = tg?.initDataUnsafe?.user?.id;
  if (fromTg) return fromTg;
  const params = new URLSearchParams(window.location.search);
  const fromQuery = params.get("tg_id");
  return fromQuery ? Number(fromQuery) : null;
}

// --- Состояние приложения ------------------------------------------------
const state = {
  analysis: null,      // весь AnalysisResult
  activeHypIndex: 0,
};

// --- Утилиты для экранов --------------------------------------------------
const screens = {
  profile: document.getElementById("screen-profile"),
  loading: document.getElementById("screen-loading"),
  error: document.getElementById("screen-error"),
  hypotheses: document.getElementById("screen-hypotheses"),
  skills: document.getElementById("screen-skills"),
  universities: document.getElementById("screen-universities"),
  roadmap: document.getElementById("screen-roadmap"),
};

function showResultScreens() {
  screens.profile.hidden = true;
  screens.loading.hidden = true;
  screens.error.hidden = true;
  screens.hypotheses.hidden = false;
  screens.skills.hidden = false;
  screens.universities.hidden = false;
  screens.roadmap.hidden = false;
  markRouteDone(["profile", "hypotheses", "skills", "universities", "roadmap"]);
}

function markRouteDone(activeStops) {
  document.querySelectorAll(".route__stop").forEach((el) => {
    const stop = el.dataset.stop;
    el.classList.toggle("is-done", activeStops.includes(stop));
  });
}

// Подсветка текущего пункта маршрута при прокрутке (scroll-spy)
const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      const id = entry.target.id.replace("screen-", "");
      const link = document.querySelector(`.route__stop[data-stop="${id}"]`);
      if (!link) return;
      link.classList.toggle("is-active", entry.isIntersecting);
    });
  },
  { rootMargin: "-20% 0px -70% 0px" }
);
[screens.profile, screens.hypotheses, screens.skills, screens.universities, screens.roadmap]
  .forEach((el) => observer.observe(el));

// --- Отправка формы -------------------------------------------------------
document.getElementById("profile-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const submitBtn = document.getElementById("submit-btn");
  submitBtn.disabled = true;

  const payload = {
    profile: {
      telegram_id: getTelegramId(),
      grade: Number(form.grade.value),
      interests: form.interests.value.trim(),
      favorite_subjects: form.favorite_subjects.value.trim(),
      current_skills: form.current_skills.value.trim(),
      values: form.values.value.trim() || null,
      budget_level: form.budget_level.value || null,
      country_pref: form.country_pref.value.trim() || null,
    },
  };

  screens.profile.hidden = true;
  screens.loading.hidden = false;

  try {
    const res = await fetch(`${BACKEND_URL}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const errBody = await res.json().catch(() => ({}));
      throw new Error(errBody.detail || `Ошибка сервера: ${res.status}`);
    }

    const data = await res.json();
    state.analysis = data.result;
    state.activeHypIndex = 0;

    renderHypotheses();
    showResultScreens();
  } catch (err) {
    screens.loading.hidden = true;
    screens.error.hidden = false;
    document.getElementById("error-text").textContent = err.message;
  } finally {
    submitBtn.disabled = false;
  }
});

document.getElementById("retry-btn").addEventListener("click", () => {
  screens.error.hidden = true;
  screens.profile.hidden = false;
});

document.getElementById("restart-btn").addEventListener("click", () => {
  state.analysis = null;
  Object.values(screens).forEach((s) => (s.hidden = true));
  screens.profile.hidden = false;
  document.getElementById("profile-form").reset();
  markRouteDone([]);
  window.scrollTo({ top: 0, behavior: "smooth" });
});

// --- Рендер экранов после получения ответа AI -----------------------------
function renderHypotheses() {
  const { hypotheses } = state.analysis;

  // Таб-переключатель гипотез
  const tabsEl = document.getElementById("hypotheses-tabs");
  tabsEl.innerHTML = "";
  hypotheses.forEach((hyp, i) => {
    const btn = document.createElement("button");
    btn.className = "hyp-tab" + (i === state.activeHypIndex ? " is-active" : "");
    btn.innerHTML = `${hyp.profession}<span class="hyp-tab__score">${hyp.match_score}%</span>`;
    btn.addEventListener("click", () => {
      state.activeHypIndex = i;
      renderHypotheses();
      renderSkills();
      renderUniversities();
      renderRoadmap();
    });
    tabsEl.appendChild(btn);
  });

  const hyp = hypotheses[state.activeHypIndex];

  document.getElementById("why-card").innerHTML = `
    <h2>${escapeHtml(hyp.profession)}</h2>
    <p>${escapeHtml(hyp.why)}</p>
  `;

  const chipsEl = document.getElementById("specializations");
  chipsEl.innerHTML = hyp.specializations
    .map((s) => `<span class="chip">${escapeHtml(s)}</span>`)
    .join("");

  renderSkills();
  renderUniversities();
  renderRoadmap();
}

function renderSkills() {
  const hyp = state.analysis.hypotheses[state.activeHypIndex];
  const el = document.getElementById("skills-list");
  el.innerHTML = hyp.skills_gap
    .map((s) => {
      const gap = Math.max(0, s.need_level - s.have_level);
      return `
        <div class="skill-item">
          <div class="skill-item__head">
            <span class="skill-item__name">${escapeHtml(s.skill)}</span>
            <span class="skill-item__gap">${gap > 0 ? `не хватает ${gap} п.п.` : "цель достигнута"}</span>
          </div>
          <div class="bar-track">
            <div class="bar-fill--have" style="width:${s.have_level}%"></div>
            <div class="bar-fill--need" style="left:${s.need_level}%"></div>
          </div>
          <p class="skill-item__note">${escapeHtml(s.how_to_improve)}</p>
        </div>
      `;
    })
    .join("");
}

function renderUniversities() {
  const hyp = state.analysis.hypotheses[state.activeHypIndex];
  const el = document.getElementById("uni-list");
  const budgetLabel = { low: "Бюджетный", medium: "Средний бюджет", high: "Любой бюджет" };
  el.innerHTML = hyp.universities
    .map(
      (u) => `
        <div class="uni-card">
          <div>
            <p class="uni-card__name">${escapeHtml(u.name)} · ${escapeHtml(u.country)}</p>
            <p class="uni-card__meta">${escapeHtml(u.program)}</p>
            <p class="uni-card__req">${escapeHtml(u.requirements)}</p>
          </div>
          <span class="budget-tag">${budgetLabel[u.budget_level] || u.budget_level}</span>
        </div>
      `
    )
    .join("");
}

function renderRoadmap() {
  const hyp = state.analysis.hypotheses[state.activeHypIndex];
  const el = document.getElementById("roadmap-list");
  el.innerHTML = hyp.roadmap
    .map(
      (step) => `
        <li>
          <p class="roadmap__time">${escapeHtml(step.timeframe)}</p>
          <p class="roadmap__action">${escapeHtml(step.action)}</p>
          <p class="roadmap__why">${escapeHtml(step.why)}</p>
        </li>
      `
    )
    .join("");
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}
