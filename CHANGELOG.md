# 更新日志

## 0.7.0 (2026-05-21)

### 新增
- **数据管线支持**：新增 `repaired` 结构类型，支持 `vol_XXX/repaired/*.{target,source}.md` 格式
- **批量构建脚本**：`scripts/build_all.py` 支持一键构建 data/ 下所有作品
- **本地开发服务器**：`scripts/serve.py` 提供 HTTP 预览服务
- **构建选项增强**：`build_from_data.py` 新增 `--serve`、`--open` 参数
- **索引页增强**：作品展开后显示作者、简介、book_id 等信息
- **页面标题优化**：浏览器标签页显示 `章节名 - 卷名 - 作品名` 完整层级
- **汇总索引**：批量构建时自动生成作品列表页

### 修复
- **作品标题**：索引页和配置不再显示 "Book 2930"，改为 catalog 中的真实作品名
- **模板语法**：修复 index.html 中 `{{COMMON_JS}}` 被格式化器破坏的问题
- **数据源限定**：`raw/` 目录不再被回退使用（对齐前文本不用于生成阅读器）
- **Python 导入**：清理 `core.py`、`generators.py` 中未使用的导入
- **demo bug**：修复 `demo/demo.py` 中的损坏 f-string
- **包配置**：修复 `pyproject.toml` 中版本号与 `__init__.py` 不一致 (0.6.0→0.7.0)
- **包数据**：确保 `html_templates/` 目录随包一起分发

### 架构
- 两项目职责明确：`parallel-text-viewer` 消费数据、生成展示
  `BilingualRanobeReader` 生产数据（爬取→翻译→对齐）
- 需求文档 `docs/REQUIREMENTS_FOR_VIEWER_INTEGRATION.md` 写入 BilingualRanobeReader

## 0.6.0 (2026-05-17)

### 新增
- 可折叠书目目录结构（作品级 + 卷级两级折叠）
- `build_from_data()` 高层 API 支持端到端构建
- 状态管理器实现跨页面设置持久化
- 章节页面面包屑导航 + 上下章/卷跳转

### 架构
- 架构扁平化：5 子包 → 6 顶层模块 + 1 模板目录
- 删除废弃模块：`validator.py`、`image_placeholder.py`、`templates/*.py`
- 合并 `core/*`、`generators/*`、`utils/*`、`config/*` 到顶层模块

## 0.5.0 (2026-05-10)

- 初始公共版本
- Config v2.0 数据模型
- 双语 HTML 生成器（垂直/水平布局）
- 书目索引生成器
- CLI + Python API
