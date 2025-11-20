"""
Config v2.0 数据模型与加载器

支持：
- 多种文件结构（标准/扁平/自定义）
- 文件路径自动推导
- 图片关联策略（目录/文件名/自定义）
- 完全向后兼容旧 config 格式
"""

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import json
import re


@dataclass
class ImageReference:
    """图片信息"""
    filename: str
    title: Optional[str] = None
    position: str = "inline"  # inline / gallery
    line: Optional[int] = None
    original_url: Optional[str] = None


@dataclass
class ChapterImages:
    """章节的图片配置"""
    override_mode: str = "none"  # none / explicit / custom
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
        """是否需要自动推导文件路径"""
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
    chapter_id_field: str = "id"  # id / number / custom
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
    association_strategy: str = "directory"  # directory / filename / custom
    association_params: ImageAssociationParams = field(default_factory=ImageAssociationParams)
    reference_style: str = "placeholder"  # placeholder / filename / relative_path
    reference_config: ImageReferenceConfig = field(default_factory=ImageReferenceConfig)


@dataclass
class StructureConfig:
    """文件结构配置"""
    type: str = "standard"  # standard / flat / custom
    volume_pattern: str = "vol_{:03d}"
    volume_title_source: str = "auto"  # auto / filename / metadata
    chapter_id_field: str = "id"  # id / filename / title
    chapter_title_source: str = "title"  # title / markdown_h1 / filename
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
    meta: MetaConfig = field(default_factory=MetaConfig)
    works: List[Work] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ConfigV2":
        """从字典创建"""
        # 简单实现，生产环境应使用 pydantic
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
                chapters = []
                for ch_data in vol_data.get("chapters", []):
                    chapter = Chapter(
                        id=ch_data.get("id", ""),
                        title=ch_data.get("title", ""),
                        main_file=ch_data.get("main_file"),
                        side_file=ch_data.get("side_file"),
                        disabled=ch_data.get("disabled", False),
                    )
                    chapters.append(chapter)
                
                volume = Volume(
                    id=vol_data.get("id", ""),
                    title=vol_data.get("title", ""),
                    directory=vol_data.get("directory"),
                    chapters=chapters,
                )
                volumes.append(volume)
            
            work = Work(
                id=work_data.get("id"),
                title=work_data.get("title", ""),
                volumes=volumes,
            )
            works.append(work)
        
        return ConfigV2(
            version=data.get("version", "2.0"),
            meta=meta,
            works=works,
        )


