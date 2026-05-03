"""
HTML 生成器

合并自: single_file.py, book_index.py, factory.py
"""

import html as html_module
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional

from .core import parse_lines, parse_md_lines, validate_line_counts
from .renderer import TemplateRenderer
from .utils import ensure_dir, compute_relative_image_path, resolve_image_path

# ═══════════════════════════════════════════════════════════
# GeneratorFactory
# ═══════════════════════════════════════════════════════════


class GeneratorFactory:
    """生成器工厂类"""

    def create_single_file_generator(
        self,
        main_file: Path,
        side_file: Path,
        title: str = "Bilingual Viewer",
        primary: str = "a",
        orientation: str = "vertical",
        sync: bool = False,
        ignore_empty: bool = True,
    ) -> "SingleFileGenerator":
        """创建单文件生成器"""
        return SingleFileGenerator(
            main_file=main_file,
            side_file=side_file,
            title=title,
            primary=primary,
            orientation=orientation,
            sync=sync,
            ignore_empty=ignore_empty,
        )

    def create_book_index_generator(self, config_file: Path) -> "BookIndexGenerator":
        """创建书目索引生成器"""
        return BookIndexGenerator(config_file)


# ═══════════════════════════════════════════════════════════
# SingleFileGenerator
# ═══════════════════════════════════════════════════════════


class SingleFileGenerator:
    """单文件HTML生成器"""

    def __init__(
        self,
        main_file: Path,
        side_file: Path,
        title: str = "Bilingual Viewer",
        primary: str = "a",
        orientation: str = "vertical",
        sync: bool = False,
        ignore_empty: bool = True,
    ):
        """
        初始化单文件生成器。

        Args:
            main_file: 主文档文件路径
            side_file: 从文档文件路径
            title: HTML页面标题
            primary: 默认主文档 ('a' 或 'b')
            orientation: 页面布局方向
            sync: 是否启动时显示同步模式
            ignore_empty: 是否忽略空白行
        """
        self.main_file = main_file
        self.side_file = side_file
        self.title = title
        self.primary = primary
        self.orientation = orientation
        self.sync = sync
        self.ignore_empty = ignore_empty
        self.renderer = TemplateRenderer()

        # 验证文件存在
        if not main_file.exists():
            raise FileNotFoundError(f"Main file not found: {main_file}")
        if not side_file.exists():
            raise FileNotFoundError(f"Side file not found: {side_file}")

    def generate(self, output_path: Path) -> None:
        """
        生成单个HTML文件。

        Args:
            output_path: 输出文件路径
        """
        # 读取和解析文本
        main_lines = parse_lines(self.main_file, ignore_empty=self.ignore_empty)
        side_lines = parse_lines(self.side_file, ignore_empty=self.ignore_empty)

        # 提取文件标题
        main_title = self._get_title(self.main_file, main_lines)
        side_title = self._get_title(self.side_file, side_lines)

        # 移除第一行（标题），从第二行开始作为正文
        main_lines = main_lines[1:] if len(main_lines) > 1 else []
        side_lines = side_lines[1:] if len(side_lines) > 1 else []

        # 验证和对齐行数
        main_lines, side_lines = validate_line_counts(
            main_lines, side_lines, str(self.main_file), str(self.side_file)
        )

        # 生成行对
        pairs = [
            [
                html_module.escape(a, quote=False),
                html_module.escape(b, quote=False),
            ]
            for a, b in zip(main_lines, side_lines)
        ]

        # 生成文档ID（用于本地存储隔离）
        pairs_json = json.dumps(pairs, ensure_ascii=False)
        doc_id = hashlib.sha1(pairs_json.encode("utf-8")).hexdigest()[:10]

        # 生成标题JSON
        titles_json = json.dumps({"a": main_title, "b": side_title}, ensure_ascii=False)

        from .renderer import get_state_manager_code

        state_manager_code = get_state_manager_code(doc_id)

        # 渲染模板
        import os

        if os.environ.get("PTV_DEBUG_COUNTS") == "1":
            print(
                f"DEBUG COUNTS (single_file): main={len(main_lines)} side={len(side_lines)} pairs={len(pairs)}"
            )

        html_content = self.renderer.render_single_file(
            title=self.title,
            count=len(pairs),
            pairs_json=pairs_json,
            titles_json=titles_json,
            state_manager_code=state_manager_code,
            orientation=self.orientation,
        )

        # 写入输出文件
        output_path.write_text(html_content, encoding="utf-8")

    def _get_title(self, file_path: Path, lines: list[str]) -> str:
        """从文件内容或路径提取标题"""
        if lines and file_path.suffix.lower() == ".md" and lines[0].strip().startswith("#"):
            title_line = lines[0].strip()
            return title_line.lstrip("#").strip()
        else:
            return file_path.stem


