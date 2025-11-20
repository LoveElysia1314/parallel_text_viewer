"""
HTML 模板和样式定义 (v2 - 使用独立的状态管理器)

包含完整的 HTML 模板、CSS 样式和 JavaScript 脚本。
模板中的占位符将在生成时被替换。

这个版本将状态管理委托给 state_manager 模块。
"""

HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>__TITLE__</title>
<style>
:root{--bg:#0f1724;--panel:#0b1220;--fg:#e6eef8;--muted:#94a3b8;--accent:#60a5fa;--line:#111827;--font-size:16px;--spacing:1;--container-width:75%;--control-bg:#071123;--control-text:var(--fg);--control-border:rgba(255,255,255,0.06)}
:root.light-theme{--bg:#f5f5f5;--panel:#ffffff;--fg:#1a1a1a;--muted:#666666;--accent:#2563eb;--line:#eeeeee;--control-bg:#f5f5f5;--control-text:var(--fg);--control-border:rgba(0,0,0,0.06)}
body{font-family:Inter, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; margin:0; padding:0; background:var(--bg); color:var(--fg); transition:background 0.3s, color 0.3s;padding-bottom:80px}
.container{max-width:var(--container-width);margin:24px auto;padding:8px}
@media (aspect-ratio: 1 / 1.2){.container{margin:0;padding:0}}
.header{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:12px}
.controls{display:flex;gap:8px;align-items:center}
.search{padding:8px;border-radius:6px;border:1px solid var(--control-border);background:var(--control-bg);color:var(--control-text)}
.view-panel{display:grid;grid-template-columns:1fr 1fr;gap:calc(var(--font-size) * var(--spacing) * 1.8)}
@media (aspect-ratio: 1 / 1.2){.view-panel{gap:0;grid-template-columns:1fr}}
.col{background:var(--panel);padding:calc(var(--font-size) * var(--spacing) * 0.4) 8px;border-radius:8px;box-shadow:0 1px 0 rgba(255,255,255,0.03) inset;display:flex;flex-direction:column;gap:0}
@media (aspect-ratio: 1 / 1.2){.col{padding:calc(var(--font-size) * var(--spacing) * 0.4) 8px;border-radius:0;box-shadow:none}}
.pair-wrapper{display:flex;flex-direction:column;gap:0;padding:0;border-radius:6px}
.pair-wrapper.horizontal{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;align-items:start}
.pair-wrapper.horizontal .block-main, .pair-wrapper.horizontal .block-side{margin-bottom:0}
.pair-wrapper.horizontal .block-side.hidden{display:none}
.pair-wrapper.horizontal .block-main{grid-column:auto}
.pair-wrapper.horizontal .block-side{grid-column:auto}
.pair-wrapper.horizontal:has(.block-side.hidden) .block-main{grid-column:1/-1;margin-bottom:0}
.block-main, .block-side{display:block}
.block-side.hidden{display:none}
.row{padding:0;margin:0}
.line{padding:0 8px;padding-top:calc(var(--font-size) * max(0, min(0.25, var(--spacing) - 0.75)));padding-bottom:calc(var(--font-size) * max(0.25, var(--spacing) - 0.75));margin-top:calc(var(--font-size) * min(0, var(--spacing) - 0.75));border-radius:6px;background:transparent;white-space:pre-wrap;font-size:var(--font-size);line-height:calc(var(--spacing) + 0.5);min-height:var(--font-size)}
.line:hover{background:rgba(96,165,250,0.06);cursor:pointer}
.line:focus-visible{outline:2px solid rgba(96,165,250,0.8);outline-offset:2px}
.text{display:inline}
.block-main, .block-side{margin-bottom:0}
.pair-wrapper.highlight .line{background:rgba(96,165,250,0.08)}
.pair-wrapper.swapped{background:rgba(96,165,250,0.04)}
.pair-wrapper.expanded .block-side{display:block}
.float-toggle{position:fixed;right:20px;top:20px;background:var(--panel);border-radius:12px;padding:8px;box-shadow:0 8px 30px rgba(3,7,18,0.6)}
.float-toggle button{background:transparent;border:1px solid rgba(255,255,255,0.06);color:#e6eef8;padding:6px;border-radius:8px;margin:0 2px;cursor:pointer}
.float-toggle button.active{background:var(--accent);color:#07243b;border-color:transparent}
.kbd{background:#02111a;border:1px solid rgba(255,255,255,0.03);padding:4px;border-radius:6px;color:var(--muted);font-size:12px}
.footer{margin-top:20px;text-align:center;color:var(--muted);font-size:13px}
.hide{display:none}
.settings-panel{display:flex;gap:12px;align-items:center;flex-wrap:wrap;padding:8px;background:var(--line);border-radius:8px}
.slider-group{display:flex;gap:6px;align-items:center}
.slider{width:100px;height:6px;cursor:pointer}
.label-small{font-size:12px;color:var(--muted);min-width:40px}
.title-heading{font-size:calc(var(--font-size) * 1.25);font-weight:600;margin:0;line-height:1.3}
.panel-section{display:flex;flex-direction:column;gap:8px;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.06)}
.panel-section:last-child{border-bottom:none}
.panel-button{width:100%;background:transparent;border:1px solid rgba(255,255,255,0.06);color:var(--fg);padding:8px;border-radius:8px;cursor:pointer;white-space:nowrap;text-align:left;transition:all 0.2s}
.panel-button:hover{background:rgba(96,165,250,0.1);border-color:var(--accent)}
.panel-button.active{background:var(--accent);color:#07243b;border-color:transparent}
.slider-container{display:flex;gap:6px;align-items:center;width:100%}
.slider-container .label-small{flex-shrink:0}
.slider-container .slider{flex:1}
.slider-container .btn-icon{flex-shrink:0;padding:4px}
.slider-input-group{display:flex;gap:4px;align-items:center;flex-shrink:0}
.slider-input-group input{width:50px;padding:4px;border:1px solid rgba(255,255,255,0.06);background:var(--control-bg);color:var(--control-text);border-radius:4px;text-align:center;font-size:12px}
.slider-input-group .unit{font-size:12px;color:var(--muted);width:24px;text-align:left;flex-shrink:0}
.btn-icon{background:transparent;border:1px solid rgba(255,255,255,0.06);color:var(--fg);padding:6px;border-radius:8px;cursor:pointer;font-size:14px;transition:all 0.2s}
.btn-icon:hover{background:rgba(96,165,250,0.1);border-color:var(--accent)}
.progress-bar{width:100%;height:4px;background:var(--line);border-radius:2px;margin-top:8px;overflow:hidden}
.progress-fill{height:100%;background:var(--accent);transition:width 0.3s}
.stats{display:flex;gap:16px;font-size:12px;color:var(--muted);margin-top:8px}
.stat-item{display:flex;gap:4px}
.scroll-top-btn{position:fixed;bottom:20px;right:20px;background:var(--accent);color:#fff;border:none;width:40px;height:40px;border-radius:50%;cursor:pointer;display:none;z-index:999;font-size:18px;transition:opacity 0.3s}
.scroll-top-btn.show{display:flex;align-items:center;justify-content:center}
.control-panel{position:fixed;right:20px;top:20px;background:var(--panel);border-radius:12px;box-shadow:0 8px 30px rgba(3,7,18,0.6);z-index:1000;width:280px;transition:all 0.3s;max-height:calc(100vh - 40px);overflow-y:auto;display:flex;flex-direction:column;gap:0}
.control-panel.collapsed{width:44px;height:44px;padding:0;display:flex;align-items:center;justify-content:center}
.control-panel.collapsed > *:not(#togglePanel){display:none}
.control-panel:not(.collapsed){padding:8px}
.control-panel #togglePanel{position:absolute;right:0;top:0;z-index:1001;width:44px;height:44px;padding:0;display:flex;align-items:center;justify-content:center}
.control-panel .panel-section{margin:0}
.control-panel .search{width:100%;box-sizing:border-box;margin-bottom:8px}
.panel-section.two-col{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.panel-section.two-col > *{margin:0}
@media (aspect-ratio: 1 / 1.2){.view-panel{grid-template-columns:1fr};.control-panel{min-width:auto;max-width:calc(100vw - 40px);min-width:280px}.settings-panel{flex-direction:column;gap:8px}}
@media (prefers-reduced-motion: reduce){*{transition:none!important} }

/* 导航样式 */
.breadcrumb{margin-bottom:12px;font-size:14px;color:var(--muted)}
.breadcrumb a{color:var(--accent);text-decoration:none}
.breadcrumb a:hover{text-decoration:underline}
.chapter-nav, .volume-nav{display:flex;gap:8px;margin-bottom:8px;justify-content:center}
.nav-btn{background:var(--control-bg);border:1px solid var(--control-border);color:var(--control-text);padding:8px 12px;border-radius:6px;cursor:pointer;font-size:14px;transition:all 0.2s}
.nav-btn:hover{background:rgba(96,165,250,0.1);border-color:var(--accent)}
.nav-btn:disabled{background:var(--line);color:var(--muted);cursor:not-allowed;border-color:var(--line)}
.nav-btn:disabled:hover{background:var(--line);border-color:var(--line)}
/* 底部全宽导航 */
.bottom-nav{position:fixed;bottom:0;left:0;right:0;width:100%;background:var(--panel);border-top:1px solid var(--line);padding:12px 20px;z-index:1000;display:flex;justify-content:center;gap:12px;flex-wrap:wrap}
.bottom-nav .nav-btn{background:var(--control-bg);border:1px solid var(--control-border);color:var(--control-text);padding:10px 16px;border-radius:6px;cursor:pointer;font-size:14px;transition:all 0.2s}
.bottom-nav .nav-btn:hover{background:rgba(96,165,250,0.1);border-color:var(--accent)}
.bottom-nav .nav-btn:disabled{background:var(--line);color:var(--muted);cursor:not-allowed;border-color:var(--line)}
.bottom-nav .nav-btn:disabled:hover{background:var(--line);border-color:var(--line)}
.nav-message{position:fixed;top:20px;left:50%;transform:translateX(-50%);background:#e74c3c;color:white;padding:10px 20px;border-radius:5px;z-index:10000;font-weight:bold}
</style>
</head>
<body>
<div class="container">
  <div class="header">
      <div>
      <h2 id="pageTitle" class="title-heading">__TITLE__</h2>
      <div style="color:var(--muted);font-size:13px">__COUNT__ pairs</div>
    </div>
  </div>

  <div class="control-panel" id="controlPanel">
    <input id="search" class="search" placeholder="Search…" />

    <div class="panel-section two-col">
      <button id="toggleSync" class="panel-button" aria-pressed="false" aria-controls="content">Sync: OFF</button>
      <button id="togglePrimaryDoc" class="panel-button" aria-pressed="false" aria-controls="content">Primary: A</button>
    </div>

    <div class="panel-section two-col">
      <button id="toggleTheme" class="panel-button" aria-pressed="false">🌙 Dark</button>
      <button id="toggleOrientation" class="panel-button" aria-pressed="true">Layout: V</button>
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
        <span class="label-small">Space</span>
        <input type="range" id="spaceSlider" class="slider" min="0.5" max="3" step="0.1" value="1" />
        <div class="slider-input-group">
          <input type="number" id="spaceInput" min="0.5" max="3" step="0.1" value="1" />
          <span class="unit">x</span>
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
      <div class="slider-container">
        <span class="label-small">Pos</span>
        <input type="range" id="positionSlider" class="slider" min="0" max="100" step="0.1" value="0" aria-label="Scroll position percentage" title="Scroll to position percent" />
        <div class="slider-input-group">
          <input type="number" id="posInput" min="0" max="100" step="0.1" value="0" />
          <span class="unit">%</span>
        </div>
      </div>
    </div>

    <div class="panel-section two-col">
      <button id="resetSettings" class="panel-button">↻ Reset</button>
      <button id="clearSwaps" class="panel-button">✕ Swap</button>
    </div>

    <div class="panel-section">
      <div style="display:flex;gap:8px;align-items:center;">
        <label class="label-small">Click:</label>
        <select id="clickAction" class="search" style="flex:1;width:auto;">
          <option value="swap">Swap</option>
          <option value="expand">Expand</option>
        </select>
      </div>
    </div>

    <div class="panel-section two-col">
      <button id="toggleSaveProgress" class="panel-button" aria-pressed="true">📖 Progress: ON</button>
      <button id="clearProgress" class="panel-button">🗑️ Clear Progress</button>
    </div>

    <button id="togglePanel" class="panel-button" style="width:44px;height:44px;padding:0;margin:0;">−</button>
  </div>  <div class="progress-bar">
    <div class="progress-fill" id="progressFill"></div>
  </div>

  <div id="content" class="col" style="min-height:400px"></div>

  <div class="footer">Tip: hover a line to highlight the pair. Click to mark the pair.</div>
</div>

<button class="scroll-top-btn" id="scrollTopBtn">↑</button>

<script>
__STATE_MANAGER_CODE__

const pairs = __PAIRS_JSON__;
const titles = __TITLES_JSON__;
const content = document.getElementById('content');
const searchInput = document.getElementById('search');
const toggleSync = document.getElementById('toggleSync');
const togglePrimaryDoc = document.getElementById('togglePrimaryDoc');
const toggleTheme = document.getElementById('toggleTheme');
const scrollTopBtn = document.getElementById('scrollTopBtn');
const progressFill = document.getElementById('progressFill');
const controlPanel = document.getElementById('controlPanel');
const toggleOrientation = document.getElementById('toggleOrientation');
const togglePanel = document.getElementById('togglePanel');
const resetSettings = document.getElementById('resetSettings');
const fontSlider = document.getElementById('fontSlider');
const spaceSlider = document.getElementById('spaceSlider');
const widthSlider = document.getElementById('widthSlider');
const positionSlider = document.getElementById('positionSlider');
const fontInput = document.getElementById('fontInput');
const spaceInput = document.getElementById('spaceInput');
const widthInput = document.getElementById('widthInput');
const posInput = document.getElementById('posInput');

// 与状态管理器同步的变量
let syncMode = false;
let primaryDocIdx = 0;
let orientation = '__ORIENTATION__';
let isDarkTheme = true;
let filteredCount = pairs.length;
let panelCollapsed = false;
let clickAction = 'swap';
let lastActivePair = null;
// 集中管理保存进度的全局开关，避免在多个模板中重复声明
window.saveReadingProgress = window.saveReadingProgress ?? true;
let saveReadingProgress = window.saveReadingProgress;
const expandedPairs = {};
const pairHeights = {};
let pairObserver = null;
let tempOverrideIdx = null;
let tempOverridePrimary = null;
let scrollSaveTimer = null;
let isUpdatingPositionFromScroll = false;

// ========== 初始化 ==========
// 1. 加载状态
stateManager.init();

// 2. 从状态管理器读取所有状态值
const initialState = stateManager.getAll();
syncMode = initialState.syncMode;
primaryDocIdx = initialState.primaryDocIdx;
// 若用户没有显式切换过方向，则使用章节/生成时传入的默认方向
if (initialState.userSetOrientation) {
  orientation = initialState.orientation;
} else {
  orientation = '__ORIENTATION__';
}
isDarkTheme = initialState.isDarkTheme;
panelCollapsed = initialState.panelCollapsed;
clickAction = initialState.clickAction;
lastActivePair = initialState.lastActivePair;
saveReadingProgress = initialState.saveReadingProgress;
Object.assign(expandedPairs, initialState.perPairExpanded || {});

// 3. 同步 UI 到状态
syncStateToUI();

// 4. 应用设置
document.documentElement.style.setProperty('--font-size', initialState.fontSize + 'px');
document.documentElement.style.setProperty('--spacing', initialState.spacing);
document.documentElement.style.setProperty('--container-width', initialState.containerWidth + '%');

// 5. 应用搜索查询
if (initialState.searchQuery) {
  searchInput.value = initialState.searchQuery;
  filter(initialState.searchQuery);
}

// 6. 渲染内容
render();

// 6.5 更新页面标题
updatePageTitle();

// 7. 恢复滚动位置
requestAnimationFrame(() => {
  if (initialState.panelScrollPercent > 0) {
    goToPercent(initialState.panelScrollPercent);
  } else if (initialState.scrollTop > 0) {
    window.scrollTo(0, initialState.scrollTop);
  }
  
  // 高亮最后活跃的行
  if (lastActivePair !== null) {
    const p = content.querySelector(`.pair-wrapper[data-pair='${lastActivePair}']`);
    if (p) {
      p.scrollIntoView({ behavior: 'auto', block: 'center' });
      p.classList.add('highlight');
    }
  }
});

// ========== 事件处理 ==========
// 这些处理器现在调用状态管理器

toggleSync.addEventListener('click', () => {
  syncMode = !syncMode;
  stateManager.set('syncMode', syncMode);
  syncStateToUI();
  if (syncMode && tempOverrideIdx !== null) {
    clearTempOverride();
  }
  render();
});

togglePrimaryDoc.addEventListener('click', () => {
  primaryDocIdx = 1 - primaryDocIdx;
  stateManager.set('primaryDocIdx', primaryDocIdx);
  syncStateToUI();
  updatePageTitle();
  render();
});

toggleTheme.addEventListener('click', () => {
  isDarkTheme = !isDarkTheme;
  stateManager.set('isDarkTheme', isDarkTheme);
  syncStateToUI();
});

toggleOrientation.addEventListener('click', () => {
  const currentIdx = findClosestVisibleIndexToCenter();
  orientation = orientation === 'vertical' ? 'horizontal' : 'vertical';
  stateManager.set('orientation', orientation);
  stateManager.set('userSetOrientation', true);
  Object.keys(pairHeights).forEach(k => delete pairHeights[k]);
  syncStateToUI();
  render();
  
  requestAnimationFrame(() => {
    const targetWrapper = content.querySelector(`.pair-wrapper[data-pair='${currentIdx}']`);
    if (targetWrapper) {
      targetWrapper.scrollIntoView({ behavior: 'auto', block: 'center' });
    }
  });
});

fontSlider.addEventListener('input', (e) => {
  const size = e.target.value;
  fontInput.value = size;
  document.documentElement.style.setProperty('--font-size', size + 'px');
  scheduleRecomputeHeights();
  stateManager.set('fontSize', parseInt(size));
});

spaceSlider.addEventListener('input', (e) => {
  const spacing = e.target.value;
  spaceInput.value = spacing;
  document.documentElement.style.setProperty('--spacing', spacing);
  scheduleRecomputeHeights();
  stateManager.set('spacing', parseFloat(spacing));
});

widthSlider.addEventListener('input', (e) => {
  const width = e.target.value;
  widthInput.value = width;
  document.documentElement.style.setProperty('--container-width', width + '%');
  stateManager.set('containerWidth', parseInt(width));
});

searchInput.addEventListener('input', (e) => {
  filter(e.target.value);
  stateManager.set('searchQuery', e.target.value);
});

togglePanel.addEventListener('click', () => {
  panelCollapsed = !panelCollapsed;
  stateManager.set('panelCollapsed', panelCollapsed);
  syncStateToUI();
});

resetSettings.addEventListener('click', () => {
  if (confirm('Reset all settings to default?')) {
    stateManager.reset();
    location.reload();
  }
});

window.addEventListener('scroll', () => {
  scrollTopBtn.classList.toggle('show', window.scrollY > 300);
  updateProgress();
  updatePositionFromCenter();
  if (saveReadingProgress) {
    if (scrollSaveTimer) clearTimeout(scrollSaveTimer);
    scrollSaveTimer = setTimeout(() => {
      stateManager.set('scrollTop', Math.round(window.scrollY));
    }, 200);
  }
});

window.addEventListener('beforeunload', () => {
  stateManager.save();
});

// ========== 核心功能函数 ==========

let _recomputeTimer = null;
function scheduleRecomputeHeights() {
  if (_recomputeTimer) clearTimeout(_recomputeTimer);
  _recomputeTimer = setTimeout(() => {
    Object.keys(pairHeights).forEach(k => delete pairHeights[k]);
    const visiblePairs = Array.from(content.querySelectorAll('.pair-wrapper')).filter(p => p.style.display !== 'none').map(p => Number(p.dataset.pair));
    if (visiblePairs.length) applyEqualHeightsForPairs(visiblePairs);
  }, 150);
}

function createPair(pairIdx, textA, textB) {
  const wrapper = document.createElement('div');
  wrapper.className = 'pair-wrapper';
  wrapper.dataset.pair = pairIdx;
  
  const mainBlock = document.createElement('div');
  mainBlock.className = 'block-main';
  const mainRow = document.createElement('div');
  mainRow.className = 'row';
  mainRow.tabIndex = 0;
  mainRow.setAttribute('role', 'button');
  const mainLine = document.createElement('div');
  mainLine.className = 'line';
  const mainText = document.createElement('span');
  mainText.className = 'text';
  mainText.textContent = textA + '\\n\\n';
  mainLine.appendChild(mainText);
  mainRow.appendChild(mainLine);
  mainBlock.appendChild(mainRow);

  const sideBlock = document.createElement('div');
  sideBlock.className = 'block-side';
  const sideRow = document.createElement('div');
  sideRow.className = 'row';
  sideRow.tabIndex = 0;
  sideRow.setAttribute('role', 'button');
  const sideLine = document.createElement('div');
  sideLine.className = 'line';
  const sideText = document.createElement('span');
  sideText.className = 'text';
  sideText.textContent = textB + '\\n\\n';
  sideLine.appendChild(sideText);
  sideRow.appendChild(sideLine);
  sideBlock.appendChild(sideRow);

  wrapper.appendChild(mainBlock);
  wrapper.appendChild(sideBlock);
  return wrapper;
}

function highlight(i, on) {
  const mainBlock = content.querySelector(`[data-pair='${i}']`);
  if (mainBlock) mainBlock.classList.toggle('highlight', on);
}

function render() {
  content.innerHTML = '';
  const frag = document.createDocumentFragment();
  pairs.forEach((p, i) => {
    const [textA, textB] = [p[0], p[1]];
    const wrapper = createPair(i, textA, textB);

    const mainBlock = wrapper.querySelector('.block-main');
    const sideBlock = wrapper.querySelector('.block-side');

    const localPrimary = getPairPrimaryIdx(i);
    mainBlock.querySelector('.text').textContent = pairs[i][localPrimary] + '\\n\\n';
    sideBlock.querySelector('.text').textContent = pairs[i][1 - localPrimary] + '\\n\\n';

    wrapper.classList.toggle('horizontal', orientation === 'horizontal');
    const isExpanded = !!expandedPairs[i];
    wrapper.classList.toggle('expanded', isExpanded);
    if (syncMode) {
      mainBlock.classList.remove('hidden');
      sideBlock.classList.remove('hidden');
      sideBlock.setAttribute('aria-hidden', 'false');
    } else {
      mainBlock.classList.remove('hidden');
      if (isExpanded) {
        sideBlock.classList.remove('hidden');
        sideBlock.setAttribute('aria-hidden', 'false');
      } else {
        sideBlock.classList.add('hidden');
        sideBlock.setAttribute('aria-hidden', 'true');
      }
    }
    wrapper.classList.toggle('swapped', localPrimary !== primaryDocIdx);

    frag.appendChild(wrapper);
  });
  content.appendChild(frag);
  updateProgress();
  if (pairObserver) { pairObserver.disconnect(); pairObserver = null; }
  if (typeof IntersectionObserver !== 'undefined') {
    pairObserver = new IntersectionObserver(entries => {
      const toMeasure = [];
      entries.forEach(en => { if (en.isIntersecting) toMeasure.push(Number(en.target.dataset.pair)); });
      if (toMeasure.length) applyEqualHeightsForPairs(toMeasure);
    }, { root: null, rootMargin: '500px 0px' });
    Array.from(content.querySelectorAll('[data-pair]')).forEach(n => pairObserver.observe(n));
  }
  const visiblePairs = Array.from(content.querySelectorAll('[data-pair]')).filter(p => p.style.display !== 'none').map(p => Number(p.dataset.pair));
  if (visiblePairs.length) applyEqualHeightsForPairs(visiblePairs);
}

function filter(q) {
  const s = q.trim().toLowerCase();
  filteredCount = 0;
  pairs.forEach((p, i) => {
    const mainBlock = content.querySelector(`[data-pair='${i}']`);
    if (!s) {
      mainBlock.style.display = 'block';
      filteredCount++;
      return;
    }
    const inA = p[0].toLowerCase().includes(s);
    const inB = p[1].toLowerCase().includes(s);
    const show = inA || inB;
    mainBlock.style.display = show ? 'block' : 'none';
    if (show) filteredCount++;
  });
  updateProgress();
  scheduleRecomputeHeights();
}

function updateProgress() {
  const visible = Array.from(document.querySelectorAll('[data-pair]')).filter(p => p.style.display !== 'none').length;
  const progress = visible > 0 ? (visible / filteredCount) * 100 : 0;
  progressFill.style.width = progress + '%';
}

function getPairPrimaryIdx(i) {
  if (tempOverrideIdx === i && typeof tempOverridePrimary !== 'undefined' && tempOverridePrimary !== null) return tempOverridePrimary;
  return primaryDocIdx;
}

function updatePageTitle() {
  const docLabels = ['a', 'b'];
  const displayDoc = docLabels[primaryDocIdx];
  const titleText = titles[displayDoc] || '__TITLE__';
  document.title = titleText;
  const h2 = document.querySelector('h2');
  if (h2) h2.textContent = titleText;
}

function setTempOverride(i, primary) {
  if (tempOverrideIdx !== null && tempOverrideIdx !== i) {
    clearTempOverride();
  }
  tempOverrideIdx = i;
  tempOverridePrimary = Number(primary);
}

function clearTempOverride() {
  tempOverrideIdx = null;
  tempOverridePrimary = null;
}

function renderPair(i) {
  const wrapper = content.querySelector(`.pair-wrapper[data-pair='${i}']`);
  if (!wrapper) return;
  const mainBlock = wrapper.querySelector('.block-main');
  const sideBlock = wrapper.querySelector('.block-side');
  const localPrimary = getPairPrimaryIdx(i);
  mainBlock.querySelector('.text').textContent = pairs[i][localPrimary] + '\\n\\n';
  sideBlock.querySelector('.text').textContent = pairs[i][1 - localPrimary] + '\\n\\n';
  wrapper.classList.toggle('horizontal', orientation === 'horizontal');
  const isExpanded = !!expandedPairs[i];
  wrapper.classList.toggle('expanded', isExpanded);
  if (syncMode) {
    mainBlock.classList.remove('hidden');
    sideBlock.classList.remove('hidden');
    sideBlock.setAttribute('aria-hidden', 'false');
  } else {
    mainBlock.classList.remove('hidden');
    if (isExpanded) {
      sideBlock.classList.remove('hidden');
      sideBlock.setAttribute('aria-hidden', 'false');
    } else {
      sideBlock.classList.add('hidden');
      sideBlock.setAttribute('aria-hidden', 'true');
    }
  }
  wrapper.classList.toggle('swapped', localPrimary !== primaryDocIdx);
  applyEqualHeightsForPairs([i]);
}

function applyEqualHeightsForPairs(indices) {
  if (!Array.isArray(indices) || indices.length === 0) return;
}

function indexToPercent(idx) {
  if (pairs.length <= 1) return 0;
  // map index in [0, pairs.length-1] to percent in [0,100]
  return (idx / (pairs.length - 1)) * 100;
}

function percentToIndex(pct) {
  const v = Math.round((pct / 100) * (pairs.length - 1));
  return Math.max(0, Math.min(v, pairs.length - 1));
}

function findClosestVisibleIndexToCenter() {
  const centerY = window.scrollY + window.innerHeight / 2;
  let bestIdx = 0;
  let bestDist = Infinity;
  pairs.forEach((p, i) => {
    const mainBlock = content.querySelector(`[data-pair='${i}']`);
    if (!mainBlock || mainBlock.style.display === 'none') return;
    const mainRow = mainBlock.querySelector('.row');
    if (!mainRow) return;
    const rect = mainRow.getBoundingClientRect();
    const top = rect.top + window.scrollY;
    const mainCenter = top + rect.height / 2;
    const dist = Math.abs(mainCenter - centerY);
    if (dist < bestDist) {
      bestDist = dist;
      bestIdx = i;
    }
  });
  return bestIdx;
}

function updatePositionFromCenter() {
  if (!positionSlider) return;
  if (isUpdatingPositionFromScroll) return;
  const idx = findClosestVisibleIndexToCenter();
  const pct = indexToPercent(idx);
  positionSlider.value = Number(pct).toFixed(1);
  posInput.value = Number(pct).toFixed(2);
}

function goToPercent(pct) {
  const idx = percentToIndex(pct);
  const target = content.querySelector(`.pair-wrapper[data-pair='${idx}']`);
  if (!target) return;
  target.scrollIntoView({ behavior: 'auto', block: 'center' });
  lastActivePair = idx;
  if (saveReadingProgress) {
    stateManager.set('lastActivePair', idx);
  }
}

content.addEventListener('click', (e) => {
  const row = e.target.closest('.row');
  if (!row) return;
  const pair = row.closest('.pair-wrapper');
  if (!pair) return;
  const idx = Number(pair.dataset.pair);
  lastActivePair = idx;
  if (saveReadingProgress) {
    stateManager.set('lastActivePair', idx);
  }

  if (clickAction === 'swap' && !syncMode) {
    const currPrimary = getPairPrimaryIdx(idx);
    const newPrimary = 1 - currPrimary;
    if (tempOverrideIdx === idx) {
      clearTempOverride();
    } else {
      setTempOverride(idx, newPrimary);
    }
  } else if (clickAction === 'expand') {
    expandedPairs[idx] = !expandedPairs[idx];
    stateManager.set('perPairExpanded', expandedPairs);
  }
  renderPair(idx);
});

content.addEventListener('pointerover', (e) => {
  const pair = e.target.closest('.pair-wrapper');
  if (pair) {
    highlight(pair.dataset.pair, true);
  }
});

content.addEventListener('pointerout', (e) => {
  const pair = e.target.closest('.pair-wrapper');
  if (pair) {
    highlight(pair.dataset.pair, false);
  }
});

document.addEventListener('keydown', (e) => {
  if (e.key === 'p' || e.key === 'P') { togglePrimaryDoc.click(); }
  if (e.key === 's' || e.key === 'S') { toggleSync.click(); }
  if (e.key === 'o' || e.key === 'O') { toggleOrientation.click(); }
  if (e.key === 'ArrowUp') { e.preventDefault(); window.scrollBy(0, -100); }
});

scrollTopBtn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));

const clickActionSel = document.getElementById('clickAction');
if (clickActionSel) {
  clickActionSel.addEventListener('change', (e) => {
    clickAction = e.target.value;
    stateManager.set('clickAction', clickAction);
    clearTempOverride();
    if (clickAction === 'swap') {
      Object.keys(expandedPairs).forEach(k => delete expandedPairs[k]);
    }
    render();
  });
}

const clearSwapsBtn = document.getElementById('clearSwaps');
if (clearSwapsBtn) {
  clearSwapsBtn.addEventListener('click', () => {
    if (tempOverrideIdx !== null) {
      const idx = tempOverrideIdx;
      clearTempOverride();
      renderPair(idx);
    }
  });
}

const toggleSaveProgress = document.getElementById('toggleSaveProgress');
if (toggleSaveProgress) {
  toggleSaveProgress.addEventListener('click', () => {
    saveReadingProgress = !saveReadingProgress;
    stateManager.set('saveReadingProgress', saveReadingProgress);
    syncStateToUI();
  });
}

const clearProgressBtn = document.getElementById('clearProgress');
if (clearProgressBtn) {
  clearProgressBtn.addEventListener('click', () => {
    if (confirm('Clear all reading progress for this document?')) {
      // 清除文档特定的阅读进度状态
      stateManager.set('scrollTop', 0);
      stateManager.set('panelScrollPercent', 0);
      stateManager.set('lastActivePair', null);
      // 重新加载页面以应用更改
      location.reload();
    }
  });
}

if (positionSlider) {
  positionSlider.addEventListener('input', (e) => {
    isUpdatingPositionFromScroll = true;
    const p = parseFloat(e.target.value);
    posInput.value = p.toFixed(2);
    goToPercent(p);
    if (saveReadingProgress) {
      stateManager.set('panelScrollPercent', p);
    }
    setTimeout(() => { isUpdatingPositionFromScroll = false; }, 150);
  });
}

</script>
</body>
</html>
"""
