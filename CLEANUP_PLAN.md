# 代码清理计划

## 待删除的 v1.0 遗留代码

### 1. 整个目录（待删除）
- [ ] `parallel_text_viewer/builders/` - v1.0 书籍构建器（全部过时）
- [ ] `parallel_text_viewer/extractors/` - v1.0 提取器（全部过时）
- [ ] `parallel_text_viewer/organizers/` - v1.0 组织策略（全部过时）
- [ ] `parallel_text_viewer/pairing/` - v1.0 文件配对（全部过时）
- [ ] `parallel_text_viewer/scanners/` - v1.0 扫描器（全部过时）
- [ ] `parallel_text_viewer/models/` - v1.0 数据模型（全部过时）

### 2. 冗余脚本（待删除）
- [ ] `scripts/conversion_cli.py` - 交互式 CLI（被 build_from_data.py 取代）
- [ ] `scripts/check_catalog_images.py` - 检查图片（可选，低优先级）
- [ ] `scripts/inject_images_from_dir.py` - 注入图片（可选，低优先级）

### 3. 过时 API（待删除）
- [ ] `parallel_text_viewer/api.py` - v1.0 API（被 v2.0 CLI 取代）
- [ ] `parallel_text_viewer/core/config_engine.py` - v1.0 配置引擎

### 4. v1.0 相关代码块
- [ ] `__main__.py` 中的所有 v1.0 命令处理
- [ ] `cli/dispatcher.py` 中的所有 v1.0 命令

## 保留的代码

### 核心 v2.0 模块
- ✓ `parallel_text_viewer/core/config_v2.py` - Config v2.0 核心
- ✓ `parallel_text_viewer/core/image_placeholder.py` - 图片占位符
- ✓ `parallel_text_viewer/config/generator.py` - 配置生成器
- ✓ `parallel_text_viewer/generators/` - HTML 生成器
- ✓ `parallel_text_viewer/templates/` - HTML 模板
- ✓ `parallel_text_viewer/cli/dispatcher.py` - CLI 分发（仅 v2.0 命令）
- ✓ `parallel_text_viewer/cli/parser.py` - 参数解析

### 主脚本
- ✓ `scripts/build_from_data.py` - 端到端构建脚本
- ✓ `scripts/verify_config_v2.py` - 验证脚本

## 删除策略

1. **第一阶段**：删除整个目录（builders、extractors等）
2. **第二阶段**：删除冗余脚本（conversion_cli等）
3. **第三阶段**：清理 API 和配置引擎
4. **第四阶段**：清理 __main__.py 和 dispatcher.py 中的 v1.0 代码
5. **第五阶段**：验证功能完整性

## 优先级

### 高（立即删除）
- builders/
- extractors/
- organizers/
- pairing/
- scanners/
- models/
- api.py
- conversion_cli.py

### 中（需要检查后删除）
- config_engine.py
- __main__.py 中的 v1.0 部分

### 低（保留观察）
- check_catalog_images.py
- inject_images_from_dir.py
