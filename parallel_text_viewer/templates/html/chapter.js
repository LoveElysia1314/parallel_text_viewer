// 从内联 JSON 加载章节数据
const pairs = __PAIRS_JSON__;
const titles = __TITLES_JSON__;

// 所有 DOM 元素已在 COMMON_JS 中声明，此处只定义章节专属状态变量
// 引用 COMMON_JS 中声明的变量: content, searchInput, toggleSync, togglePrimaryDoc,
//   toggleOrientation, positionSlider, posInput, clickActionSel, progressFill

// 与状态管理器同步的变量
let syncMode = false;
let primaryDocIdx = 0;
let orientation = '__ORIENTATION__';
let filteredCount = pairs.length;
let clickAction = 'swap';
let lastActivePair = null;
const expandedPairs = {};
const pairHeights = {};
let pairObserver = null;
let tempOverrideIdx = null;
let tempOverridePrimary = null;
let isUpdatingPositionFromScroll = false;
let isDragging = false;

// 移动端拖动检测，防止拖动时触发点击切换
content.addEventListener('touchstart', () => {
  isDragging = false;
});

content.addEventListener('touchmove', () => {
  isDragging = true;
});

// 从状态管理器读取所有状态值
const initialState = stateManager.getAll();
syncMode = initialState.syncMode;
primaryDocIdx = initialState.primaryDocIdx;
// 如果用户未显式切换过方向，则使用章节模板传入的默认方向
if (initialState.userSetOrientation) {
  orientation = initialState.orientation;
} else {
  orientation = '__ORIENTATION__';
}
clickAction = initialState.clickAction;
lastActivePair = initialState.lastActivePair;
saveReadingProgress = initialState.saveReadingProgress;
Object.assign(expandedPairs, initialState.perPairExpanded || {});

// 应用搜索查询
if (initialState.searchQuery) {
  searchInput.value = initialState.searchQuery;
  filter(initialState.searchQuery);
}

// 渲染内容
render();

// 更新页面标题
updatePageTitle();

// 恢复滚动位置
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

// ========== 章节页面专用事件处理 ==========
if (toggleSync) {
  toggleSync.addEventListener('click', () => {
    syncMode = !syncMode;
    stateManager.set('syncMode', syncMode);
    syncStateToUI();
    if (syncMode && tempOverrideIdx !== null) {
      clearTempOverride();
    }
    render();
  });
}

if (togglePrimaryDoc) {
  togglePrimaryDoc.addEventListener('click', () => {
    primaryDocIdx = 1 - primaryDocIdx;
    stateManager.set('primaryDocIdx', primaryDocIdx);
    syncStateToUI();
    updatePageTitle();
    render();
  });
}

