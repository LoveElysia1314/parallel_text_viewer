"""
ConfigGenerator - 自动生成 Config v2.0

支持从多种数据源生成配置：
1. StandardConfigGenerator: 扫描文件系统
2. CrawlerOutputGenerator: 从爬虫输出 JSON 生成
3. CSVConfigGenerator: 从 CSV 文件导入

用户可以继承 ConfigGenerator 实现自定义生成器。
"""

import json
import csv
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
import re

from ..core.config_v2 import (
    ConfigV2,
    MetaConfig,
    Work,
    Volume,
    Chapter,
    ImageConfig,
    ImageAssociationParams,
    ImageReferenceConfig,
    StructureConfig,
)


@dataclass
class GeneratorOptions:
    """生成器选项"""
    book_id: str
    title: str
    working_dir: str = "."
    volume_pattern: str = "vol_{:03d}"
    image_base_path: str = "images"
    image_strategy: str = "directory"  # directory / filename / custom
    reference_style: str = "placeholder"  # placeholder / filename / relative_path
    languages: Dict[str, str] = None  # {"main": "cn", "side": "en"}
    
    def __post_init__(self):
        if self.languages is None:
            self.languages = {"main": "cn", "side": "en"}


class ConfigGenerator(ABC):
    """
    ConfigGenerator 基类
    
    所有生成器的抽象基类。用户可以继承此类实现自定义生成器。
    
    使用示例：
    ```python
    class MyCustomGenerator(ConfigGenerator):
        def generate(self, options: GeneratorOptions) -> ConfigV2:
            # 实现你的逻辑
            ...
    
    gen = MyCustomGenerator()
    config = gen.generate(GeneratorOptions(...))
    ```
    """
    
    def __init__(self):
        self.options: Optional[GeneratorOptions] = None
        self.config: Optional[ConfigV2] = None
    
    @abstractmethod
    def generate(self, options: GeneratorOptions) -> ConfigV2:
        """
        生成 Config v2.0
        
        Args:
            options: 生成选项
        
        Returns:
            ConfigV2 对象
        """
        pass
    
    def _create_base_config(self, options: GeneratorOptions) -> ConfigV2:
        """创建基础 Config 对象"""
        
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
                type="standard",
                volume_pattern=options.volume_pattern,
                languages=options.languages,
            ),
        )
        
        config = ConfigV2(meta=meta, works=[])
        self.config = config
        
        return config
    
    def _add_work(self, title: str = "", volumes: List[Volume] = None) -> Work:
        """添加作品"""
        if self.config is None:
            raise RuntimeError("Base config not initialized")
        
        work = Work(title=title or self.options.title, volumes=volumes or [])
        self.config.works.append(work)
        
        return work
    
    def _add_volume(self, work: Work, vol_id: str, vol_title: str = "") -> Volume:
        """添加卷"""
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
        """添加章节"""
        chapter = Chapter(
            id=ch_id,
            title=ch_title,
            main_file=main_file,
            side_file=side_file,
        )
        volume.chapters.append(chapter)
        return chapter
    
    def _scan_chapter_images(self, ch_id: str, vol_id: str) -> Optional["ChapterImages"]:
        """
        扫描并关联章节的图片
        
        根据 book_id、vol_id 和 ch_id 在 images 目录中查找对应的图片
        """
        if not self.options:
            return None
        
        # 构造图片目录路径
        # 工作目录通常是: data/chapters/2930
        # 图片目录应该是: data/images/2930/vol_001
        book_id = self.options.book_id
        working_dir = Path(self.options.working_dir)
        
        # 从工作目录 (data/chapters/2930) 向上找到 data 目录
        # data/chapters/2930 -> data/chapters -> data
        data_root = working_dir.parent.parent
        
        # 构造图片目录: data/images/2930/vol_001
        images_dir = data_root / self.options.image_base_path / book_id / f"vol_{vol_id}"
        
        if not images_dir.exists():
            return None
        
        # 查找匹配 ch_id 的图片文件
        # 例如: ch_id = "118359" 时查找 118359_*.jpg
        pattern = f"{ch_id}_*.jpg"
        matching_images = list(images_dir.glob(pattern))
        
        if not matching_images:
            return None
        
        # 构造 ImageReference 列表
        from ..core.config_v2 import ChapterImages, ImageReference
        
        image_refs = []
        for img_file in sorted(matching_images):
            # 构造相对于 data root 的相对路径
            # 例如: images/2930/vol_001/118359_1_159954.jpg
            rel_path = str(img_file.relative_to(data_root))
            
            image_ref = ImageReference(
                filename=rel_path,
                title=None,
                position="inline",
            )
            image_refs.append(image_ref)
        
        if image_refs:
            return ChapterImages(
                override_mode="explicit",
                files=image_refs,
            )
        
        return None
    
    def save(self, path: Path) -> Path:
        """保存生成的 config 到文件"""
        if self.config is None:
            raise RuntimeError("No config to save. Call generate() first.")
        
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        data = asdict(self.config)
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return path


