"""
核心模块：数据模型、配置、文本处理、路径解析、构建 API、配置生成器

合并自: core/*.py, config/generator.py
"""

import json
import csv
import re
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any, Callable
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# 数据模型 (config_v2.py)
# ═══════════════════════════════════════════════════════════════


@dataclass
class ImageReference:
    """图片信息"""

    filename: str
    title: Optional[str] = None
    position: str = "inline"
    line: Optional[int] = None
    original_url: Optional[str] = None


@dataclass
class ChapterImages:
    """章节的图片配置"""

    override_mode: str = "none"
    files: List[ImageReference] = field(default_factory=list)


@dataclass
class ChapterFiles:
    """章节文件配置"""

    main: Optional[str] = None
    side: Optional[str] = None


@dataclass
class Chapter:
    """章节"""

    id: str
    title: str
    main_file: Optional[str] = None
    side_file: Optional[str] = None
    files: Optional[ChapterFiles] = None
    disabled: bool = False
    ignore_empty: bool = True
    orientation: str = "vertical"
    images: ChapterImages = field(default_factory=ChapterImages)

    def should_auto_derive_files(self) -> bool:
        return (
            self.main_file is None
            and self.side_file is None
            and (self.files is None or (self.files.main is None and self.files.side is None))
        )


@dataclass
class Volume:
    """卷"""

    id: str
    title: str
    directory: Optional[str] = None
    chapters: List[Chapter] = field(default_factory=list)


@dataclass
class Work:
    """作品"""

    id: Optional[str] = None
    title: str = ""
    volumes: List[Volume] = field(default_factory=list)


@dataclass
class ImageAssociationParams:
    """图片关联参数"""

    chapter_id_field: str = "id"
    filename_pattern: Optional[str] = None
    mappings: Dict[str, str] = field(default_factory=dict)


@dataclass
class ImageReferenceConfig:
    """图片引用配置"""

    placeholder_pattern: str = "{IMG:.*}"
    placeholder_format: str = "{IMG:{chapter_id}_{index:03d}}"


@dataclass
class ImageConfig:
    """图片配置"""

    enabled: bool = True
    base_path: str = "images"
    association_strategy: str = "directory"
    association_params: ImageAssociationParams = field(default_factory=ImageAssociationParams)
    reference_style: str = "placeholder"
    reference_config: ImageReferenceConfig = field(default_factory=ImageReferenceConfig)


@dataclass
class StructureConfig:
    """文件结构配置"""

    type: str = "standard"
    volume_pattern: str = "vol_{:03d}"
    volume_title_source: str = "auto"
    chapter_id_field: str = "id"
    chapter_title_source: str = "title"
    languages: Dict[str, str] = field(default_factory=lambda: {"main": "cn", "side": "en"})


@dataclass
class MetaConfig:
    """元数据配置"""

    book_id: str
    title: str = ""
    authors: List[str] = field(default_factory=list)
    description: Optional[str] = None
    working_dir: str = "."
    images: ImageConfig = field(default_factory=ImageConfig)
    structure: StructureConfig = field(default_factory=StructureConfig)


@dataclass
class ConfigV2:
    """Config v2.0 完整结构"""

    schema: str = "https://parallel-text-viewer.io/schema/config-2.0.json"
    version: str = "2.0"
    meta: MetaConfig = field(default_factory=lambda: MetaConfig(book_id=""))
    works: List[Work] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ConfigV2":
        meta_data = data.get("meta", {})
        meta = MetaConfig(
            book_id=meta_data.get("book_id", ""),
            title=meta_data.get("title", ""),
            authors=meta_data.get("authors", []),
            description=meta_data.get("description"),
            working_dir=meta_data.get("working_dir", "."),
        )

        works = []
        for work_data in data.get("works", []):
            volumes = []
            for vol_data in work_data.get("volumes", []):
                chapters = [
                    Chapter(
                        id=ch_data.get("id", ""),
                        title=ch_data.get("title", ""),
                        main_file=ch_data.get("main_file"),
                        side_file=ch_data.get("side_file"),
                        disabled=ch_data.get("disabled", False),
                    )
                    for ch_data in vol_data.get("chapters", [])
                ]
                volumes.append(
                    Volume(
                        id=vol_data.get("id", ""),
                        title=vol_data.get("title", ""),
                        directory=vol_data.get("directory"),
                        chapters=chapters,
                    )
                )
            works.append(
                Work(id=work_data.get("id"), title=work_data.get("title", ""), volumes=volumes)
            )

        return ConfigV2(version=data.get("version", "2.0"), meta=meta, works=works)


