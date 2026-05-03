__STATE_MANAGER_CODE__

// ========== 公共 DOM 元素查询 ==========
const ctrlToggle = document.getElementById('ctrlToggle');
const ctrlPanel = document.getElementById('ctrlPanel');
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
const searchInput = document.getElementById('search');
const content = document.getElementById('content');

// 章节页面专属控件（在索引页面中为 null，所有引用处需判空）
const toggleSync = document.getElementById('toggleSync');
const togglePrimaryDoc = document.getElementById('togglePrimaryDoc');
const toggleOrientation = document.getElementById('toggleOrientation');
const positionSlider = document.getElementById('positionSlider');
const posInput = document.getElementById('posInput');
const clickActionSel = document.getElementById('clickAction');
const progressFill = document.getElementById('progressFill');

// 索引页面专属控件
const toggleLanguage = document.getElementById('toggleLanguage');
const langLabel = document.getElementById('langLabel');

// 标签元素（用于同步开关状态）
const primaryLabel = document.getElementById('primaryLabel');
const layoutLabel = document.getElementById('layoutLabel');

// ========== 公共变量和初始化 ==========
let isDarkTheme = true;
let ctrlPanelOpen = false;
// 将保存进度状态集中在 window 对象上，避免在多个模板中重复声明
window.saveReadingProgress = window.saveReadingProgress ?? true;
let saveReadingProgress = window.saveReadingProgress;
let scrollSaveTimer = null;

// 初始化状态管理器
stateManager.init();

// 读取全局初始状态并应用
const __globalInitialState = stateManager.getAll();
isDarkTheme = __globalInitialState.isDarkTheme;
ctrlPanelOpen = __globalInitialState.ctrlPanelOpen || false;
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
    if (isNaN(size) || size < 12 || size > 28) return;
    if (fontSlider) fontSlider.value = size;
    document.documentElement.style.setProperty('--font-size', size + 'px');
    stateManager.set('fontSize', size);
  });
}

if (spaceInput) {
  spaceInput.addEventListener('input', (e) => {
    const spacing = parseFloat(e.target.value);
    if (isNaN(spacing) || spacing < 0.5 || spacing > 3) return;
    if (spaceSlider) spaceSlider.value = spacing;
    document.documentElement.style.setProperty('--spacing', spacing);
    stateManager.set('spacing', spacing);
  });
}

if (widthInput) {
  widthInput.addEventListener('input', (e) => {
    const width = parseInt(e.target.value);
    if (isNaN(width) || width < 50 || width > 100) return;
    if (widthSlider) widthSlider.value = width;
    document.documentElement.style.setProperty('--container-width', width + '%');
    stateManager.set('containerWidth', width);
  });
}

if (posInput) {
  posInput.addEventListener('input', (e) => {
    const percent = parseFloat(e.target.value);
    if (isNaN(percent) || percent < 0 || percent > 100) return;
    if (positionSlider) positionSlider.value = percent;
    // goToPercent 由章节页面定义，使用 typeof 检查避免索引页面报错
    if (typeof goToPercent === 'function') {
      if (typeof isUpdatingPositionFromScroll !== 'undefined') {
        isUpdatingPositionFromScroll = true;
      }
      goToPercent(percent);
      if (typeof isUpdatingPositionFromScroll !== 'undefined') {
        setTimeout(() => { isUpdatingPositionFromScroll = false; }, 150);
      }
    }
    if (saveReadingProgress) {
      stateManager.set('panelScrollPercent', percent);
    }
  });
}

if (ctrlToggle) {
  ctrlToggle.addEventListener('click', (e) => {
    e.stopPropagation();
    ctrlPanelOpen = !ctrlPanelOpen;
    stateManager.set('ctrlPanelOpen', ctrlPanelOpen);
    syncStateToUI();
  });
}

// 点击面板外自动关闭
document.addEventListener('click', (e) => {
  if (ctrlPanelOpen && ctrlPanel && !ctrlPanel.contains(e.target) && e.target !== ctrlToggle) {
    ctrlPanelOpen = false;
    stateManager.set('ctrlPanelOpen', false);
    syncStateToUI();
  }
});

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

// ========== 唯一的 syncStateToUI 函数（覆盖所有控件，null-safe） ==========
function syncStateToUI() {
  const state = stateManager.getAll();

  // 确保 saveReadingProgress 始终从 state 中同步到全局变量
  window.saveReadingProgress = state.saveReadingProgress;
  saveReadingProgress = window.saveReadingProgress;

  // 同步面板展开状态
  if (ctrlPanel) {
    ctrlPanel.classList.toggle('open', state.ctrlPanelOpen);
  }
  if (ctrlToggle) {
    ctrlToggle.classList.toggle('active', state.ctrlPanelOpen);
  }

  // 同步滑块和输入值
  if (fontSlider) {
    fontSlider.value = state.fontSize;
    if (fontInput) fontInput.value = state.fontSize;
    document.documentElement.style.setProperty('--font-size', state.fontSize + 'px');
  }

  if (spaceSlider) {
    spaceSlider.value = state.spacing;
    if (spaceInput) spaceInput.value = state.spacing;
    document.documentElement.style.setProperty('--spacing', state.spacing);
  }

  if (widthSlider) {
    widthSlider.value = state.containerWidth;
    if (widthInput) widthInput.value = state.containerWidth;
    document.documentElement.style.setProperty('--container-width', state.containerWidth + '%');
  }

  if (positionSlider) {
    positionSlider.value = state.panelScrollPercent;
    if (posInput) posInput.value = parseFloat(state.panelScrollPercent).toFixed(2);
  }

  // 同步开关滑块（使用 .on class）
  if (toggleSync) {
    toggleSync.classList.toggle('on', state.syncMode);
  }

  if (togglePrimaryDoc) {
    togglePrimaryDoc.classList.toggle('on', state.primaryDocIdx === 0);
    if (primaryLabel) primaryLabel.textContent = state.primaryDocIdx === 0 ? 'Primary A' : 'Primary B';
  }

  if (toggleOrientation) {
    toggleOrientation.classList.toggle('on', state.orientation === 'vertical');
    if (layoutLabel) layoutLabel.textContent = state.orientation === 'vertical' ? 'Layout V' : 'Layout H';
  }

  if (toggleLanguage) {
    toggleLanguage.classList.toggle('on', state.currentLanguage === 'en');
    if (langLabel) langLabel.textContent = state.currentLanguage === 'cn' ? 'Chinese' : 'English';
  }

  // 同步主题（用开关表示暗色/亮色）
  if (state.isDarkTheme) {
    document.documentElement.classList.remove('light-theme');
  } else {
    document.documentElement.classList.add('light-theme');
  }
  if (toggleTheme) {
    toggleTheme.classList.toggle('on', state.isDarkTheme);
  }

  // 同步阅读进度保存设置
  if (toggleSaveProgress) {
    toggleSaveProgress.classList.toggle('on', state.saveReadingProgress);
  }

  // 同步搜索框
  if (searchInput) {
    searchInput.value = state.searchQuery || '';
  }

  // 同步点击行为选择器
  if (clickActionSel) {
    clickActionSel.value = state.clickAction || 'swap';
  }
}

// 初始同步UI
syncStateToUI();