class StandardConfigGenerator(ConfigGenerator):
    """
    标准配置生成器 - 扫描文件系统
    
    自动扫描工作目录下的文件结构，识别卷和章节。
    
    支持的结构模式：
    1. 标准结构: vol_001/cn/001.md, vol_001/en/001.md
    2. 扁平结构: ch_001_cn.md, ch_001_en.md
    
    使用示例：
    ```python
    gen = StandardConfigGenerator()
    config = gen.generate(GeneratorOptions(
        book_id="mybook",
        title="My Book",
        working_dir="/path/to/book",
        volume_pattern="vol_{:03d}",
    ))
    config.meta.structure.type = "standard"
    gen.save(Path("config.json"))
    ```
    """
    
    def generate(self, options: GeneratorOptions) -> ConfigV2:
        """扫描文件系统生成 config"""
        
        config = self._create_base_config(options)
        working_dir = Path(options.working_dir)
        
        # 读取 catalog 文件（如果存在）
        # catalog 通常在 data/catalogs/{book_id}.json
        catalog_data = self._load_catalog(options.book_id, working_dir)
        
        # 检测结构类型
        structure_type = self._detect_structure_type(working_dir)
        config.meta.structure.type = structure_type
        
        if structure_type == "standard":
            self._scan_standard_structure(working_dir, catalog_data)
        elif structure_type == "flat":
            self._scan_flat_structure(working_dir, catalog_data)
        
        return config
    
    def _load_catalog(self, book_id: str, working_dir: Path) -> Optional[Dict[str, Any]]:
        """
        读取 catalog 文件以获取卷名和章节名
        
        Catalog 通常位于: data/catalogs/{book_id}.json
        """
        try:
            # 从工作目录向上找到 data 目录
            # working_dir 通常是 data/chapters/{book_id}
            data_root = working_dir.parent.parent
            
            catalog_file = data_root / "catalogs" / f"{book_id}.json"
            if not catalog_file.exists():
                return None
            
            with open(catalog_file, 'r', encoding='utf-8') as f:
                catalog = json.load(f)
            
            return catalog
        except Exception as e:
            return None
    
    def _detect_structure_type(self, working_dir: Path) -> str:
        """检测目录结构类型"""
        
        # 查找是否有卷目录 (vol_*)
        vol_dirs = list(working_dir.glob("vol_*"))
        if vol_dirs:
            # 检查是否有语言子目录
            for vol_dir in vol_dirs:
                lang_dirs = list(vol_dir.glob("*"))
                if any(d.is_dir() and d.name in ["cn", "en", "zh", "en-US"] for d in lang_dirs):
                    return "standard"
        
        # 查找扁平 markdown 文件 (ch_*_*.md)
        flat_files = list(working_dir.glob("ch_*_*.md"))
        if flat_files:
            return "flat"
        
        # 默认标准结构
        return "standard"
    
    def _scan_standard_structure(self, working_dir: Path, catalog_data: Optional[Dict] = None) -> None:
        """扫描标准结构: vol_xxx/lang/xxx.md"""
        
        work = self._add_work()
        
        # 查找所有卷目录
        vol_pattern = re.compile(r'vol_(\d+)')
        vol_dirs = sorted(
            [d for d in working_dir.iterdir() if d.is_dir() and vol_pattern.match(d.name)],
            key=lambda d: int(vol_pattern.match(d.name).group(1))
        )
        
        # 构建 catalog 快速查询表: {vol_index} -> {ch_id} -> chapter_name
        catalog_map = {}
        if catalog_data:
            volumes = catalog_data.get("volumes", [])
            for vol_idx, vol_info in enumerate(volumes):
                vol_idx_padded = str(vol_idx + 1).zfill(3)
                catalog_map[vol_idx_padded] = {}
                
                for ch_info in vol_info.get("chapters", []):
                    url = ch_info.get("url", "")
                    # 从 URL 提取章节 ID，例如: https://...2930/118227.htm -> 118227
                    ch_id_match = re.search(r'/(\d+)\.htm', url)
                    if ch_id_match:
                        ch_id = ch_id_match.group(1)
                        ch_name = ch_info.get("chapter_name", "")
                        catalog_map[vol_idx_padded][ch_id] = {
                            "name": ch_name,
                            "vol_name": vol_info.get("volume_name", f"Volume {vol_idx + 1}")
                        }
        
        for vol_dir_idx, vol_dir in enumerate(vol_dirs):
            vol_match = vol_pattern.match(vol_dir.name)
            vol_num = int(vol_match.group(1))
            vol_id = str(vol_num).zfill(3)
            
            # 从 catalog 获取卷名
            vol_title = vol_dir.name
            if vol_id in catalog_map:
                # 从 catalog 中获取卷名
                vol_data = list(catalog_map[vol_id].values())
                if vol_data and "vol_name" in vol_data[0]:
                    vol_title = vol_data[0]["vol_name"]
            
            volume = self._add_volume(work, vol_id, vol_title=vol_title)
            
            # 查找语言目录
            lang_dirs = {d.name: d for d in vol_dir.iterdir() if d.is_dir()}
            
            # 获取主语言目录中的章节
            main_lang = self.options.languages.get("main", "cn")
            main_dir = lang_dirs.get(main_lang)
            
            if main_dir:
                # 扫描主语言目录中的 markdown 文件
                for main_file in sorted(main_dir.glob("*.md")):
                    ch_match = re.match(r'(\d+)', main_file.stem)
                    if not ch_match:
                        continue
                    
                    ch_id = ch_match.group(1)
                    
                    # 从 catalog 获取章节名，如果没有则使用文件名
                    ch_title = main_file.stem
                    if vol_id in catalog_map and ch_id in catalog_map[vol_id]:
                        ch_title = catalog_map[vol_id][ch_id].get("name", ch_title)
                    
                    # 查找对应的侧语言文件
                    side_lang = self.options.languages.get("side", "en")
                    side_dir = lang_dirs.get(side_lang)
                    side_file = side_dir / main_file.name if side_dir else None
                    
                    # 相对路径
                    main_rel = str(main_file.relative_to(working_dir))
                    side_rel = str(side_file.relative_to(working_dir)) if side_file and side_file.exists() else None
                    
                    # 扫描关联的图片
                    chapter_images = self._scan_chapter_images(ch_id, vol_id)
                    
                    chapter = self._add_chapter(
                        volume,
                        ch_id,
                        ch_title=ch_title,
                        main_file=main_rel,
                        side_file=side_rel,
                    )
                    
                    # 添加图片信息到章节
                    if chapter_images:
                        chapter.images = chapter_images
    
    def _scan_flat_structure(self, working_dir: Path, catalog_data: Optional[Dict] = None) -> None:
        """扫描扁平结构: ch_001_cn.md, ch_001_en.md"""
        
        work = self._add_work()
        volume = self._add_volume(work, "001", vol_title="Volume 001")
        
        # 查找所有章节文件
        ch_pattern = re.compile(r'ch_(\d+)_')
        ch_files = {}
        
        for md_file in working_dir.glob("ch_*.md"):
            match = ch_pattern.match(md_file.name)
            if not match:
                continue
            
            ch_id = match.group(1)
            if ch_id not in ch_files:
                ch_files[ch_id] = {}
            
            # 提取语言
            lang_match = re.search(r'_([a-z]{2})\.md', md_file.name)
            if lang_match:
                lang = lang_match.group(1)
                ch_files[ch_id][lang] = md_file
        
        # 创建章节
        main_lang = self.options.languages.get("main", "cn")
        side_lang = self.options.languages.get("side", "en")
        
        for ch_id in sorted(ch_files.keys()):
            main_file = ch_files[ch_id].get(main_lang)
            side_file = ch_files[ch_id].get(side_lang)
            
            if not main_file:
                continue
            
            # 使用文件名作为章节标题
            ch_title = main_file.stem
            
            main_rel = str(main_file.relative_to(working_dir))
            side_rel = str(side_file.relative_to(working_dir)) if side_file else None
            
            self._add_chapter(
                volume,
                ch_id,
                ch_title=ch_title,
                main_file=main_rel,
                side_file=side_rel,
            )