class ConfigLoader:
    """Config 加载器，支持 v1 和 v2 格式"""

    @staticmethod
    def load_file(path: Path) -> ConfigV2:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        version = data.get("version", "1.0")
        if version == "2.0":
            return ConfigV2.from_dict(data)
        return ConfigLoader._migrate_v1_to_v2(data, path.parent)

    @staticmethod
    def save(config: ConfigV2, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(config), f, ensure_ascii=False, indent=2)

    @staticmethod
    def _migrate_v1_to_v2(data_v1: Dict[str, Any], config_dir: Path) -> ConfigV2:
        title = data_v1.get("title", "")
        book_id = data_v1.get("novel_id", "")
        config_v2 = ConfigV2(meta=MetaConfig(book_id=book_id, title=title, working_dir="."))
        if "base_image_path" in data_v1:
            config_v2.meta.images.base_path = data_v1["base_image_path"].rstrip("/")
        work = Work(title=title, volumes=[])
        for vol_data in data_v1.get("volumes", []):
            volume = Volume(
                id=vol_data.get("id", vol_data.get("volume_name", "")),
                title=vol_data.get("volume_name", ""),
                chapters=[],
            )
            for ch_data in vol_data.get("chapters", []):
                chapter = Chapter(
                    id=ch_data.get("id", ch_data.get("chapter_name", "")),
                    title=ch_data.get("chapter_name", ch_data.get("title", "")),
                    main_file=ch_data.get("main_file"),
                    side_file=ch_data.get("side_file"),
                    disabled=ch_data.get("disabled", False),
                )
                if "images" in ch_data:
                    chapter.images.files = [
                        ImageReference(
                            filename=img.get("filename", ""),
                            title=img.get("title"),
                            position=img.get("position", "inline"),
                            line=img.get("line"),
                        )
                        for img in ch_data.get("images", [])
                    ]
                volume.chapters.append(chapter)
            work.volumes.append(volume)
        config_v2.works = [work]
        return config_v2

    @staticmethod
    def validate(config: ConfigV2, working_dir: Path = None) -> Tuple[bool, List[str]]:
        errors = []
        working_dir = Path(working_dir) if working_dir else Path.cwd()
        if not config.meta.book_id:
            errors.append("Missing meta.book_id")
        if not config.works:
            errors.append("No works defined")
        for work in config.works:
            for volume in work.volumes:
                for chapter in volume.chapters:
                    if chapter.main_file:
                        full_path = working_dir / chapter.main_file
                        if not full_path.exists():
                            errors.append(f"Main file not found: {chapter.main_file}")
                    if chapter.side_file:
                        full_path = working_dir / chapter.side_file
                        if not full_path.exists():
                            errors.append(f"Side file not found: {chapter.side_file}")
        return len(errors) == 0, errors


# ═══════════════════════════════════════════════════════════════
# 路径解析 (path_resolver.py)
# ═══════════════════════════════════════════════════════════════


