"""
公共模板组件 - 包含共享的CSS和JavaScript逻辑

这些组件被章节页面和索引页面共享。
"""

# 公共CSS样式
COMMON_CSS = """
:root{--bg:#0f1724;--panel:#0b1220;--fg:#e6eef8;--muted:#94a3b8;--accent:#60a5fa;--line:#111827;--font-size:16px;--spacing:1;--container-width:75%;--control-bg:#071123;--control-text:var(--fg);--control-border:rgba(255,255,255,0.06)}
:root.light-theme{--bg:#f5f5f5;--panel:#ffffff;--fg:#1a1a1a;--muted:#666666;--accent:#2563eb;--line:#eeeeee;--control-bg:#f5f5f5;--control-text:var(--fg);--control-border:rgba(0,0,0,0.06)}
body{font-family:Inter, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; margin:0; padding:0; background:var(--bg); color:var(--fg); transition:background 0.3s, color 0.3s;padding-bottom:80px}
.container{max-width:var(--container-width);margin:24px auto;padding:8px}
@media (aspect-ratio: 1 / 1.2){.container{margin:0;padding:0}}
.header{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:12px}
.controls{display:flex;gap:8px;align-items:center}
.search{padding:8px;border-radius:6px;border:1px solid var(--control-border);background:var(--control-bg);color:var(--control-text)}
.footer{margin-top:20px;text-align:center;color:var(--muted);font-size:13px}
.hide{display:none}
.title-heading{font-size:calc(var(--font-size) * 1.25);font-weight:600;margin:0;line-height:1.3;word-break:break-word;overflow-wrap:break-word}
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
.label-small{font-size:12px;color:var(--muted);min-width:40px}
.slider{width:100px;height:6px;cursor:pointer}
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
@media (aspect-ratio: 1 / 1.2){.control-panel{min-width:auto;max-width:calc(100vw - 40px);min-width:280px}}
@media (prefers-reduced-motion: reduce){*{transition:none!important} }
"""