class CrawlerOutputGenerator(ConfigGenerator):
    """
    爬虫输出生成器 - 从爬虫 JSON 生成 config
    
    假设爬虫输出格式为：
    ```json
    {
        "title": "Book Title",
        "volumes": [
            {
                "id": "001",
                "title": "Volume 1",
                "chapters": [
                    {
                        "id": "001",
                        "title": "Chapter 1",
                        "main_file": "vol_001/cn/001.md",
                        "side_file": "vol_001/en/001.md",
                        "images": ["img1.png", "img2.png"]
                    }
                ]
            }
        ]
    }
    ```
    
    使用示例：
    ```python
    gen = CrawlerOutputGenerator()
    config = gen.generate_from_crawler_json(
        GeneratorOptions(...),
        Path("crawler_output.json")
    )
    gen.save(Path("config.json"))
    ```
    """
    
    def generate(self, options: GeneratorOptions, crawler_json: Path = None) -> ConfigV2:
        """
        从爬虫输出生成 config
        
        Args:
            options: 生成选项
            crawler_json: 爬虫输出 JSON 文件路径
        """
        
        if not crawler_json:
            raise ValueError("crawler_json path is required")
        
        return self.generate_from_crawler_json(options, crawler_json)
    
    def generate_from_crawler_json(
        self,
        options: GeneratorOptions,
        crawler_json: Path,
    ) -> ConfigV2:
        """从爬虫 JSON 生成 config"""
        
        config = self._create_base_config(options)
        
        with open(crawler_json, "r", encoding="utf-8") as f:
            crawler_data = json.load(f)
        
        # 创建工作
        work_title = crawler_data.get("title", options.title)
        work = self._add_work(work_title)
        
        # 处理卷和章节
        for vol_data in crawler_data.get("volumes", []):
            vol_id = vol_data.get("id", "").zfill(3)
            vol_title = vol_data.get("title", f"Volume {vol_id}")
            
            volume = self._add_volume(work, vol_id, vol_title)
            
            for ch_data in vol_data.get("chapters", []):
                ch_id = ch_data.get("id", "").zfill(3)
                ch_title = ch_data.get("title", f"Chapter {ch_id}")
                main_file = ch_data.get("main_file")
                side_file = ch_data.get("side_file")
                
                chapter = self._add_chapter(
                    volume,
                    ch_id,
                    ch_title,
                    main_file,
                    side_file,
                )
                
                # 处理图片元数据
                for idx, img_name in enumerate(ch_data.get("images", [])):
                    from ..core.config_v2 import ImageReference
                    chapter.images.files.append(
                        ImageReference(filename=img_name)
                    )
        
        return config


