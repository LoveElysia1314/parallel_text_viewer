"""
索引页面专用模板组件

包含索引页面的专用CSS和JavaScript逻辑。
"""

from .common_template import COMMON_CSS, COMMON_JS

# 索引页面专用CSS（使用共享变量以复用暗黑/明亮配色）
INDEX_CSS = """
.work{margin-bottom:30px;border:1px solid rgba(255,255,255,0.06);border-radius:6px;overflow:hidden}
.work-title{background:var(--accent);color:var(--fg);padding:15px;margin:0;font-size:1.2em}
.volume{margin:15px;border-left:3px solid var(--accent);padding-left:15px}
.volume-title{color:var(--muted);margin:0 0 10px 0;font-size:1.1em}
.chapters{display:grid;grid-template-columns:repeat(4, 1fr);gap:8px;list-style:none;padding:0;margin:0}
.chapter{margin:0}
.chapter a{display:block;padding:8px 12px;background:var(--control-bg);color:var(--control-text);text-decoration:none;border-radius:4px;transition:background 0.2s,color 0.2s;text-align:center;font-size:14px;min-height:40px;display:flex;align-items:center;justify-content:center;border:1px solid var(--control-border)}
.chapter a:hover{background:var(--accent);color:var(--fg)}
.chapter.disabled a{background:var(--line);color:var(--muted);text-decoration:line-through;border-color:rgba(255,255,255,0.03)}
@media (max-width: 768px) {
  .chapters{grid-template-columns:repeat(2, 1fr);gap:6px}
  .chapter a{font-size:12px;min-height:35px;padding:6px 8px}
}
@media (max-width: 480px) {
  .chapters{grid-template-columns:1fr}
  .chapter a{font-size:14px;min-height:40px;padding:8px 12px}
}
"""

# 索引页面专用JavaScript
INDEX_JS = """
// 索引页面专用变量（searchInput, content 等公共元素已在 COMMON_JS 中声明）
let currentLanguage = 'cn'; // 默认中文

// 索引页面专用事件处理
const toggleLanguage = document.getElementById('toggleLanguage');

if (toggleLanguage) {
  toggleLanguage.addEventListener('click', () => {
    currentLanguage = currentLanguage === 'cn' ? 'en' : 'cn';
    stateManager.set('currentLanguage', currentLanguage);
    syncIndexToUI();
    renderIndex();
  });
}

if (searchInput) {
  searchInput.addEventListener('input', (e) => {
    filterChapters(e.target.value);
    stateManager.set('searchQuery', e.target.value);
  });
}

// 从状态管理器读取索引页面状态
const initialState = stateManager.getAll();
currentLanguage = initialState.currentLanguage || 'cn';
if (initialState.searchQuery) {
  if (searchInput) searchInput.value = initialState.searchQuery;
  filterChapters(initialState.searchQuery);
}

// 渲染索引页面
renderIndex();

// 索引页面专用函数
function renderIndex() {
  // content 已在 COMMON_JS 中声明为全局变量
  if (!content) return;

  // 这里应该从__INDEX_DATA__获取数据
  const indexData = __INDEX_DATA__ || {};

  let html = '';
  indexData.forEach(workData => {
    html += `<div class="work">`;
    html += `<h2 class="work-title">${workData.title || 'Unknown Work'}</h2>`;

    for (const [volumeId, volumeData] of Object.entries(workData.volumes || {})) {
      html += `<div class="volume">`;
      html += `<h3 class="volume-title">${volumeData.title || volumeId}</h3>`;
      html += `<ul class="chapters">`;

      const chapters = volumeData.chapters || [];
      chapters.forEach(chapter => {
        const isAvailable = !chapter.disabled;
        const chapterClass = isAvailable ? 'chapter' : 'chapter disabled';
        const chapterLink = isAvailable ?
          `<a href="${chapter.url || '#'}">${chapter.title || 'Unknown'}</a>` :
          `<span>${chapter.title || 'Unknown'}</span>`;
        html += `<li class="${chapterClass}">${chapterLink}</li>`;
      });

      html += `</ul>`;
      html += `</div>`;
    }

    html += `</div>`;
  });

  content.innerHTML = html;
}

function filterChapters(query) {
  const chapters = document.querySelectorAll('.chapter');
  const q = query.trim().toLowerCase();
  chapters.forEach(chapter => {
    const text = chapter.textContent.toLowerCase();
    const show = !q || text.includes(q);
    chapter.style.display = show ? 'block' : 'none';
  });
}

// 同步UI状态
function syncIndexToUI() {
  if (toggleLanguage) {
    toggleLanguage.textContent = currentLanguage === 'cn' ? 'Chinese' : 'English';
    toggleLanguage.setAttribute('aria-pressed', (currentLanguage === 'en').toString());
  }
}

// 初始同步UI（仅作用于索引页面的 UI 控件）
syncIndexToUI();
"""

# 索引页面完整HTML模板
INDEX_HTML_TEMPLATE = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>__TITLE__</title>
<style>
{COMMON_CSS}
{INDEX_CSS}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div>
      <h2 class="title-heading">__TITLE__</h2>
      <div style="color:var(--muted);font-size:13px">__DESCRIPTION__</div>
    </div>
  </div>

  <div class="control-panel" id="controlPanel">
    <input id="search" class="search" placeholder="Search chapters…" />

    <div class="panel-section two-col">
      <button id="toggleLanguage" class="panel-button" aria-pressed="false">Chinese</button>
      <button id="toggleTheme" class="panel-button" aria-pressed="false">🌙 Dark</button>
    </div>

    <div class="panel-section">
      <div class="slider-container">
        <span class="label-small">Font</span>
        <input type="range" id="fontSlider" class="slider" min="12" max="28" value="16" />
        <div class="slider-input-group">
          <input type="number" id="fontInput" min="12" max="28" value="16" />
          <span class="unit">px</span>
        </div>
      </div>
      <div class="slider-container">
        <span class="label-small">Width</span>
        <input type="range" id="widthSlider" class="slider" min="50" max="100" step="1" value="75" />
        <div class="slider-input-group">
          <input type="number" id="widthInput" min="50" max="100" step="1" value="75" />
          <span class="unit">%</span>
        </div>
      </div>
    </div>

    <div class="panel-section two-col">
      <button id="resetSettings" class="panel-button">↻ Reset</button>
    </div>

    <button id="togglePanel" class="panel-button" style="width:44px;height:44px;padding:0;margin:0;">−</button>
  </div>

  <div id="content"></div>

  <div class="footer">Select a chapter to start reading</div>
</div>

<button class="scroll-top-btn" id="scrollTopBtn">↑</button>

<script>
{COMMON_JS}
{INDEX_JS}
</script>
</body>
</html>
"""