# 公共JavaScript逻辑
COMMON_JS = """
__STATE_MANAGER_CODE__

// 公共变量和初始化
let isDarkTheme = true;
let panelCollapsed = false;
// 将保存进度状态集中在 window 对象上，避免在多个模板中重复声明
window.saveReadingProgress = window.saveReadingProgress ?? true;
let saveReadingProgress = window.saveReadingProgress;
let scrollSaveTimer = null;

// ========== 事件处理 ==========
const controlPanel = document.getElementById('controlPanel');
const togglePanel = document.getElementById('togglePanel');
const resetSettings = document.getElementById('resetSettings');
const toggleTheme = document.getElementById('toggleTheme');
const fontSlider = document.getElementById('fontSlider');
const spaceSlider = document.getElementById('spaceSlider');
const widthSlider = document.getElementById('widthSlider');
const fontInput = document.getElementById('fontInput');
const spaceInput = document.getElementById('spaceInput');
const widthInput = document.getElementById('widthInput');
const scrollTopBtn = document.getElementById('scrollTopBtn');
const toggleSaveProgress = document.getElementById('toggleSaveProgress');
const positionSlider = document.getElementById('positionSlider');
const posInput = document.getElementById('posInput');

// 初始化状态管理器放到 DOM 元素查询之后，避免在 block-scoped 变量声明前触发 syncStateToUI 导致 ReferenceError
stateManager.init();

// 读取全局初始状态并应用
const __globalInitialState = stateManager.getAll();
isDarkTheme = __globalInitialState.isDarkTheme;
panelCollapsed = __globalInitialState.panelCollapsed;
window.saveReadingProgress = __globalInitialState.saveReadingProgress;
saveReadingProgress = window.saveReadingProgress;

// Apply initial settings
document.documentElement.style.setProperty('--font-size', __globalInitialState.fontSize + 'px');
document.documentElement.style.setProperty('--spacing', __globalInitialState.spacing);
document.documentElement.style.setProperty('--container-width', __globalInitialState.containerWidth + '%');

// ========== 事件处理 ==========
if (toggleTheme) {
  toggleTheme.addEventListener('click', () => {
    isDarkTheme = !isDarkTheme;
    stateManager.set('isDarkTheme', isDarkTheme);
    syncStateToUI();
  });
}

if (fontSlider) {
  fontSlider.addEventListener('input', (e) => {
    const size = e.target.value;
    if (fontInput) fontInput.value = size;
    document.documentElement.style.setProperty('--font-size', size + 'px');
    stateManager.set('fontSize', parseInt(size));
  });
}

if (spaceSlider) {
  spaceSlider.addEventListener('input', (e) => {
    const spacing = e.target.value;
    if (spaceInput) spaceInput.value = spacing;
    document.documentElement.style.setProperty('--spacing', spacing);
    stateManager.set('spacing', parseFloat(spacing));
  });
}

if (widthSlider) {
  widthSlider.addEventListener('input', (e) => {
    const width = e.target.value;
    if (widthInput) widthInput.value = width;
    document.documentElement.style.setProperty('--container-width', width + '%');
    stateManager.set('containerWidth', parseInt(width));
  });
}

// 数值输入框事件监听，确保与滑块同步
if (fontInput) {
  fontInput.addEventListener('input', (e) => {
    const size = parseInt(e.target.value);
    if (isNaN(size) || size < 12 || size > 28) return; // 验证范围
    if (fontSlider) fontSlider.value = size;
    document.documentElement.style.setProperty('--font-size', size + 'px');
    stateManager.set('fontSize', size);
  });
}

if (spaceInput) {
  spaceInput.addEventListener('input', (e) => {
    const spacing = parseFloat(e.target.value);
    if (isNaN(spacing) || spacing < 0.5 || spacing > 3) return; // 验证范围
    if (spaceSlider) spaceSlider.value = spacing;
    document.documentElement.style.setProperty('--spacing', spacing);
    stateManager.set('spacing', spacing);
  });
}

if (widthInput) {
  widthInput.addEventListener('input', (e) => {
    const width = parseInt(e.target.value);
    if (isNaN(width) || width < 50 || width > 100) return; // 验证范围
    if (widthSlider) widthSlider.value = width;
    document.documentElement.style.setProperty('--container-width', width + '%');
    stateManager.set('containerWidth', width);
  });
}

if (posInput) {
  posInput.addEventListener('input', (e) => {
    const percent = parseFloat(e.target.value);
    if (isNaN(percent) || percent < 0 || percent > 100) return; // 验证范围
    if (positionSlider) positionSlider.value = percent;
    // 对于位置输入框，需要调用goToPercent函数
    if (typeof goToPercent === 'function') {
      goToPercent(percent);
    }
    if (saveReadingProgress) {
      stateManager.set('panelScrollPercent', percent);
    }
  });
}

if (togglePanel) {
  togglePanel.addEventListener('click', () => {
    panelCollapsed = !panelCollapsed;
    stateManager.set('panelCollapsed', panelCollapsed);
    syncStateToUI();
  });
}

if (resetSettings) {
  resetSettings.addEventListener('click', () => {
    if (confirm('Reset all settings to default?')) {
      stateManager.reset();
      location.reload();
    }
  });
}

if (toggleSaveProgress) {
  toggleSaveProgress.addEventListener('click', () => {
    saveReadingProgress = !saveReadingProgress;
    stateManager.set('saveReadingProgress', saveReadingProgress);
    syncStateToUI();
  });
}

if (scrollTopBtn) {
  scrollTopBtn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
}

window.addEventListener('scroll', () => {
  if (scrollTopBtn) {
    scrollTopBtn.classList.toggle('show', window.scrollY > 300);
  }
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

// ========== 辅助函数 ==========
function syncStateToUI() {
  const state = stateManager.getAll();

  // 确保 saveReadingProgress 始终从 state 中同步到全局变量，避免重复声明问题
  window.saveReadingProgress = state.saveReadingProgress;
  saveReadingProgress = window.saveReadingProgress;

  // 同步滑块和输入值
  if (fontSlider) {
    fontSlider.value = state.fontSize;
    if (fontInput) fontInput.value = state.fontSize;
  }

  if (spaceSlider) {
    spaceSlider.value = state.spacing;
    if (spaceInput) spaceInput.value = state.spacing;
  }

  if (widthSlider) {
    widthSlider.value = state.containerWidth;
    if (widthInput) widthInput.value = state.containerWidth;
  }

  // 同步主题
  // 同步主题（使用 `light-theme` 类在 :root 上切换亮色变量）
  if (state.isDarkTheme) {
    document.documentElement.classList.remove('light-theme');
    if (toggleTheme) toggleTheme.textContent = '🌙 Dark';
  } else {
    document.documentElement.classList.add('light-theme');
    if (toggleTheme) toggleTheme.textContent = '☀️ Light';
  }

  if (toggleTheme) {
    toggleTheme.setAttribute('aria-pressed', state.isDarkTheme.toString());
  }

  // 同步面板折叠状态
  if (controlPanel) {
    controlPanel.classList.toggle('collapsed', state.panelCollapsed);
  }

  if (togglePanel) {
    togglePanel.textContent = state.panelCollapsed ? '☰' : '−';
    togglePanel.setAttribute('aria-expanded', (!state.panelCollapsed).toString());
  }

  // 同步阅读进度保存设置
  if (toggleSaveProgress) {
    toggleSaveProgress.textContent = state.saveReadingProgress ? '📖 Progress: ON' : '📖 Progress: OFF';
    toggleSaveProgress.setAttribute('aria-pressed', state.saveReadingProgress.toString());
  }
}

// 初始同步UI
syncStateToUI();
"""