if (toggleOrientation) {
  toggleOrientation.addEventListener('click', () => {
    const currentIdx = findClosestVisibleIndexToCenter();
    orientation = orientation === 'vertical' ? 'horizontal' : 'vertical';
    // 标记用户已显式切换方向，避免打开其它章节时被章节默认覆盖
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
}

if (searchInput) {
  searchInput.addEventListener('input', (e) => {
    filter(e.target.value);
    stateManager.set('searchQuery', e.target.value);
  });
}

window.addEventListener('scroll', () => {
  scrollTopBtn.classList.toggle('show', window.scrollY > 300);
  updateProgress();
  updatePositionFromCenter();
  // scrollTop 的保存由 common.js 的 scroll 处理器负责
  // 此处只需保存 panelScrollPercent（首次加载恢复位置用）
  if (saveReadingProgress) {
    if (window._posScrollTimer) clearTimeout(window._posScrollTimer);
    window._posScrollTimer = setTimeout(() => {
      const idx = findClosestVisibleIndexToCenter();
      const pct = indexToPercent(idx);
      stateManager.set('panelScrollPercent', pct);
    }, 200);
  }
});

// ========== 章节页面专用函数 ==========
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
  mainText.textContent = textA + '\n\n';
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
  sideText.textContent = textB + '\n\n';
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
    // Use innerHTML to render HTML content (like <img> tags), not just text
    mainBlock.querySelector('.text').innerHTML = pairs[i][localPrimary] + '\n\n';
    sideBlock.querySelector('.text').innerHTML = pairs[i][1 - localPrimary] + '\n\n';

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
  updatePositionFromCenter(); // 更新位置滑块以反映过滤后的状态
  scheduleRecomputeHeights();
}

function updateProgress() {
  const visible = Array.from(document.querySelectorAll('[data-pair]')).filter(p => p.style.display !== 'none').length;
  const progress = visible > 0 ? (visible / filteredCount) * 100 : 0;
  const progressFill = document.getElementById('progressFill');
  if (progressFill) progressFill.style.width = progress + '%';
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
  mainBlock.querySelector('.text').textContent = pairs[i][localPrimary] + '\n\n';
  sideBlock.querySelector('.text').textContent = pairs[i][1 - localPrimary] + '\n\n';
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
  // 当有搜索过滤时，基于可见pairs的数量进行计算
  const visiblePairs = Array.from(content.querySelectorAll('.pair-wrapper')).filter(p => p.style.display !== 'none');
  if (visiblePairs.length <= 1) return 0;
  // 找到当前idx在可见pairs中的位置
  const visibleIndices = visiblePairs.map(p => Number(p.dataset.pair)).sort((a, b) => a - b);
  const visibleIndex = visibleIndices.indexOf(idx);
  if (visibleIndex === -1) return 0;
  return (visibleIndex / (visibleIndices.length - 1)) * 100;
}

function percentToIndex(pct) {
  const visiblePairs = Array.from(content.querySelectorAll('.pair-wrapper')).filter(p => p.style.display !== 'none');
  if (visiblePairs.length === 0) return 0;
  if (visiblePairs.length === 1) return Number(visiblePairs[0].dataset.pair);
  // 获取可见pairs的索引数组
  const visibleIndices = visiblePairs.map(p => Number(p.dataset.pair)).sort((a, b) => a - b);
  const v = Math.round((pct / 100) * (visibleIndices.length - 1));
  const clampedIndex = Math.max(0, Math.min(v, visibleIndices.length - 1));
  return visibleIndices[clampedIndex];
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
  if (posInput) posInput.value = Number(pct).toFixed(2);
}

function goToPercent(pct) {
  const idx = percentToIndex(pct);
  const target = content.querySelector(`.pair-wrapper[data-pair='${idx}']`);
  if (!target || target.style.display === 'none') {
    // 如果目标被隐藏，找到最近的可见pair
    const visiblePairs = Array.from(content.querySelectorAll('.pair-wrapper')).filter(p => p.style.display !== 'none');
    if (visiblePairs.length === 0) return;
    const closestVisible = visiblePairs.reduce((closest, current) => {
      const currentIdx = Number(current.dataset.pair);
      const closestIdx = Number(closest.dataset.pair);
      return Math.abs(currentIdx - idx) < Math.abs(closestIdx - idx) ? current : closest;
    });
    closestVisible.scrollIntoView({ behavior: 'auto', block: 'center' });
    lastActivePair = Number(closestVisible.dataset.pair);
  } else {
    target.scrollIntoView({ behavior: 'auto', block: 'center' });
    lastActivePair = idx;
  }
  if (saveReadingProgress) {
    stateManager.set('lastActivePair', lastActivePair);
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

  // 延迟执行切换逻辑，以检查是否有选中文本或拖动（避免在选词或拖动时触发）
  setTimeout(() => {
    if (isDragging) {
      // 如果是拖动操作，则不执行切换
      return;
    }
    const selection = window.getSelection();
    if (selection.toString().trim() !== '') {
      // 如果有选中文本（例如双击选词），则不执行切换
      return;
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
  }, 200); // 延迟200ms，以确保双击选词和拖动检测有足够时间
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
  if (e.key === 'p' || e.key === 'P') { if (togglePrimaryDoc) togglePrimaryDoc.click(); }
  if (e.key === 's' || e.key === 'S') { if (toggleSync) toggleSync.click(); }
  if (e.key === 'o' || e.key === 'O') { if (toggleOrientation) toggleOrientation.click(); }
  if (e.key === 'ArrowUp') { e.preventDefault(); window.scrollBy(0, -100); }
});

// clickActionSel 已在 COMMON_JS 中声明，此处直接使用
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
    if (posInput) posInput.value = p.toFixed(2);
    goToPercent(p);
    if (saveReadingProgress) {
      stateManager.set('panelScrollPercent', p);
    }
    setTimeout(() => { isUpdatingPositionFromScroll = false; }, 150);
  });
}

// ========== 章节/卷 导航按钮逻辑（如模板提供 URL 占位符则启用）
const prevChapterBtn = document.getElementById('prevChapterBtn');
const nextChapterBtn = document.getElementById('nextChapterBtn');
const prevVolumeBtn = document.getElementById('prevVolumeBtn');
const nextVolumeBtn = document.getElementById('nextVolumeBtn');
const indexBtn = document.getElementById('indexBtn');

function setupNavBtn(btn) {
  if (!btn) return;
  const href = btn.dataset.href;
  if (!href || href === '#' || href.indexOf('__') !== -1) {
    btn.disabled = true;
    return;
  }
  btn.addEventListener('click', () => {
    window.location.href = href;
  });
}

setupNavBtn(prevChapterBtn);
setupNavBtn(nextChapterBtn);
setupNavBtn(prevVolumeBtn);
setupNavBtn(nextVolumeBtn);
setupNavBtn(indexBtn);