class PathResolver:
    """路径解析器"""

    def __init__(self, working_dir: Path = None):
        self.working_dir = Path(working_dir) if working_dir else Path.cwd()
        self._cache = {}

    def resolve_chapter_files(
        self, chapter: Chapter, structure: StructureConfig, volume_id: str
    ) -> Tuple[Optional[Path], Optional[Path]]:
        if chapter.main_file or chapter.side_file:
            main_file = Path(chapter.main_file) if chapter.main_file else None
            side_file = Path(chapter.side_file) if chapter.side_file else None
            if main_file and not main_file.is_absolute():
                main_file = self.working_dir / main_file
            if side_file and not side_file.is_absolute():
                side_file = self.working_dir / side_file
            return main_file, side_file

        cache_key = (volume_id, chapter.id)
        if cache_key in self._cache:
            return self._cache[cache_key]

        vol_dir = self._derive_volume_directory(volume_id, structure)
        chapter_filename = f"{chapter.id}.md"
        main_lang = structure.languages.get("main", "cn")
        side_lang = structure.languages.get("side", "en")
        main_file = self.working_dir / vol_dir / main_lang / chapter_filename
        side_file = self.working_dir / vol_dir / side_lang / chapter_filename
        result = (main_file, side_file)
        self._cache[cache_key] = result
        return result

    def _derive_volume_directory(self, volume_id: str, structure: StructureConfig) -> str:
        if volume_id.startswith("vol_"):
            return volume_id
        if volume_id.isdigit():
            return structure.volume_pattern.format(int(volume_id))
        return volume_id

    def resolve_chapter_images(
        self, chapter_id: str, image_root: Path, strategy: str, params: ImageAssociationParams
    ) -> List[Path]:
        if not image_root.exists():
            return []
        cache_key = (chapter_id, str(image_root), strategy)
        if cache_key in self._cache:
            return self._cache[cache_key]
        images = []
        if strategy == "directory":
            chapter_dir = image_root / chapter_id
            if chapter_dir.is_dir():
                images = sorted(chapter_dir.glob("*"))
        elif strategy == "filename":
            pattern = (params.filename_pattern or "{chapter_id}_*.jpg").replace(
                "{chapter_id}", chapter_id
            )
            images = sorted(image_root.glob(pattern))
        elif strategy == "custom":
            rel_path = params.mappings.get(chapter_id)
            if rel_path:
                path = image_root / rel_path
                if path.is_file():
                    images = [path]
                elif path.is_dir():
                    images = sorted(path.glob("*"))
                else:
                    parent = image_root / Path(rel_path).parent
                    if parent.exists():
                        images = sorted(parent.glob(Path(rel_path).name))
        self._cache[cache_key] = images
        return images

    def compute_relative_path(self, from_file: Path, to_file: Path) -> str:
        try:
            return to_file.relative_to(from_file.parent).as_posix()
        except ValueError:
            return to_file.as_posix()

    def clear_cache(self):
        self._cache.clear()


# ═══════════════════════════════════════════════════════════════
# 文本处理 (text_processor.py)
# ═══════════════════════════════════════════════════════════════


def parse_lines(path: Path, ignore_empty: bool = True) -> List[str]:
    s = path.read_text(encoding="utf-8")
    lines = s.splitlines()
    if ignore_empty:
        lines = [l for l in lines if l.strip() != ""]
        lines = ["    " + l.lstrip() for l in lines]
    return lines


def parse_md_lines(
    path: Path, ignore_empty: bool = True, base_path: Optional[Path] = None
) -> Tuple[Optional[str], List[str]]:
    s = path.read_text(encoding="utf-8")
    lines = s.splitlines()

    title = None
    if lines and lines[0].strip().startswith("#"):
        title_match = re.match(r"^#\s*(.+)", lines[0].strip())
        if title_match:
            title = title_match.group(1).strip()
        lines = lines[1:]

    processed_lines = []
    for line in lines:

        def replace_image(match):
            alt_text = match.group(1)
            img_path = match.group(2).strip()
            img_basename = Path(img_path).name
            return f'<img src="{img_basename}" alt="{alt_text}">'

        line = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", replace_image, line)
        processed_lines.append(line)

    if ignore_empty:
        processed_lines = [l for l in processed_lines if l.strip() != ""]
        processed_lines = ["    " + l.lstrip() for l in processed_lines]
    return title, processed_lines


def validate_line_counts(
    main_lines: List[str],
    side_lines: List[str],
    main_identifier: Optional[str] = None,
    side_identifier: Optional[str] = None,
) -> Tuple[List[str], List[str]]:
    filtered_main = [l for l in main_lines if l.strip()]
    filtered_side = [l for l in side_lines if l.strip()]

    if len(filtered_main) != len(filtered_side):
        m_id = main_identifier or "<main>"
        s_id = side_identifier or "<side>"
        print(
            f"Warning: different line counts: main={len(filtered_main)} side={len(filtered_side)} file_main={m_id} file_side={s_id}"
        )
        if len(filtered_main) < len(filtered_side):
            main_lines += [""] * (len(filtered_side) - len(filtered_main))
        else:
            side_lines += [""] * (len(filtered_main) - len(filtered_side))
        print(f"Padded to {len(main_lines)} lines (identifiers: {m_id}, {s_id}).")
    return main_lines, side_lines