class ConfigLoader:
    """Config 加载器，支持 v1 和 v2 格式"""
    
    @staticmethod
    def load_file(path: Path) -> ConfigV2:
        """加载 config 文件"""
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 检测版本
        version = data.get("version", "1.0")
        
        if version == "2.0":
            return ConfigV2.from_dict(data)
        else:
            # 自动转换 v1 到 v2
            return ConfigLoader._migrate_v1_to_v2(data, path.parent)
    
    @staticmethod
    def _migrate_v1_to_v2(data_v1: Dict[str, Any], config_dir: Path) -> ConfigV2:
        """从 v1 格式迁移到 v2"""
        
        # 获取基础信息
        title = data_v1.get("title", "")
        book_id = data_v1.get("novel_id", "")
        
        # 创建 v2 config
        config_v2 = ConfigV2()
        config_v2.meta.title = title
        config_v2.meta.book_id = book_id
        config_v2.meta.working_dir = "."
        
        # 处理旧格式的 base_image_path
        if "base_image_path" in data_v1:
            config_v2.meta.images.base_path = data_v1["base_image_path"].rstrip("/")
        
        # 转换作品和卷
        work = Work(title=title, volumes=[])
        
        for vol_data in data_v1.get("volumes", []):
            volume = Volume(
                id=vol_data.get("id", vol_data.get("volume_name", "")),
                title=vol_data.get("volume_name", ""),
                chapters=[],
            )
            
            for ch_data in vol_data.get("chapters", []):
                # v1 格式：main_file / side_file 已指定
                chapter = Chapter(
                    id=ch_data.get("id", ch_data.get("chapter_name", "")),
                    title=ch_data.get("chapter_name", ch_data.get("title", "")),
                    main_file=ch_data.get("main_file"),
                    side_file=ch_data.get("side_file"),
                    disabled=ch_data.get("disabled", False),
                )
                
                # 转换 images 字段
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
        """验证 config"""
        errors = []
        working_dir = Path(working_dir) if working_dir else Path.cwd()
        
        # 检查必需字段
        if not config.meta.book_id:
            errors.append("Missing meta.book_id")
        
        if not config.works:
            errors.append("No works defined")
        
        # 检查文件存在性（仅针对显式指定的路径）
        for work in config.works:
            for volume in work.volumes:
                for chapter in volume.chapters:
                    # 如果显式指定了文件路径，检查存在性
                    if chapter.main_file:
                        full_path = working_dir / chapter.main_file
                        if not full_path.exists():
                            errors.append(f"Main file not found: {chapter.main_file}")
                    
                    if chapter.side_file:
                        full_path = working_dir / chapter.side_file
                        if not full_path.exists():
                            errors.append(f"Side file not found: {chapter.side_file}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def save(config: ConfigV2, path: Path) -> Path:
        """保存 config 到文件"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # 转换为字典并序列化
        data = asdict(config)
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return path


class PathResolver:
    """
    路径解析器 - 自动推导文件路径
    
    支持三种卷结构模式：
    1. directory: vol_001/cn/001.md, vol_001/en/001.md
    2. filename: ch_001_cn.md, ch_001_en.md  
    3. custom: 通过映射规则自定义
    """
    
    def __init__(self, config: ConfigV2, working_dir: Path = None):
        self.config = config
        self.working_dir = Path(working_dir) if working_dir else Path(config.meta.working_dir)
        self._path_cache = {}
    
    def resolve_chapter_files(
        self,
        chapter: Chapter,
        volume: Volume,
        work: Work
    ) -> Tuple[Optional[Path], Optional[Path]]:
        """
        解析章节文件路径
        
        返回 (main_file, side_file)，如果找不到返回 None
        
        支持三种策略：
        - explicit: 使用 chapter.main_file / side_file
        - auto_derive: 根据 structure 配置自动推导
        """
        
        # 1. 如果显式指定，直接使用
        if chapter.main_file:
            main_path = self.working_dir / chapter.main_file
        else:
            main_path = self._derive_file_path(chapter, volume, "main")
        
        if chapter.side_file:
            side_path = self.working_dir / chapter.side_file
        else:
            side_path = self._derive_file_path(chapter, volume, "side")
        
        # 验证路径存在
        if main_path and not main_path.exists():
            main_path = None
        if side_path and not side_path.exists():
            side_path = None
        
        return main_path, side_path
    
    def _derive_file_path(
        self,
        chapter: Chapter,
        volume: Volume,
        language_type: str = "main"
    ) -> Optional[Path]:
        """
        根据 structure 配置推导文件路径
        
        language_type: "main" 或 "side"
        """
        
        structure = self.config.meta.structure
        cache_key = f"{volume.id}_{chapter.id}_{language_type}"
        
        if cache_key in self._path_cache:
            return self._path_cache[cache_key]
        
        # 获取语言代码
        lang_main = structure.languages.get("main", "cn")
        lang_side = structure.languages.get("side", "en")
        lang_code = lang_main if language_type == "main" else lang_side
        
        base_path = self.working_dir
        
        # 处理不同的结构类型
        if structure.type == "standard":
            # 标准结构: vol_001/cn/001.md
            vol_dir = structure.volume_pattern.format(int(volume.id) if volume.id.isdigit() else 0)
            chapter_file = f"{chapter.id}.md"
            
            # 尝试多种路径组织方式
            possible_paths = [
                base_path / vol_dir / lang_code / chapter_file,
                base_path / "data" / vol_dir / lang_code / chapter_file,
                base_path / "chapters" / volume.id / vol_dir / lang_code / chapter_file,
            ]
            
            for path in possible_paths:
                if path.exists():
                    self._path_cache[cache_key] = path
                    return path
        
        elif structure.type == "flat":
            # 扁平结构: ch_001_cn.md
            chapter_file = f"ch_{chapter.id}_{lang_code}.md"
            
            possible_paths = [
                base_path / chapter_file,
                base_path / "data" / chapter_file,
                base_path / "chapters" / chapter_file,
            ]
            
            for path in possible_paths:
                if path.exists():
                    self._path_cache[cache_key] = path
                    return path
        
        elif structure.type == "custom":
            # 自定义结构 - 使用映射规则
            pattern = structure.languages.get(f"{language_type}_pattern", "")
            if pattern:
                # 替换占位符
                path_str = pattern.format(
                    volume_id=volume.id,
                    chapter_id=chapter.id,
                    language=lang_code
                )
                path = base_path / path_str
                if path.exists():
                    self._path_cache[cache_key] = path
                    return path
        
        self._path_cache[cache_key] = None
        return None
    
    def resolve_chapter_images(
        self,
        chapter: Chapter,
        volume: Volume,
        work: Work
    ) -> List[Path]:
        """
        解析章节的图片路径
        
        支持三种关联策略：
        - directory: images/vol_001/001/
        - filename: images/vol_001_001_*.png
        - custom: 根据自定义规则映射
        """
        
        if not self.config.meta.images.enabled:
            return []
        
        strategy = self.config.meta.images.association_strategy
        base_dir = self.working_dir / self.config.meta.images.base_path
        
        if not base_dir.exists():
            return []
        
        images = []
        
        if strategy == "directory":
            # 策略1: 按目录组织 images/vol_001/001/
            vol_pattern = self.config.meta.structure.volume_pattern
            vol_dir = vol_pattern.format(int(volume.id) if volume.id.isdigit() else 0)
            
            image_dir = base_dir / vol_dir / chapter.id
            if image_dir.exists():
                images = sorted([f for f in image_dir.glob("*") if f.is_file()])
        
        elif strategy == "filename":
            # 策略2: 按文件名前缀 images/vol_001_001_*.png
            vol_pattern = self.config.meta.structure.volume_pattern
            vol_dir = vol_pattern.format(int(volume.id) if volume.id.isdigit() else 0)
            
            # 移除 vol_{} 格式，提取数字
            vol_num = vol_pattern.split("{")[1].split("}")[0]  # "03d"
            vol_id_clean = volume.id.zfill(3) if volume.id.isdigit() else volume.id
            
            pattern = f"{vol_id_clean}_{chapter.id}_*"
            images = sorted(base_dir.glob(pattern))
        
        elif strategy == "custom":
            # 策略3: 自定义映射
            mappings = self.config.meta.images.association_params.mappings
            key = f"{volume.id}/{chapter.id}"
            
            if key in mappings:
                image_path = base_dir / mappings[key]
                if image_path.is_dir():
                    images = sorted([f for f in image_path.glob("*") if f.is_file()])
                elif image_path.is_file():
                    images = [image_path]
        
        return images
