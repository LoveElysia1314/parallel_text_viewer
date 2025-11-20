# 脚本使用指南

注意：项目已在重构过程中移除了部分旧的 v1 脚本（例如 `check_catalog_images.py`、`inject_images_from_dir.py` 和 `conversion_cli.py`）。
这些脚本的文档仍保留在此处以便参考，但对应的脚本文件已从仓库中移除。若你需要这些工具，请联系维护者或从历史提交中恢复。

本目录包含用于检查和管理 `catalog.json` 图片配置的工具脚本（部分已移除）。

## 脚本列表

### 1. check_catalog_images.py - 检查配置中的图片字段

**功能**：扫描 catalog.json 并报告各章节的图片配置情况。

**使用方法**：
```bash
python scripts/check_catalog_images.py <catalog.json>
```

**示例**：
```bash
python scripts/check_catalog_images.py demo/catalog_2930.json
```

**输出信息**：
- ✓ 是否设置了 `meta.base_image_path`
- 📸 包含图片的章节数量及明细
- ⚠️ 缺失图片的章节数量及列表
- 💡 针对缺失图片的建议操作

### 2. inject_images_from_dir.py - 自动注入本地图片

**功能**：扫描本地 images 目录，自动发现图片并注入到 catalog.json。

**使用方法**：
```bash
python scripts/inject_images_from_dir.py <catalog.json> \
  --images-root <图片根目录> \
  [--dry-run | --no-dry-run] \
  [--overwrite]
```

**参数说明**：
- `catalog.json`：catalog 配置文件路径
- `--images-root`：本地图片根目录路径（必需）
- `--dry-run`（默认）：预览变更但不写入文件
- `--no-dry-run`：实际写入变更，自动备份原文件
- `--overwrite`：覆盖已有的 images 字段（默认保留已有）

**示例**：

**第 1 步：干运行预览**
```bash
python scripts/inject_images_from_dir.py demo/catalog_2930.json \
  --images-root data/images/2930 --dry-run
```

预览输出：
```
📂 扫描图片目录: data/images/2930
🔄 目录模式: vol_id/chap_id/* 或 chap_id/*
  ✓ 注入 2 张图片 → vol_001/118227 (序章 孤傲的公主大人与怠惰的邻人)
  ✓ 注入 1 张图片 → vol_001/118228 (第1话 错过免费转蛋会非常不甘心吧？)
  ...

📊 统计:
  ✓ 已注入图片: 12 个章节
  ⊘ 已跳过（已有图片）: 3 个章节
  📝 元数据更新: meta.base_image_path = data/images/2930/

💾 干运行模式: 变更未保存
   运行以下命令保存更改:
   python scripts/inject_images_from_dir.py demo/catalog_2930.json \
     --images-root data/images/2930 --no-dry-run
```

**第 2 步：执行注入**
```bash
python scripts/inject_images_from_dir.py demo/catalog_2930.json \
  --images-root data/images/2930 --no-dry-run
```

执行结果：
```
✓ 配置已更新: demo/catalog_2930.json
💾 已备份原文件: demo/catalog_2930.json.bak
```

## 目录结构要求

脚本假设图片目录按以下结构组织：

```
data/images/2930/
├── vol_001/
│   ├── 118227/              # chapter_id（对应 chapters[].id）
│   │   ├── 001.jpg
│   │   └── 002.jpg
│   └── 118228/
│       └── 003.jpg
├── vol_002/
│   └── 122878/
│       └── 004.jpg
└── vol_003/
    └── 127630/
        └── 005.jpg
```

其中：
- `vol_001`, `vol_002` 等为卷 ID（对应 `volumes[].volume_id` 或 `volumes[].title`）
- `118227`, `118228` 等为章节 ID（对应 `chapters[].id` 或 `chapters[].main_file` 的文件名 stem）

## 工作流程建议

### 场景 1：初始化配置中的图片

1. **准备图片目录**：
   ```bash
   mkdir -p data/images/2930/vol_001/118227
   cp /path/to/images/*.jpg data/images/2930/vol_001/118227/
   ```

2. **检查现状**：
   ```bash
   python scripts/check_catalog_images.py demo/catalog_2930.json
   ```

3. **干运行预览**：
   ```bash
   python scripts/inject_images_from_dir.py demo/catalog_2930.json \
     --images-root data/images/2930 --dry-run
   ```

4. **确认无误后执行注入**：
   ```bash
   python scripts/inject_images_from_dir.py demo/catalog_2930.json \
     --images-root data/images/2930 --no-dry-run
   ```

5. **生成 HTML**：
   ```bash
   python -m parallel_text_viewer --index demo/catalog_2930.json -d output/
   ```

### 场景 2：更新现有配置中的图片

1. **添加新图片到本地目录**
2. **运行注入脚本（带 --overwrite）**：
   ```bash
   python scripts/inject_images_from_dir.py demo/catalog_2930.json \
     --images-root data/images/2930 --overwrite --no-dry-run
   ```

### 场景 3：CI/CD 自动流程

在 GitHub Actions 或其他 CI 中添加：

```yaml
- name: Check catalog images
  run: python scripts/check_catalog_images.py demo/catalog_2930.json

- name: Inject images
  run: |
    python scripts/inject_images_from_dir.py demo/catalog_2930.json \
      --images-root data/images/2930 --no-dry-run || true

- name: Generate HTML
  run: python -m parallel_text_viewer --index demo/catalog_2930.json -d output/
```

## 常见问题

**Q: 脚本找不到图片怎么办？**

A: 检查以下几点：
1. 图片根目录是否正确：`--images-root data/images/2930`
2. 卷 ID 是否与 catalog 中的 `volumes[].volume_id` 或 `title` 匹配
3. 章节 ID 是否与 catalog 中的 `chapters[].id` 或文件名匹配
4. 文件扩展名是否为支持格式（.jpg, .jpeg, .png, .webp, .gif, .bmp）

**Q: 如何覆盖已有的图片配置？**

A: 使用 `--overwrite` 选项：
```bash
python scripts/inject_images_from_dir.py demo/catalog_2930.json \
  --images-root data/images/2930 --overwrite --no-dry-run
```

**Q: 如何恢复备份的配置？**

A: 脚本在执行 `--no-dry-run` 时会自动备份原文件：
```bash
cp demo/catalog_2930.json.bak demo/catalog_2930.json
```

## 相关文档

- [README.md - 图片路径管理小节](../README.md#图片路径管理检查与注入)
- [docs/IMAGE_MANAGEMENT_PLAN.md - 详细的图片管理方案](../docs/IMAGE_MANAGEMENT_PLAN.md)
