"""
书目索引生成器

负责从配置文件生成批量书目对照HTML文件。
"""

import html
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any

from .base import Generator
from .navigation import NavigationGenerator
from ..core.text_processor import parse_lines, parse_md_lines, validate_line_counts
from ..templates.renderer import TemplateRenderer
from ..templates.state_manager import get_state_manager_code
from ..utils.file_utils import ensure_dir
from ..utils.image_utils import compute_relative_image_path, resolve_image_path


class BookIndexGenerator(Generator):
    """书目索引生成器"""

    def __init__(self, config_file: Path):
        """
        初始化书目索引生成器。

        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.config = self._load_config()
        self.renderer = TemplateRenderer()
        self.navigation_generator = NavigationGenerator()

        # 获取工作目录（用于解析相对路径）
        meta = self.config.get("meta", {})
        working_dir_str = meta.get("working_dir", ".")
        self.working_dir = Path(working_dir_str)
        if not self.working_dir.is_absolute():
            # 如果工作目录是相对路径，相对于配置文件的父目录
            self.working_dir = self.config_file.parent / self.working_dir
        self.working_dir = self.working_dir.resolve()

        # 获取输出结构配置
        self.output_structure = self.config.get("output_structure", "flat")
        self.structure_config = self.config.get("structure_config", {})
        
        # 读取 catalog 以获取实际的作品标题（如果存在）
        self.catalog_data = self._load_catalog()

    def generate(self, output_dir: Path) -> None:
        """
        生成书目索引和多个对照HTML文件。

        Args:
            output_dir: 输出目录
        """
        output_dir = Path(output_dir)
        ensure_dir(output_dir)

        # 收集所有章节的路径映射
        chapter_paths = self._collect_chapter_paths(output_dir)

        # 生成所有章节的HTML
        for work in self.config.get("works", []):
            for volume in work.get("volumes", []):
                for chapter in volume.get("chapters", []):
                    # 生成章节输出路径 - 传入完整的 volume 对象以获取卷ID
                    chapter_path = self._get_chapter_output_path(
                        work, volume, chapter
                    )
                    full_chapter_path = output_dir / chapter_path

                    # 确保父目录存在
                    ensure_dir(full_chapter_path.parent)

                    # 生成章节HTML
                    nav_info = self._build_nav_info(
                        work, volume, chapter, chapter_paths
                    )
                    # 传入 output_dir 以便在生成导航时计算到顶层 index.html 的相对路径
                    self._generate_chapter_html(chapter, nav_info, full_chapter_path, output_dir)

        # 生成索引HTML
        self._generate_index_html(output_dir)

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not self.config_file.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_file}")

        with open(self.config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def _load_catalog(self) -> Dict[str, Any]:
        """
        读取 catalog 文件以获取真实的作品标题
        
        Catalog 通常位于: data/catalogs/{book_id}.json
        """
        try:
            book_id = self.config.get("meta", {}).get("book_id")
            if not book_id:
                return {}
            
            # 从工作目录向上找到 data 目录
            # working_dir 通常是 data/chapters/{book_id}
            data_root = self.working_dir.parent.parent
            
            catalog_file = data_root / "catalogs" / f"{book_id}.json"
            if not catalog_file.exists():
                return {}
            
            with open(catalog_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def _collect_chapter_paths(self, output_dir: Path) -> Dict[tuple, Path]:
        """收集所有章节的路径映射"""
        chapter_paths = {}
        for work in self.config.get("works", []):
            for volume in work.get("volumes", []):
                for chapter in volume.get("chapters", []):
                    chapter_key = (work["title"], volume["title"], chapter["title"])
                    chapter_path = self._get_chapter_output_path(
                        work, volume, chapter
                    )
                    chapter_paths[chapter_key] = chapter_path
        return chapter_paths

    def _get_chapter_output_path(self, work: Dict, volume: Dict, chapter: Dict) -> Path:
        """根据配置生成章节的输出路径"""
        work_title = work["title"]
        volume_title = volume["title"]
        volume_id = volume.get("id", "vol_001")
        chapter_title = chapter["title"]
        
        # 生成安全的文件名
        safe_chapter_title = "".join(
            c for c in chapter_title if c.isalnum() or c in (" ", "-", "_")
        ).rstrip()

        if self.output_structure == "flat":
            return Path(f"{safe_chapter_title}.html")
        elif self.output_structure == "by_work":
            safe_work = self._safe_filename(work_title)
            # 使用卷ID而不是卷标题
            return Path("works") / safe_work / f"vol_{volume_id}" / f"{safe_chapter_title}.html"
        elif self.output_structure == "by_volume":
            # 使用卷ID而不是卷标题
            return Path("volumes") / f"vol_{volume_id}" / f"{safe_chapter_title}.html"
        elif self.output_structure == "custom":
            template = self.structure_config.get("path_template", "{work}/{volume}/{chapter}.html")
            path_str = template.format(
                work=self._safe_filename(work_title),
                volume=f"vol_{volume_id}",
                chapter=safe_chapter_title,
            )
            return Path(path_str)
        else:
            return Path(f"{safe_chapter_title}.html")

    def _safe_filename(self, name: str) -> str:
        """生成安全的文件名"""
        return "".join(
            c for c in name
            if c.isalnum() or c in (" ", "-", "_", "的", "第", "卷", "章", "话", "序", "终", "后", "插")
        ).rstrip()

    def _build_nav_info(self, work: Dict, volume: Dict, chapter: Dict, chapter_paths: Dict) -> Dict:
        """构建章节导航信息"""
        work_title = work["title"]
        volume_title = volume["title"]
        chapter_title = chapter["title"]

        # 找到当前位置
        work_idx = None
        volume_idx = None
        chapter_idx = None
        for w_idx, w in enumerate(self.config.get("works", [])):
            if w["title"] == work_title:
                work_idx = w_idx
                for v_idx, v in enumerate(w.get("volumes", [])):
                    if v["title"] == volume_title:
                        volume_idx = v_idx
                        for c_idx, c in enumerate(v.get("chapters", [])):
                            if c["title"] == chapter_title:
                                chapter_idx = c_idx
                                break
                        break
                break

        nav_info = {
            "work_title": work_title,
            "volume_title": volume_title,
            "chapter_title": chapter_title,
            "index_url": "../index.html",  # 默认
            "prev_chapter_url": "#",
            "next_chapter_url": "#",
            "prev_volume_url": "#",
            "next_volume_url": "#",
        }

        if work_idx is not None and volume_idx is not None and chapter_idx is not None:
            works = self.config.get("works", [])
            volumes = works[work_idx].get("volumes", [])
            chapters = volumes[volume_idx].get("chapters", [])

            # Prev chapter
            if chapter_idx > 0:
                prev_chapter = chapters[chapter_idx - 1]
                prev_path = chapter_paths[(work_title, volume_title, prev_chapter["title"])]
                nav_info["prev_chapter_url"] = prev_path.as_posix()
            elif volume_idx > 0:
                prev_volume = volumes[volume_idx - 1]
                prev_chapters = prev_volume.get("chapters", [])
                if prev_chapters:
                    prev_chapter = prev_chapters[-1]
                    prev_path = chapter_paths[(work_title, prev_volume["title"], prev_chapter["title"])]
                    nav_info["prev_chapter_url"] = prev_path.as_posix()

            # Next chapter
            if chapter_idx < len(chapters) - 1:
                next_chapter = chapters[chapter_idx + 1]
                next_path = chapter_paths[(work_title, volume_title, next_chapter["title"])]
                nav_info["next_chapter_url"] = next_path.as_posix()
            elif volume_idx < len(volumes) - 1:
                next_volume = volumes[volume_idx + 1]
                next_chapters = next_volume.get("chapters", [])
                if next_chapters:
                    next_chapter = next_chapters[0]
                    next_path = chapter_paths[(work_title, next_volume["title"], next_chapter["title"])]
                    nav_info["next_chapter_url"] = next_path.as_posix()

            # Prev volume
            if volume_idx > 0:
                prev_volume = volumes[volume_idx - 1]
                prev_chapters = prev_volume.get("chapters", [])
                if prev_chapters:
                    prev_chapter = prev_chapters[0]
                    prev_path = chapter_paths[(work_title, prev_volume["title"], prev_chapter["title"])]
                    nav_info["prev_volume_url"] = prev_path.as_posix()

            # Next volume
            if volume_idx < len(volumes) - 1:
                next_volume = volumes[volume_idx + 1]
                next_chapters = next_volume.get("chapters", [])
                if next_chapters:
                    next_chapter = next_chapters[0]
                    next_path = chapter_paths[(work_title, next_volume["title"], next_chapter["title"])]
                    nav_info["next_volume_url"] = next_path.as_posix()

        return nav_info

    def _generate_chapter_html(self, chapter: Dict, nav_info: Dict, output_path: Path, output_dir: Path) -> None:
        """生成单个章节的HTML文件"""
        main_file = Path(chapter["main_file"])
        side_file_path = chapter.get("side_file")
        title = chapter["title"]

        # 处理相对路径 - 相对于工作目录，而不是配置文件目录
        if not main_file.is_absolute():
            main_file = self.working_dir / main_file

        # 读取和解析文本 - 使用 parse_md_lines 来处理 markdown 图片
        title_from_file, main_lines = parse_md_lines(
            main_file,
            ignore_empty=chapter.get("ignore_empty", True),
            base_path=self.working_dir
        )
        
        # 使用文件中的标题如果没有额外的标题
        if not title and title_from_file:
            title = title_from_file

        if side_file_path:
            side_file = Path(side_file_path)
            if not side_file.is_absolute():
                side_file = self.working_dir / side_file
            _, side_lines = parse_md_lines(
                side_file,
                ignore_empty=chapter.get("ignore_empty", True),
                base_path=self.working_dir
            )
        else:
            side_lines = [""] * len(main_lines)

        # 验证和对齐行数，传入文件路径以便调试输出不一致时的文件名
        side_identifier = str(side_file) if 'side_file' in locals() and side_file is not None else '<no-side>'
        main_lines, side_lines = validate_line_counts(main_lines, side_lines, str(main_file), side_identifier)

        # 处理图片路径（如果配置中包含 images）
        base_image_path = self.config.get("meta", {}).get("base_image_path")
        if chapter.get("images") and base_image_path:
            # 将图片路径转换为相对于输出 HTML 的相对路径
            for img_info in chapter.get("images", []):
                filename = img_info.get("filename")
                if filename and not filename.startswith(("http://", "https://")):
                    try:
                        img_abs_path = resolve_image_path(
                            self.working_dir,
                            filename,
                            base_image_path
                        )
                        if isinstance(img_abs_path, Path):
                            rel_img_path = compute_relative_image_path(output_path, img_abs_path)
                            img_info["filename"] = rel_img_path
                    except Exception as e:
                        # 如果转换失败，保留原始路径并输出警告
                        print(f"⚠️  警告：无法转换图片路径 {filename}: {e}")

        # 生成行对
        pairs = [[a, b] for a, b in zip(main_lines, side_lines)]
        
        # 调整图像路径：从项目相对路径转换为输出HTML相对路径
        # 图像可能仍然使用 `images/2930/...` 或 `images\2930\...` 的形式，需要转换为相对于输出HTML的路径
        import re
        def adjust_image_paths_in_pairs(pairs_list, html_output_path, chapter_config):
            r"""
            调整 pairs 中的图像路径。
            从 `images/...` 或 `images\...` 转换为相对于 html_output_path 的相对路径。
            对于纯文件名，尝试从章节配置的images中匹配对应的完整路径。
            例如: images/2930/vol_001/file.jpg -> ../../images/2930/vol_001/file.jpg
                  images\2930\vol_001\file.jpg -> ../../images/2930/vol_001/file.jpg
                  118359_1_159954.jpg -> ../../images/2930/vol_001/118359_1_159954.jpg (如果配置中有匹配)
            """
            # 构建文件名到完整路径的映射
            image_mapping = {}
            if chapter_config.get("images", {}).get("files"):
                for img_info in chapter_config["images"]["files"]:
                    filename = img_info.get("filename", "")
                    if filename:
                        # 提取文件名部分（不含路径）
                        img_basename = Path(filename).name
                        image_mapping[img_basename] = filename.replace('\\', '/')
            
            adjusted_pairs = []
            for pair in pairs_list:
                adjusted_pair = []
                for text in pair:
                    # 查找 <img src="..." 的所有实例，并替换 src 中的图像路径
                    def fix_img_src(match):
                        src = match.group(1)
                        # 规范化路径分隔符（将 \\ 转换为 /）
                        src_normalized = src.replace('\\', '/')

                        # 优先匹配包含 'images/' 的路径片段
                        idx = src_normalized.find('images/')
                        if idx != -1:
                            tail = src_normalized[idx:]
                            adjusted_src = '../../' + tail
                            return f'<img src="{adjusted_src}"'

                        # 否则只取文件名（basename），忽略原始路径
                        from pathlib import Path as _P
                        basename = _P(src_normalized).name

                        # 使用映射（basename -> 原始配置路径）优先解析
                        if basename in image_mapping:
                            full_path = image_mapping[basename]
                            adjusted_src = '../../' + full_path.replace('\\', '/')
                            return f'<img src="{adjusted_src}"'

                        # 最后回退到假设路径 images/2930/<volume>/<basename>
                        volume_dir = html_output_path.parent.name
                        adjusted_src = f'../../images/2930/{volume_dir}/{basename}'
                        return f'<img src="{adjusted_src}"'
                    
                    text = re.sub(r'<img\s+src="([^"]+)"', fix_img_src, text)
                    adjusted_pair.append(text)
                adjusted_pairs.append(adjusted_pair)
            return adjusted_pairs
        
        pairs = adjust_image_paths_in_pairs(pairs, output_path, chapter)

        # 生成文档ID
        pairs_json = json.dumps(pairs, ensure_ascii=False)
        doc_id = hashlib.sha1(pairs_json.encode("utf-8")).hexdigest()[:10]

        # 生成标题JSON
        titles_json = json.dumps({"a": "中文", "b": "English"}, ensure_ascii=False)

        # 获取状态管理器代码
        state_manager_code = get_state_manager_code(doc_id)

        # 生成导航HTML
        # 计算到顶层 index.html 的相对路径（用于 breadcrumb 返回）
        try:
            index_path = output_dir / "index.html"
            rel_index = index_path.relative_to(output_path.parent)
            index_url = rel_index.as_posix()
        except Exception:
            # fallback to a safe relative path using os.path.relpath
            import os
            index_url = os.path.relpath(str(output_dir / "index.html"), start=str(output_path.parent)).replace('\\', '/')
        nav_info['index_url'] = index_url

        # 计算其他导航URL的相对路径
        for key in ['prev_chapter_url', 'next_chapter_url', 'prev_volume_url', 'next_volume_url']:
            url = nav_info.get(key, '#')
            if url != '#' and not url.startswith('http'):
                # 如果是相对路径，计算相对于当前章节的相对路径
                try:
                    target_path = (output_dir / url).resolve()
                    rel_path = target_path.relative_to(output_path.parent)
                    nav_info[key] = rel_path.as_posix()
                except Exception:
                    # fallback
                    import os
                    nav_info[key] = os.path.relpath(str(output_dir / url), start=str(output_path.parent)).replace('\\', '/')

        nav_html = self.navigation_generator.generate_navigation(nav_info)

        import os
        if os.environ.get('PTV_DEBUG_COUNTS') == '1':
            print(f"DEBUG COUNTS (book_index): main={len(main_lines)} side={len(side_lines)} pairs={len(pairs)} file={str(main_file)}")

        # 渲染模板
        html_content = self.renderer.render_chapter(
            title=title,
            count=len(pairs),
            pairs_json=pairs_json,
            titles_json=titles_json,
            state_manager_code=state_manager_code,
            orientation=chapter.get("orientation", "vertical"),
            nav_html=nav_html,
            nav_info=nav_info,
        )

        # 写入文件
        output_path.write_text(html_content, encoding="utf-8")

    def _generate_index_html(self, output_dir: Path) -> None:
        """生成索引HTML文件"""
        index_data = []
        
        # 尝试从 catalog 获取真实作品标题
        catalog = self.catalog_data
        
        for work in self.config.get("works", []):
            # 优先使用 catalog 中的标题，否则使用配置中的标题
            work_title = catalog.get("title", work["title"]) if catalog else work["title"]
            work_data = {"title": work_title, "volumes": []}
            
            for volume in work.get("volumes", []):
                volume_data = {"title": volume["title"], "chapters": []}
                for chapter in volume.get("chapters", []):
                    # 计算相对URL - 传递完整对象
                    chapter_path = self._get_chapter_output_path(work, volume, chapter)
                    # 使用 POSIX 风格路径作为 HTML 中的相对 URL（使用 '/'，避免 Windows '\\'）
                    relative_url = chapter_path.as_posix()
                    chapter_data = {
                        "title": chapter["title"],
                        "url": relative_url,
                        "disabled": chapter.get("disabled", False),
                    }
                    volume_data["chapters"].append(chapter_data)
                work_data["volumes"].append(volume_data)
            index_data.append(work_data)

        # 渲染索引模板
        html_content = self.renderer.render_index(index_data)
        index_file = output_dir / "index.html"
        index_file.write_text(html_content, encoding="utf-8")
        print(f"Generated index at {index_file}")