class CSVConfigGenerator(ConfigGenerator):
    """
    CSV 导入生成器 - 从 CSV 文件导入章节信息
    
    CSV 格式：
    ```
    volume_id,volume_title,chapter_id,chapter_title,main_file,side_file
    001,Volume 1,001,Chapter 1,vol_001/cn/001.md,vol_001/en/001.md
    001,Volume 1,002,Chapter 2,vol_001/cn/002.md,vol_001/en/002.md
    ```
    
    使用示例：
    ```python
    gen = CSVConfigGenerator()
    config = gen.generate(
        GeneratorOptions(...),
        csv_file=Path("chapters.csv")
    )
    gen.save(Path("config.json"))
    ```
    """
    
    def generate(self, options: GeneratorOptions, csv_file: Path = None) -> ConfigV2:
        """
        从 CSV 文件生成 config
        
        Args:
            options: 生成选项
            csv_file: CSV 文件路径
        """
        
        if not csv_file:
            raise ValueError("csv_file path is required")
        
        return self.generate_from_csv(options, csv_file)
    
    def generate_from_csv(
        self,
        options: GeneratorOptions,
        csv_file: Path,
    ) -> ConfigV2:
        """从 CSV 文件生成 config"""
        
        config = self._create_base_config(options)
        
        with open(csv_file, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            
            volumes = {}
            work = self._add_work()
            
            for row in reader:
                vol_id = row.get("volume_id", "001").zfill(3)
                vol_title = row.get("volume_title", f"Volume {vol_id}")
                ch_id = row.get("chapter_id", "").zfill(3)
                ch_title = row.get("chapter_title", f"Chapter {ch_id}")
                main_file = row.get("main_file")
                side_file = row.get("side_file")
                
                # 创建或获取卷
                if vol_id not in volumes:
                    volume = self._add_volume(work, vol_id, vol_title)
                    volumes[vol_id] = volume
                else:
                    volume = volumes[vol_id]
                
                # 添加章节
                self._add_chapter(
                    volume,
                    ch_id,
                    ch_title,
                    main_file,
                    side_file,
                )
        
        return config


class GeneratorRegistry:
    """
    生成器注册表
    
    用于管理和查找生成器。支持插件式扩展。
    
    使用示例：
    ```python
    # 注册自定义生成器
    class MyGenerator(ConfigGenerator):
        ...
    
    registry = GeneratorRegistry()
    registry.register("my_gen", MyGenerator)
    
    # 创建生成器
    gen = registry.create("my_gen")
    config = gen.generate(options)
    ```
    """
    
    def __init__(self):
        self._generators = {}
        self._register_builtins()
    
    def _register_builtins(self) -> None:
        """注册内置生成器"""
        self.register("standard", StandardConfigGenerator)
        self.register("crawler", CrawlerOutputGenerator)
        self.register("csv", CSVConfigGenerator)
    
    def register(self, name: str, generator_class) -> None:
        """注册生成器"""
        self._generators[name] = generator_class
    
    def unregister(self, name: str) -> None:
        """注销生成器"""
        if name in self._generators:
            del self._generators[name]
    
    def create(self, name: str) -> ConfigGenerator:
        """创建生成器实例"""
        if name not in self._generators:
            raise ValueError(f"Unknown generator: {name}")
        
        return self._generators[name]()
    
    def list_generators(self) -> List[str]:
        """列出所有可用生成器"""
        return list(self._generators.keys())
    
    def get_help(self, name: str) -> str:
        """获取生成器帮助信息"""
        if name not in self._generators:
            return f"Unknown generator: {name}"
        
        gen_class = self._generators[name]
        return gen_class.__doc__ or "No documentation available"


# 全局生成器注册表
_default_registry = None


def get_default_registry() -> GeneratorRegistry:
    """获取全局生成器注册表"""
    global _default_registry
    if _default_registry is None:
        _default_registry = GeneratorRegistry()
    return _default_registry