# ═══════════════════════════════════════════════════════════════
# 配置生成器 (config/generator.py - 精简版)
# ═══════════════════════════════════════════════════════════════


@dataclass
class GeneratorOptions:
    """生成器选项"""

    book_id: str
    title: str
    working_dir: str = "."
    volume_pattern: str = "vol_{:03d}"
    image_base_path: str = "images"
    image_strategy: str = "directory"
    reference_style: str = "placeholder"
    languages: Dict[str, str] = None

    def __post_init__(self):
        if self.languages is None:
            self.languages = {"main": "cn", "side": "en"}


class ConfigGenerator(ABC):
    """ConfigGenerator 基类"""

    def __init__(self):
        self.options: Optional[GeneratorOptions] = None
        self.config: Optional[ConfigV2] = None

    @abstractmethod
    def generate(self, options: GeneratorOptions) -> ConfigV2:
        pass

    def _create_base_config(self, options: GeneratorOptions) -> ConfigV2:
        self.options = options
        meta = MetaConfig(
            book_id=options.book_id,
            title=options.title,
            working_dir=options.working_dir,
            images=ImageConfig(
                enabled=True,
                base_path=options.image_base_path,
                association_strategy=options.image_strategy,
                association_params=ImageAssociationParams(),
                reference_style=options.reference_style,
                reference_config=ImageReferenceConfig(),
            ),
            structure=StructureConfig(
                type="standard", volume_pattern=options.volume_pattern, languages=options.languages
            ),
        )
        config = ConfigV2(meta=meta, works=[])
        self.config = config
        return config

    def _add_work(self, title: str = "", volumes: List[Volume] = None) -> Work:
        if self.config is None:
            raise RuntimeError("Base config not initialized")
        work = Work(title=title or self.options.title, volumes=volumes or [])
        self.config.works.append(work)
        return work

    def _add_volume(self, work: Work, vol_id: str, vol_title: str = "") -> Volume:
        volume = Volume(id=vol_id, title=vol_title)
        work.volumes.append(volume)
        return volume

    def _add_chapter(
        self,
        volume: Volume,
        ch_id: str,
        ch_title: str = "",
        main_file: Optional[str] = None,
        side_file: Optional[str] = None,
    ) -> Chapter:
        chapter = Chapter(id=ch_id, title=ch_title, main_file=main_file, side_file=side_file)
        volume.chapters.append(chapter)
        return chapter

    def save(self, path: Path) -> Path:
        if self.config is None:
            raise RuntimeError("No config to save. Call generate() first.")
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(self.config), f, ensure_ascii=False, indent=2)
        return path


