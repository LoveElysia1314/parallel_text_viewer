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