# ═══════════════════════════════════════════════════════════
# BookIndexGenerator
# ═══════════════════════════════════════════════════════════


class BookIndexGenerator:
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

        # 获取工作目录（用于解析相对路径）
        meta = self.config.get("meta", {})
        working_dir_str = meta.get("working_dir", ".")
        self.working_dir = Path(working_dir_str)
        if not self.working_dir.is_absolute():
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
                    chapter_path = self._get_chapter_output_path(work, volume, chapter)
                    full_chapter_path = output_dir / chapter_path
                    ensure_dir(full_chapter_path.parent)

                    nav_info = self._build_nav_info(work, volume, chapter, chapter_paths)
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
        """读取 catalog 文件以获取真实的作品标题"""
        try:
            book_id = self.config.get("meta", {}).get("book_id")
            if not book_id:
                return {}
            data_root = self.working_dir.parent.parent
            catalog_file = data_root / "catalogs" / f"{book_id}.json"
            if not catalog_file.exists():
                return {}
            with open(catalog_file, "r", encoding="utf-8") as f:
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
                    chapter_path = self._get_chapter_output_path(work, volume, chapter)
                    chapter_paths[chapter_key] = chapter_path
        return chapter_paths

    def _get_chapter_output_path(self, work: Dict, volume: Dict, chapter: Dict) -> Path:
        """根据配置生成章节的输出路径"""
        work_title = work["title"]
        volume_title = volume["title"]
        volume_id = volume.get("id", "vol_001")
        chapter_title = chapter["title"]
        safe_chapter_title = "".join(
            c for c in chapter_title if c.isalnum() or c in (" ", "-", "_")
        ).rstrip()

        if self.output_structure == "flat":
            return Path(f"{safe_chapter_title}.html")
        elif self.output_structure == "by_work":
            safe_work = self._safe_filename(work_title)
            return Path("works") / safe_work / f"vol_{volume_id}" / f"{safe_chapter_title}.html"
        elif self.output_structure == "by_volume":
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
            c
            for c in name
            if c.isalnum()
            or c in (" ", "-", "_", "的", "第", "卷", "章", "话", "序", "终", "后", "插")
        ).rstrip()

    @staticmethod
    def _generate_nav_html(nav_info: Dict) -> str:
        """生成导航HTML"""
        return f"""
        <!-- Breadcrumb navigation -->
        <div class="breadcrumb">
            <a href="{nav_info['index_url']}">Index</a> &gt;
            <span>{nav_info['work_title']}</span> &gt;
            <span>{nav_info['volume_title']}</span> &gt;
            <span>{nav_info['chapter_title']}</span>
        </div>
        """

    def _build_nav_info(self, work: Dict, volume: Dict, chapter: Dict, chapter_paths: Dict) -> Dict:
        """构建章节导航信息"""
        work_title = work["title"]
        volume_title = volume["title"]
        chapter_title = chapter["title"]

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
            "index_url": "../index.html",
        }
        nav_info["prev_chapter_url"] = "#"
        nav_info["next_chapter_url"] = "#"
        nav_info["prev_volume_url"] = "#"
        nav_info["next_volume_url"] = "#"

        # Find prev/next chapter
        if work_idx is not None:
            all_volumes = self.config.get("works", [])[work_idx].get("volumes", [])
            flat_chapters = []
            for v_idx, v in enumerate(all_volumes):
                for c_idx, c in enumerate(v.get("chapters", [])):
                    flat_chapters.append((v_idx, c_idx, c["title"]))

            for i, (v_idx, c_idx, title) in enumerate(flat_chapters):
                if title == chapter_title:
                    if i > 0:
                        prev_v, prev_c, _ = flat_chapters[i - 1]
                        prev_key = (
                            work_title,
                            all_volumes[prev_v]["title"],
                            all_volumes[prev_v]["chapters"][prev_c]["title"],
                        )
                        if prev_key in chapter_paths:
                            nav_info["prev_chapter_url"] = str(chapter_paths[prev_key])
                    if i < len(flat_chapters) - 1:
                        next_v, next_c, _ = flat_chapters[i + 1]
                        next_key = (
                            work_title,
                            all_volumes[next_v]["title"],
                            all_volumes[next_v]["chapters"][next_c]["title"],
                        )
                        if next_key in chapter_paths:
                            nav_info["next_chapter_url"] = str(chapter_paths[next_key])
                    break

        # Find prev/next volume
        if volume_idx is not None:
            all_volumes = self.config.get("works", [])[work_idx].get("volumes", [])
            for v_idx, v in enumerate(all_volumes):
                if v["title"] == volume_title:
                    if v_idx > 0:
                        prev_vol = all_volumes[v_idx - 1]
                        if prev_vol.get("chapters"):
                            last_ch = prev_vol["chapters"][-1]
                            key = (work_title, prev_vol["title"], last_ch["title"])
                            if key in chapter_paths:
                                nav_info["prev_volume_url"] = str(chapter_paths[key])
                    if v_idx < len(all_volumes) - 1:
                        next_vol = all_volumes[v_idx + 1]
                        if next_vol.get("chapters"):
                            first_ch = next_vol["chapters"][0]
                            key = (work_title, next_vol["title"], first_ch["title"])
                            if key in chapter_paths:
                                nav_info["next_volume_url"] = str(chapter_paths[key])
                    break

        return nav_info

    def _generate_chapter_html(
        self, chapter: Dict, nav_info: Dict, output_path: Path, output_dir: Path
    ) -> None:
        """生成章节 HTML"""
        # 解析文件路径
        main_file = chapter.get("main_file")
        side_file = chapter.get("side_file")

        if not main_file:
            return

        main_path = self.working_dir / main_file
        side_path = self.working_dir / side_file if side_file else None

        if not main_path.exists():
            return

        # 读取和解析文本
        title, main_lines = parse_md_lines(main_path, ignore_empty=True, base_path=self.working_dir)

        if side_path and side_path.exists():
            _, side_lines = parse_md_lines(side_path, ignore_empty=True, base_path=self.working_dir)
        else:
            side_lines = []

        # 验证和对齐行数
        main_lines, side_lines = validate_line_counts(
            main_lines, side_lines, str(main_path), str(side_path)
        )

        # 替换图片占位符
        from .renderer import get_state_manager_code

        # 生成行对
        pairs = [
            [html_module.escape(a, quote=False), html_module.escape(b, quote=False)]
            for a, b in zip(main_lines, side_lines)
        ]

        pairs_json = json.dumps(pairs, ensure_ascii=False)
        doc_id = hashlib.sha1(pairs_json.encode("utf-8")).hexdigest()[:10]
        titles_json = json.dumps({"a": title or main_file.stem, "b": ""}, ensure_ascii=False)
        state_manager_code = get_state_manager_code(doc_id)

        # 修正导航URL - 使相对路径正确
        for key in ["prev_chapter_url", "next_chapter_url", "prev_volume_url", "next_volume_url"]:
            url = nav_info.get(key, "#")
            if url != "#" and not url.startswith("http"):
                try:
                    target_path = (output_dir / url).resolve()
                    rel_path = target_path.relative_to(output_path.parent)
                    nav_info[key] = rel_path.as_posix()
                except Exception:
                    import os

                    nav_info[key] = os.path.relpath(
                        str(output_dir / url), start=str(output_path.parent)
                    ).replace("\\", "/")

        nav_html = self._generate_nav_html(nav_info)

        import os as os_mod

        if os_mod.environ.get("PTV_DEBUG_COUNTS") == "1":
            print(
                f"DEBUG COUNTS (book_index): main={len(main_lines)} side={len(side_lines)} pairs={len(pairs)} file={str(main_file)}"
            )

        chapter_title = chapter.get("title", title or main_file.stem)
        html_content = self.renderer.render_chapter(
            title=chapter_title,
            count=len(pairs),
            pairs_json=pairs_json,
            titles_json=titles_json,
            state_manager_code=state_manager_code,
            orientation="vertical",
            nav_html=nav_html,
            nav_info=nav_info,
        )

        output_path.write_text(html_content, encoding="utf-8")

    def _generate_index_html(self, output_dir: Path) -> None:
        """生成索引 HTML"""
        index_data = []

        for work in self.config.get("works", []):
            work_info = {
                "title": work.get("title", "Unknown"),
                "volumes": {},
            }

            for volume in work.get("volumes", []):
                vol_id = volume.get("id", "vol_001")
                vol_info = {
                    "title": volume.get("title", vol_id),
                    "chapters": [],
                }

                for chapter in volume.get("chapters", []):
                    chapter_path = self._get_chapter_output_path(work, volume, chapter)
                    ch_info = {
                        "title": chapter.get("title", "Unknown"),
                        "url": str(chapter_path),
                        "disabled": chapter.get("disabled", False),
                    }
                    vol_info["chapters"].append(ch_info)

                work_info["volumes"][vol_id] = vol_info

            index_data.append(work_info)

        html_content = self.renderer.render_index(index_data)
        index_path = output_dir / "index.html"
        index_path.write_text(html_content, encoding="utf-8")