class StandardConfigGenerator(ConfigGenerator):
    """标准配置生成器 - 扫描文件系统"""

    def generate(self, options: GeneratorOptions) -> ConfigV2:
        config = self._create_base_config(options)
        working_dir = Path(options.working_dir)
        catalog_data = self._load_catalog(options.book_id, working_dir)
        structure_type = self._detect_structure_type(working_dir)
        config.meta.structure.type = structure_type
        if structure_type == "standard":
            self._scan_standard_structure(working_dir, catalog_data)
        elif structure_type == "flat":
            self._scan_flat_structure(working_dir, catalog_data)
        return config

    def _load_catalog(self, book_id: str, working_dir: Path) -> Optional[Dict[str, Any]]:
        try:
            data_root = working_dir.parent.parent
            catalog_file = data_root / "catalogs" / f"{book_id}.json"
            if not catalog_file.exists():
                return None
            with open(catalog_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def _detect_structure_type(self, working_dir: Path) -> str:
        vol_dirs = list(working_dir.glob("vol_*"))
        if vol_dirs:
            for vol_dir in vol_dirs:
                lang_dirs = list(vol_dir.glob("*"))
                if any(d.is_dir() and d.name in ["cn", "en", "zh", "en-US"] for d in lang_dirs):
                    return "standard"
        flat_files = list(working_dir.glob("ch_*_*.md"))
        if flat_files:
            return "flat"
        return "standard"

    def _scan_standard_structure(
        self, working_dir: Path, catalog_data: Optional[Dict] = None
    ) -> None:
        work = self._add_work()
        vol_pattern = re.compile(r"vol_(\d+)")
        vol_dirs = sorted(
            [d for d in working_dir.iterdir() if d.is_dir() and vol_pattern.match(d.name)],
            key=lambda d: int(vol_pattern.match(d.name).group(1)),
        )
        catalog_map = {}
        if catalog_data:
            for vol_idx, vol_info in enumerate(catalog_data.get("volumes", [])):
                vol_idx_padded = str(vol_idx + 1).zfill(3)
                catalog_map[vol_idx_padded] = {}
                for ch_info in vol_info.get("chapters", []):
                    url = ch_info.get("url", "")
                    ch_id_match = re.search(r"/(\d+)\.htm", url)
                    if ch_id_match:
                        ch_id = ch_id_match.group(1)
                        catalog_map[vol_idx_padded][ch_id] = {
                            "name": ch_info.get("chapter_name", ""),
                            "vol_name": vol_info.get("volume_name", f"Volume {vol_idx + 1}"),
                        }
        for vol_dir in vol_dirs:
            vol_match = vol_pattern.match(vol_dir.name)
            vol_num = int(vol_match.group(1))
            vol_id = str(vol_num).zfill(3)
            vol_title = vol_dir.name
            if vol_id in catalog_map and catalog_map[vol_id]:
                first_val = next(iter(catalog_map[vol_id].values()))
                if "vol_name" in first_val:
                    vol_title = first_val["vol_name"]
            volume = self._add_volume(work, vol_id, vol_title=vol_title)
            lang_dirs = {d.name: d for d in vol_dir.iterdir() if d.is_dir()}
            main_lang = self.options.languages.get("main", "cn")
            main_dir = lang_dirs.get(main_lang)
            if main_dir:
                for main_file in sorted(main_dir.glob("*.md")):
                    ch_match = re.match(r"(\d+)", main_file.stem)
                    if not ch_match:
                        continue
                    ch_id = ch_match.group(1)
                    ch_title = main_file.stem
                    if vol_id in catalog_map and ch_id in catalog_map[vol_id]:
                        ch_title = catalog_map[vol_id][ch_id].get("name", ch_title)
                    side_lang = self.options.languages.get("side", "en")
                    side_dir = lang_dirs.get(side_lang)
                    side_file = side_dir / main_file.name if side_dir else None
                    main_rel = str(main_file.relative_to(working_dir))
                    side_rel = (
                        str(side_file.relative_to(working_dir))
                        if side_file and side_file.exists()
                        else None
                    )
                    self._add_chapter(
                        volume, ch_id, ch_title=ch_title, main_file=main_rel, side_file=side_rel
                    )

    def _scan_flat_structure(self, working_dir: Path, catalog_data: Optional[Dict] = None) -> None:
        work = self._add_work()
        volume = self._add_volume(work, "001", vol_title="Volume 001")
        ch_pattern = re.compile(r"ch_(\d+)_")
        ch_files = {}
        for md_file in working_dir.glob("ch_*.md"):
            match = ch_pattern.match(md_file.name)
            if not match:
                continue
            ch_id = match.group(1)
            if ch_id not in ch_files:
                ch_files[ch_id] = {}
            lang_match = re.search(r"_([a-z]{2})\.md", md_file.name)
            if lang_match:
                ch_files[ch_id][lang_match.group(1)] = md_file
        main_lang = self.options.languages.get("main", "cn")
        side_lang = self.options.languages.get("side", "en")
        for ch_id in sorted(ch_files.keys()):
            main_file = ch_files[ch_id].get(main_lang)
            side_file = ch_files[ch_id].get(side_lang)
            if not main_file:
                continue
            main_rel = str(main_file.relative_to(working_dir))
            side_rel = str(side_file.relative_to(working_dir)) if side_file else None
            self._add_chapter(
                volume, ch_id, ch_title=main_file.stem, main_file=main_rel, side_file=side_rel
            )


class CrawlerOutputGenerator(ConfigGenerator):
    """爬虫输出生成器 - 从爬虫 JSON 生成 config"""

    def generate(self, options: GeneratorOptions, crawler_json: Path = None) -> ConfigV2:
        if not crawler_json:
            raise ValueError("crawler_json path is required")
        return self.generate_from_crawler_json(options, crawler_json)

    def generate_from_crawler_json(self, options: GeneratorOptions, crawler_json: Path) -> ConfigV2:
        config = self._create_base_config(options)
        with open(crawler_json, "r", encoding="utf-8") as f:
            crawler_data = json.load(f)
        config.meta.title = crawler_data.get("title", options.title)
        work = self._add_work(title=crawler_data.get("title", options.title))
        for vol_data in crawler_data.get("volumes", []):
            vol_id = vol_data.get("id", "001").zfill(3)
            volume = self._add_volume(
                work, vol_id, vol_title=vol_data.get("title", f"Volume {vol_id}")
            )
            for ch_data in vol_data.get("chapters", []):
                ch_id = ch_data.get("id", "").zfill(3)
                chapter = self._add_chapter(
                    volume,
                    ch_id,
                    ch_title=ch_data.get("title", f"Chapter {ch_id}"),
                    main_file=ch_data.get("main_file"),
                    side_file=ch_data.get("side_file"),
                )
                for idx, img_name in enumerate(ch_data.get("images", [])):
                    chapter.images.files.append(ImageReference(filename=img_name))
        return config


# ═══════════════════════════════════════════════════════════════
# 高层构建 API (build.py)
# ═══════════════════════════════════════════════════════════════


@dataclass
class BuildOptions:
    """构建选项"""

    data_root: Path
    output_dir: Path
    book_id: str
    title: str = ""
    main_pattern: Optional[str] = None
    side_pattern: Optional[str] = None
    image_pattern: Optional[str] = None
    working_dir_candidates: Optional[List[str]] = None
    validate_config: bool = True
    copy_images: bool = True
    preserve_image_structure: bool = True
    search_recursive_images: bool = False

    def __post_init__(self):
        if isinstance(self.data_root, str):
            self.data_root = Path(self.data_root)
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)


