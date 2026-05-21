// ═══════════════════════════════════════════════════════════════
// 索引页面 — 作品/卷/章 层级目录
// 支持：作品层级可折叠（默认收起）、卷层级可折叠（默认收起）、搜索自动展开
// ═══════════════════════════════════════════════════════════════

let currentLanguage = "cn"; // 当前显示语言（cn/en）
let worksCollapsed = {}; // { workTitle: true/false } — 作品折叠状态
let volumesCollapsed = {}; // { "workTitle|volTitle": true/false } — 卷折叠状态
let isSearchActive = false; // 搜索激活时临时展开所有层级

// ── 从状态管理器恢复索引页面状态 ──
(function loadIndexState() {
  const saved = stateManager.getAll();
  currentLanguage = saved.currentLanguage || "cn";
  worksCollapsed = saved.worksCollapsed || {};
  volumesCollapsed = saved.volumesCollapsed || {};
})();

// ── 事件绑定：语言切换 ──
if (toggleLanguage) {
  toggleLanguage.addEventListener("click", () => {
    currentLanguage = currentLanguage === "cn" ? "en" : "cn";
    stateManager.set("currentLanguage", currentLanguage);
    syncIndexToUI();
    renderIndex();
  });
}

// ── 事件绑定：搜索过滤 ──
if (searchInput) {
  searchInput.addEventListener("input", (e) => {
    const q = e.target.value.trim();
    isSearchActive = !!q;
    stateManager.set("searchQuery", q);
    // 搜索激活时重新渲染（展开所有），清空时恢复折叠状态
    renderIndex();
  });
}

// 恢复搜索框内容
(function restoreSearch() {
  const saved = stateManager.getAll();
  if (saved.searchQuery && searchInput) {
    searchInput.value = saved.searchQuery;
    isSearchActive = true;
  }
})();

// ── 事件代理：作品/卷的折叠/展开点击 ──
document.addEventListener("click", (e) => {
  const workHeader = e.target.closest(".work-header");
  const volHeader = e.target.closest(".volume-header");

  if (workHeader) {
    const title = workHeader.dataset.workTitle;
    const isCollapsed = worksCollapsed[title] !== false; // 默认 true（收起）
    worksCollapsed = { ...worksCollapsed, [title]: !isCollapsed };
    stateManager.set("worksCollapsed", worksCollapsed);
    renderIndex();
    return;
  }

  if (volHeader) {
    const key = volHeader.dataset.volKey;
    const isCollapsed = volumesCollapsed[key] !== false; // 默认 true（收起）
    volumesCollapsed = { ...volumesCollapsed, [key]: !isCollapsed };
    stateManager.set("volumesCollapsed", volumesCollapsed);
    renderIndex();
    return;
  }
});

// ── 渲染主函数 ──
function renderIndex() {
  if (!content) return;

  const indexData = __INDEX_DATA__ || [];

  if (!indexData.length) {
    content.innerHTML = '<div class="empty-state">暂无书目数据</div>';
    return;
  }

  const container = document.createElement("div");

  indexData.forEach((workData) => {
    const workTitle = workData.title || "未知作品";
    const volumes = workData.volumes || {};
    const volEntries = Object.entries(volumes);
    const totalChapters = volEntries.reduce(
      (sum, [, v]) => sum + (v.chapters || []).length,
      0,
    );

    // ── 作品层级 ──
    const workEl = document.createElement("div");
    workEl.className = "work";

    // 作品头部（可点击）
    const isWorkCollapsed = isSearchActive
      ? false
      : worksCollapsed[workTitle] !== false;
    const workHeader = createWorkHeader(
      workTitle,
      volEntries.length,
      totalChapters,
      isWorkCollapsed,
      workData.author,
      workData.description,
      workData.book_id,
    );
    workEl.appendChild(workHeader);

    // 作品简介（展开时显示）
    if (!isWorkCollapsed && (workData.author || workData.description)) {
      const metaEl = createWorkMeta(
        workData.author,
        workData.description,
        workData.book_id,
      );
      workEl.appendChild(metaEl);
    }

    // 作品内容体
    const workBody = document.createElement("div");
    workBody.className = `work-body${isWorkCollapsed ? " collapsed" : ""}`;

    // ── 遍历卷 ──
    volEntries.forEach(([volId, volData]) => {
      const volTitle = volData.title || volId;
      const volKey = workTitle + "|" + volTitle;
      const chapters = volData.chapters || [];
      const isVolCollapsed = isSearchActive
        ? false
        : volumesCollapsed[volKey] !== false;

      const volEl = document.createElement("div");
      volEl.className = "volume";

      // 卷头部（可点击）
      const volHeader = createVolumeHeader(
        volTitle,
        chapters.length,
        isVolCollapsed,
        volKey,
      );
      volEl.appendChild(volHeader);

      // 卷内容体
      const volBody = document.createElement("div");
      volBody.className = `volume-body${isVolCollapsed ? " collapsed" : ""}`;
      volBody.appendChild(createChapterList(chapters));
      volEl.appendChild(volBody);
      workBody.appendChild(volEl);
    });

    workEl.appendChild(workBody);
    container.appendChild(workEl);
  });

  content.innerHTML = "";
  content.appendChild(container);
  syncIndexToUI();
  applySearchFilter();
}

