// ============= 状态管理器 =============
// 这个模块专门负责管理所有状态的保存和加载

class StateManager {
  constructor(docId) {
    this.docId = docId;
    this.GLOBAL_STORAGE_KEY = 'bilingual-reader-global-settings';
    this.DOC_STORAGE_KEY = `bilingual-reader-doc-settings-${docId}`;
    this.isInitializing = true;
    this.listeners = {};
    
    // 默认状态 - 分离全局和文档特定状态
    this.globalState = {
      // UI 设置
      fontSize: 16,
      spacing: 1,
      containerWidth: 100,
      
      // 显示模式
      syncMode: false,
      primaryDocIdx: 0,
      orientation: 'vertical',
      // 标记用户是否显式切换过方向（若为 false 则可由章节默认覆盖）
      userSetOrientation: false,
      
      // 外观
      isDarkTheme: true,
      ctrlPanelOpen: false,
      
      // 交互
      clickAction: 'swap',
      
      // 内容过滤
      searchQuery: '',
      
      // 每行对的展开/交换状态
      perPairExpanded: {},
      
      // 阅读进度设置
      saveReadingProgress: true
    };
    
    this.docState = {
      // 位置信息（文档特定）
      scrollTop: 0,
      panelScrollPercent: 0,
      lastActivePair: null
    };
    
    // 合并状态用于向后兼容
    this.state = { ...this.globalState, ...this.docState };
  }
  
  // 初始化：从 localStorage 加载状态
  init() {
    this.loadGlobal();
    this.loadDoc();
    this.isInitializing = false;
  }
  
  // 保存状态到 localStorage
  save() {
    // 初始化时不保存（避免保存默认值）
    if (this.isInitializing) return;
    
    this.saveGlobal();
    this.saveDoc();
    this.emit('save', this.state);
  }
  
  // 保存全局状态
  saveGlobal() {
    try {
      const data = JSON.stringify(this.globalState);
      localStorage.setItem(this.GLOBAL_STORAGE_KEY, data);
    } catch (e) {
      console.warn('Failed to save global state:', e);
      this.emit('error', { type: 'save', error: e });
    }
  }
  
  // 保存文档特定状态
  saveDoc() {
    try {
      const data = JSON.stringify(this.docState);
      localStorage.setItem(this.DOC_STORAGE_KEY, data);
    } catch (e) {
      console.warn('Failed to save doc state:', e);
      this.emit('error', { type: 'save', error: e });
    }
  }
  
  // 从 localStorage 加载状态
  load() {
    this.loadGlobal();
    this.loadDoc();
  }
  
  // 加载全局状态
  loadGlobal() {
    try {
      const saved = localStorage.getItem(this.GLOBAL_STORAGE_KEY);
      if (!saved) {
        // 首次加载：根据屏幕宽高比设置默认宽度
        const isPortrait = window.innerHeight > window.innerWidth;
        this.globalState.containerWidth = isPortrait ? 100 : 75;
        this.emit('load', { fresh: true });
        return;
      }
      
      const data = JSON.parse(saved);
      // 只覆盖已保存的属性，保留默认值
      this.globalState = { ...this.globalState, ...data };
      
      // 兼容迁移: 旧版 panelCollapsed → ctrlPanelOpen
      if ('panelCollapsed' in data && !('ctrlPanelOpen' in data)) {
        this.globalState.ctrlPanelOpen = data.panelCollapsed;
      }
      this.emit('load', { fresh: false, data: data });
    } catch (e) {
      console.warn('Failed to load global state:', e);
      this.emit('error', { type: 'load', error: e });
    }
  }
  
  // 加载文档特定状态
  loadDoc() {
    try {
      const saved = localStorage.getItem(this.DOC_STORAGE_KEY);
      if (saved) {
        const data = JSON.parse(saved);
        // 只覆盖已保存的属性，保留默认值
        this.docState = { ...this.docState, ...data };
      }
      // 文档特定状态没有首次加载的特殊处理
    } catch (e) {
      console.warn('Failed to load doc state:', e);
      this.emit('error', { type: 'load', error: e });
    }
    
    // 更新合并状态
    this.state = { ...this.globalState, ...this.docState };
  }
  
  // 设置单个状态值
  set(key, value) {
    const old = this.state[key];
    if (old === value) return; // 无变化则不保存
    
    this.state[key] = value;
    
    // 根据键的类型保存到对应状态对象
    if (this.isDocSpecificKey(key)) {
      this.docState[key] = value;
      this.saveDoc();
    } else {
      this.globalState[key] = value;
      this.saveGlobal();
    }
    
    this.emit('change', { key, oldValue: old, newValue: value });
  }
  
  // 判断是否为文档特定键
  isDocSpecificKey(key) {
    const docSpecificKeys = ['scrollTop', 'panelScrollPercent', 'lastActivePair'];
    return docSpecificKeys.includes(key);
  }
  
  // 获取状态值
  get(key) {
    return this.state[key];
  }
  
  // 批量设置状态
  setMany(updates) {
    const changes = {};
    let hasGlobalChanges = false;
    let hasDocChanges = false;
    
    for (const [key, value] of Object.entries(updates)) {
      if (this.state[key] !== value) {
        changes[key] = { old: this.state[key], new: value };
        this.state[key] = value;
        
        if (this.isDocSpecificKey(key)) {
          this.docState[key] = value;
          hasDocChanges = true;
        } else {
          this.globalState[key] = value;
          hasGlobalChanges = true;
        }
      }
    }
    
    if (Object.keys(changes).length > 0) {
      this.emit('changeMany', changes);
      if (hasGlobalChanges) this.saveGlobal();
      if (hasDocChanges) this.saveDoc();
    }
  }
  
  // 获取所有状态
  getAll() {
    return { ...this.state };
  }
  
  // 重置为默认值
  reset() {
    // 保存当前的阅读进度（文档特定状态）
    const savedScrollTop = this.docState.scrollTop;
    const savedPanelScrollPercent = this.docState.panelScrollPercent;
    const savedLastActivePair = this.docState.lastActivePair;
    
    // 根据当前屏幕宽高比设置默认宽度
    const isPortrait = window.innerHeight > window.innerWidth;
    const defaultWidth = isPortrait ? 100 : 75;
    
    // 重置全局状态
    this.globalState = {
      fontSize: 16,
      spacing: 1,
      containerWidth: defaultWidth,
      syncMode: false,
      primaryDocIdx: 0,
      orientation: 'vertical',
      isDarkTheme: true,
      ctrlPanelOpen: false,
      clickAction: 'swap',
      searchQuery: '',
      perPairExpanded: {},
      saveReadingProgress: true
    };
    
    // 重置文档特定状态，但保留阅读进度
    this.docState = {
      scrollTop: savedScrollTop,
      panelScrollPercent: savedPanelScrollPercent,
      lastActivePair: savedLastActivePair
    };
    
    // 更新合并状态
    this.state = { ...this.globalState, ...this.docState };
    
    this.emit('reset');
    this.saveGlobal(); // 只保存全局状态的重置
  }
  
  // 清除 localStorage
  clear() {
    try {
      localStorage.removeItem(this.GLOBAL_STORAGE_KEY);
      localStorage.removeItem(this.DOC_STORAGE_KEY);
      this.emit('clear');
    } catch (e) {
      console.warn('Failed to clear state:', e);
    }
  }
  
  // 订阅状态变化
  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }
  
  // 触发事件
  emit(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(cb => cb(data));
    }
  }
  
  // 取消订阅
  off(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    }
  }
}

// 创建全局状态管理器实例
const stateManager = new StateManager('__DOC_ID__');