@dataclass
class BuildResult:
    """构建结果"""

    success: bool
    config_file: Optional[Path] = None
    output_dir: Optional[Path] = None
    working_dir: Optional[Path] = None
    images_copied: int = 0
    images_failed: int = 0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class PatternPathResolver:
    """Pattern 路径解析器"""

    PLACEHOLDER_PATTERN = r"\{([^}]+)\}"

    def __init__(self, base_dir: Path, book_id: str):
        self.base_dir = Path(base_dir)
        self.book_id = book_id

    def expand_pattern(self, pattern: str, **context) -> List[Path]:
        if "book_id" not in context:
            context["book_id"] = self.book_id
        expanded = pattern
        for key, value in context.items():
            expanded = expanded.replace(f"{{{key}}}", str(value))
        full_path = self.base_dir / expanded
        if "*" in str(full_path) or "?" in str(full_path):
            parent = full_path.parent
            pattern_str = full_path.name
            if parent.exists():
                return sorted(parent.glob(pattern_str))
            return []
        return [full_path]


class BuildExecutor:
    """构建执行器"""

    def __init__(self, options: BuildOptions):
        self.options = options
        from .cli import CommandDispatcher

        self.dispatcher = CommandDispatcher()
        self.config: Optional[ConfigV2] = None
        self.working_dir: Optional[Path] = None

    def execute(self) -> BuildResult:
        result = BuildResult(success=False, output_dir=self.options.output_dir)
        logger.info("=" * 70)
        logger.info("开始构建流程")
        logger.info("=" * 70)
        logger.info(f"数据根目录: {self.options.data_root.absolute()}")
        logger.info(f"输出目录: {self.options.output_dir.absolute()}")
        logger.info(f"书籍 ID: {self.options.book_id}")

        if not self._step_find_working_dir(result):
            return result
        if not self._step_generate_config(result):
            return result
        if self.options.validate_config:
            if not self._step_validate_config(result):
                return result
        if not self._step_generate_html(result):
            return result
        if self.options.copy_images:
            if not self._step_copy_images(result):
                logger.warning("[WARN] 图片复制步骤出错，但继续处理")

        result.success = True
        logger.info("\n" + "=" * 70)
        logger.info("[OK] 构建完成！")
        logger.info("=" * 70)
        return result

    def _step_find_working_dir(self, result: BuildResult) -> bool:
        logger.info("\n步骤 1: 发现工作目录")
        from .utils import find_working_directory

        try:
            if not self.options.data_root.exists():
                msg = f"数据根目录不存在: {self.options.data_root}"
                logger.error(f"[ERROR] {msg}")
                result.errors.append(msg)
                return False
            working_dir = find_working_directory(
                self.options.data_root,
                self.options.book_id,
                candidates=self.options.working_dir_candidates,
            )
            if not working_dir:
                msg = f"无法找到工作目录（book_id={self.options.book_id}）"
                logger.error(f"[ERROR] {msg}")
                result.errors.append(msg)
                return False
            self.working_dir = working_dir
            result.working_dir = working_dir
            logger.info(f"[OK] 工作目录: {working_dir}")
            return True
        except Exception as e:
            msg = f"发现工作目录时出错: {e}"
            logger.error(f"[ERROR] {msg}")
            result.errors.append(msg)
            return False

    def _step_generate_config(self, result: BuildResult) -> bool:
        logger.info("\n步骤 2: 生成配置文件")
        try:
            working_dir_abs = self.working_dir.resolve()
            config_file = self.options.output_dir / "config.json"
            config_dict = {
                "mode": "gen-config",
                "book_id": self.options.book_id,
                "title": self.options.title or f"Book {self.options.book_id}",
                "working_dir": str(working_dir_abs),
                "volume_pattern": "vol_{:03d}",
                "image_strategy": "directory",
                "output_structure": "by_volume",
                "output": str(config_file),
            }
            self.dispatcher.dispatch(config_dict)
            self.config = ConfigLoader.load_file(config_file)
            result.config_file = config_file
            logger.info(f"[OK] Config 已生成: {config_file}")
            return True
        except Exception as e:
            msg = f"生成配置文件时出错: {e}"
            logger.error(f"[ERROR] {msg}")
            import traceback

            traceback.print_exc()
            result.errors.append(msg)
            return False

    def _step_validate_config(self, result: BuildResult) -> bool:
        logger.info("\n步骤 3: 验证配置文件")
        try:
            is_valid, errors = ConfigLoader.validate(self.config, self.working_dir)
            if is_valid:
                logger.info("[OK] Config 验证通过")
                return True
            logger.error("[ERROR] Config 验证失败:")
            for error in errors:
                logger.error(f"  - {error}")
                result.errors.append(error)
            return False
        except Exception as e:
            msg = f"验证配置文件时出错: {e}"
            logger.error(f"[ERROR] {msg}")
            result.errors.append(msg)
            return False

    def _step_generate_html(self, result: BuildResult) -> bool:
        logger.info("\n步骤 4: 生成 HTML 输出")
        try:
            self.dispatcher.dispatch(
                {
                    "mode": "book_index",
                    "index": result.config_file,
                    "output_dir": str(self.options.output_dir),
                }
            )
            logger.info(f"[OK] HTML 已生成: {self.options.output_dir}")
            return True
        except Exception as e:
            msg = f"生成 HTML 时出错: {e}"
            logger.error(f"[ERROR] {msg}")
            import traceback

            traceback.print_exc()
            result.errors.append(msg)
            return False

    def _step_copy_images(self, result: BuildResult) -> bool:
        logger.info("\n步骤 5: 复制图片文件")
        from .utils import copy_images_from_config

        try:
            copied, failed = copy_images_from_config(
                result.config_file,
                self.options.data_root,
                self.options.output_dir,
                preserve_structure=self.options.preserve_image_structure,
                search_recursive=self.options.search_recursive_images,
                overwrite=False,
            )
            result.images_copied, result.images_failed = copied, failed
            logger.info(f"[OK] 图片复制完成: {copied} 张成功, {failed} 张失败")
            return True
        except Exception as e:
            msg = f"复制图片时出错: {e}"
            logger.error(f"[ERROR] {msg}")
            import traceback

            traceback.print_exc()
            result.errors.append(msg)
            return False


def build_from_data(options: BuildOptions) -> BuildResult:
    """端到端数据构建 API"""
    executor = BuildExecutor(options)
    return executor.execute()