// ── 创建作品头部 DOM ──
function createWorkHeader(
  title,
  volCount,
  chCount,
  isCollapsed,
  author,
  description,
  bookId,
) {
  const header = document.createElement("div");
  header.className = "work-header";
  header.dataset.workTitle = title;

  const icon = document.createElement("span");
  icon.className = `toggle-icon${isCollapsed ? " collapsed" : ""}`;
  icon.textContent = "▼";

  const titleEl = document.createElement("h3");
  titleEl.className = "work-title-text";
  titleEl.textContent = title;

  const meta = document.createElement("span");
  meta.className = "work-meta";
  meta.textContent = `${chCount} 章 · ${volCount} 卷`;

  header.append(icon, titleEl, meta);
  return header;
}

// ── 创建作品元信息 DOM ──
function createWorkMeta(author, description, bookId) {
  const container = document.createElement("div");
  container.className = "work-meta-info";

  const info = document.createElement("div");
  info.className = "work-meta-content";

  if (author) {
    const authorEl = document.createElement("div");
    authorEl.className = "work-author";
    authorEl.textContent = `✎ ${author}`;
    info.appendChild(authorEl);
  }

  if (description) {
    const descEl = document.createElement("div");
    descEl.className = "work-description";
    descEl.textContent = description;
    info.appendChild(descEl);
  }

  if (bookId) {
    const idEl = document.createElement("div");
    idEl.className = "work-book-id";
    idEl.textContent = `#${bookId}`;
    info.appendChild(idEl);
  }

  container.appendChild(info);
  return container;
}

// ── 创建卷头部 DOM ──
function createVolumeHeader(title, chCount, isCollapsed, volKey) {
  const header = document.createElement("div");
  header.className = "volume-header";
  header.dataset.volKey = volKey;

  const icon = document.createElement("span");
  icon.className = `toggle-icon${isCollapsed ? " collapsed" : ""}`;
  icon.textContent = "▶";

  const titleEl = document.createElement("h4");
  titleEl.className = "volume-title-text";
  titleEl.textContent = title;

  const meta = document.createElement("span");
  meta.className = "volume-meta";
  meta.textContent = `${chCount} 章`;

  header.append(icon, titleEl, meta);
  return header;
}

// ── 创建章节列表 DOM ──
function createChapterList(chapters) {
  const ul = document.createElement("ul");
  ul.className = "chapters";

  chapters.forEach((chapter) => {
    const li = document.createElement("li");
    const isAvailable = !chapter.disabled;
    li.className = `chapter${isAvailable ? "" : " disabled"}`;

    if (isAvailable) {
      const a = document.createElement("a");
      a.href = chapter.url || "#";
      a.textContent = chapter.title || "未知章节";
      li.appendChild(a);
    } else {
      const span = document.createElement("span");
      span.textContent = chapter.title || "未知章节";
      li.appendChild(span);
    }

    ul.appendChild(li);
  });

  return ul;
}

// ── 搜索过滤（隐藏不匹配的章节 → 隐藏空的卷 → 隐藏空的作品） ──
function applySearchFilter() {
  if (!searchInput) return;
  const q = searchInput.value.trim().toLowerCase();
  if (!q) return;

  // 隐藏不匹配的章节
  document.querySelectorAll(".chapter").forEach((el) => {
    const text = el.textContent.toLowerCase();
    el.style.display = text.includes(q) ? "" : "none";
  });

  // 隐藏没有可见章节的卷
  document.querySelectorAll(".volume").forEach((vol) => {
    const visibleChs = [...vol.querySelectorAll(".chapter")].some(
      (c) => c.style.display !== "none",
    );
    vol.style.display = visibleChs ? "" : "none";
    // 卷标头总是可见，但如果没有匹配章节则整体隐藏卷卡片
  });

  // 隐藏没有可见卷的作品
  document.querySelectorAll(".work").forEach((work) => {
    const visibleVols = [...work.querySelectorAll(".volume")].some(
      (v) => v.style.display !== "none",
    );
    work.style.display = visibleVols ? "" : "none";
  });
}

// ── 同步 UI 控件状态 ──
function syncIndexToUI() {
  if (toggleLanguage) {
    toggleLanguage.textContent =
      currentLanguage === "cn" ? "Chinese" : "English";
    toggleLanguage.setAttribute(
      "aria-pressed",
      (currentLanguage === "en").toString(),
    );
  }
}

// ── 更新页脚信息 ──
(function updateFooter() {
  const bookCountEl = document.getElementById("bookCount");
  if (bookCountEl) {
    const count = (__INDEX_DATA__ || []).length;
    bookCountEl.textContent = `共 ${count} 部作品`;
  }
})();

// ── 初始渲染 ──
renderIndex();
