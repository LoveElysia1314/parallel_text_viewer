"""
占位符图片引用系统

支持在 Markdown 中使用占位符 {IMG:001_001} 来引用图片，
解藕 Markdown 内容和物理文件结构。

核心思想：
- Markdown 中只写 {IMG:chapter_index}，不涉及文件路径
- 通过 PlaceholderResolver 在 HTML 生成时动态替换为实际图片
- 支持三种引用风格：placeholder / filename / relative_path
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable
from collections import defaultdict

from .config_v2 import ConfigV2, PathResolver, Chapter, Volume, Work


@dataclass
class PlaceholderImage:
    """占位符对应的图片"""
    chapter_id: str
    index: int
    image_path: Path
    filename: str
    title: Optional[str] = None
    

class PlaceholderResolver:
    """
    占位符解析器
    
    负责：
    1. 扫描 Markdown 中的占位符 {IMG:xxx_xxx}
    2. 根据 config 的 image_association_strategy 找到对应图片
    3. 根据 reference_style 转换为最终形式
    """
    
    # 占位符正则：{IMG:chapter_id_index}
    PLACEHOLDER_PATTERN = re.compile(r'\{IMG:([a-zA-Z0-9_]+)_(\d+)\}')
    
    def __init__(self, config: ConfigV2, working_dir: Path = None):
        self.config = config
        self.working_dir = Path(working_dir) if working_dir else Path(config.meta.working_dir)
        self.path_resolver = PathResolver(config, self.working_dir)
        
        # 缓存：chapter_id -> List[PlaceholderImage]
        self._image_cache: Dict[str, List[PlaceholderImage]] = defaultdict(list)
        self._cache_initialized = False
    
    def _build_image_cache(self) -> None:
        """构建图片缓存，以加速批量替换"""
        
        if self._cache_initialized:
            return
        
        for work in self.config.works:
            for volume in work.volumes:
                for chapter in volume.chapters:
                    # 获取该章节的所有图片
                    image_paths = self.path_resolver.resolve_chapter_images(
                        chapter, volume, work
                    )
                    
                    for idx, img_path in enumerate(image_paths):
                        placeholder_img = PlaceholderImage(
                            chapter_id=chapter.id,
                            index=idx,
                            image_path=img_path,
                            filename=img_path.name,
                            title=None,
                        )
                        
                        # 如果 config 中有图片元数据，尝试匹配
                        for img_ref in chapter.images.files:
                            if img_ref.filename == img_path.name:
                                placeholder_img.title = img_ref.title
                                break
                        
                        self._image_cache[chapter.id].append(placeholder_img)
        
        self._cache_initialized = True
    
    def find_placeholders(self, text: str) -> List[Tuple[str, str, Chapter]]:
        """
        在文本中找到所有占位符
        
        返回列表，每个元素为 (占位符, 替换内容, chapter)
        """
        
        self._build_image_cache()
        results = []
        
        for match in self.PLACEHOLDER_PATTERN.finditer(text):
            placeholder = match.group(0)  # 完整占位符 {IMG:001_001}
            chapter_id = match.group(1)   # 001
            index = int(match.group(2))    # 001
            
            # 查找对应章节
            chapter = self._find_chapter_by_id(chapter_id)
            if not chapter:
                continue
            
            # 获取替换内容
            replacement = self._get_replacement(chapter_id, index)
            if replacement:
                results.append((placeholder, replacement, chapter))
        
        return results
    
    def replace_placeholders(
        self,
        text: str,
        chapter: Chapter = None,
        volume: Volume = None,
        work: Work = None
    ) -> str:
        """
        替换文本中的所有占位符
        
        参数可选，用于计算相对路径等
        """
        
        self._build_image_cache()
        
        def replacer(match):
            placeholder = match.group(0)
            chapter_id = match.group(1)
            index = int(match.group(2))
            
            replacement = self._get_replacement(chapter_id, index)
            return replacement if replacement else placeholder
        
        return self.PLACEHOLDER_PATTERN.sub(replacer, text)
    
    def get_images_for_chapter(self, chapter_id: str) -> List[PlaceholderImage]:
        """获取某章节的所有图片"""
        self._build_image_cache()
        return self._image_cache.get(chapter_id, [])
    
    def _get_replacement(self, chapter_id: str, index: int) -> Optional[str]:
        """
        根据 reference_style 获取替换内容
        
        支持三种风格：
        1. placeholder: 保持原样（实际上不会调用此函数）
        2. filename: ![](image_001.png)
        3. relative_path: ![](../images/001_001.png)
        """
        
        images = self._image_cache.get(chapter_id, [])
        if index >= len(images):
            return None
        
        img = images[index]
        style = self.config.meta.images.reference_style
        
        if style == "filename":
            return self._format_as_filename(img)
        elif style == "relative_path":
            return self._format_as_relative_path(img)
        elif style == "placeholder":
            # 保持占位符，通常在 HTML 生成时处理
            return None
        else:
            # 默认使用文件名
            return self._format_as_filename(img)
    
    def _format_as_filename(self, img: PlaceholderImage) -> str:
        """格式化为: ![title](filename.png)"""
        title = img.title or img.filename
        return f"![{title}]({img.filename})"
    
    def _format_as_relative_path(self, img: PlaceholderImage) -> str:
        """格式化为: ![title](../../images/chapter_001/img_001.png)"""
        # 这里简化实现，实际可能需要计算相对路径
        relative = f"../{self.config.meta.images.base_path}/{img.chapter_id}/{img.filename}"
        title = img.image_path.stem
        return f"![{title}]({relative})"
    
    def _find_chapter_by_id(self, chapter_id: str) -> Optional[Tuple[Chapter, Volume, Work]]:
        """通过 chapter_id 查找章节"""
        for work in self.config.works:
            for volume in work.volumes:
                for chapter in volume.chapters:
                    if chapter.id == chapter_id:
                        return chapter
        return None


class PlaceholderImageMapper:
    """
    占位符图片映射器
    
    在 HTML 生成时将占位符转换为实际 HTML 标签
    """
    
    def __init__(self, resolver: PlaceholderResolver, base_url: str = ""):
        self.resolver = resolver
        self.base_url = base_url
    
    def convert_to_html(
        self,
        text: str,
        chapter_id: str,
        image_url_formatter: Optional[Callable[[Path], str]] = None
    ) -> str:
        """
        将占位符转换为 HTML img 标签
        
        Args:
            text: Markdown 转换后的 HTML
            chapter_id: 章节 ID
            image_url_formatter: 自定义 URL 格式化函数
        """
        
        images = self.resolver.get_images_for_chapter(chapter_id)
        
        for idx, img in enumerate(images):
            placeholder = f"{{IMG:{chapter_id}_{idx}}}"
            
            if image_url_formatter:
                url = image_url_formatter(img.image_path)
            else:
                url = self._default_url_formatter(img.image_path)
            
            title = img.title or img.filename
            html_img = f'<img src="{url}" alt="{title}" title="{title}" class="placeholder-image" />'
            
            text = text.replace(placeholder, html_img)
        
        return text
    
    def _default_url_formatter(self, image_path: Path) -> str:
        """默认 URL 格式化：相对于 HTML 文件位置"""
        if self.base_url:
            # 如果指定了基础 URL，使用绝对路径
            return f"{self.base_url}/{image_path.name}"
        else:
            # 否则使用相对路径
            return f"../images/{image_path.name}"


class PlaceholderTextProcessor:
    """
    占位符文本处理器
    
    集成到 text_processor.py 中，处理 Markdown 文本
    """
    
    def __init__(self, config: ConfigV2, working_dir: Path = None):
        self.config = config
        self.working_dir = working_dir or Path(config.meta.working_dir)
        self.resolver = PlaceholderResolver(config, self.working_dir)
    
    def process(
        self,
        text: str,
        chapter_id: str = None,
        preserve_placeholders: bool = False
    ) -> str:
        """
        处理文本中的占位符
        
        Args:
            text: 输入文本（Markdown）
            chapter_id: 所属章节 ID
            preserve_placeholders: 是否保留占位符（True 则转为数据，False 则转为 Markdown/HTML）
        
        Returns:
            处理后的文本
        """
        
        if not self.config.meta.images.enabled:
            return text
        
        if preserve_placeholders:
            # 保留占位符，但验证它们有效
            return self._validate_placeholders(text)
        else:
            # 替换占位符
            return self.resolver.replace_placeholders(text, chapter_id=chapter_id)
    
    def _validate_placeholders(self, text: str) -> str:
        """验证占位符，移除无效的"""
        
        def validator(match):
            chapter_id = match.group(1)
            index = int(match.group(2))
            
            images = self.resolver.get_images_for_chapter(chapter_id)
            if index >= len(images):
                # 无效的占位符，移除或标记
                return f"[INVALID_IMG:{chapter_id}_{index}]"
            
            return match.group(0)
        
        return PlaceholderResolver.PLACEHOLDER_PATTERN.sub(validator, text)
    
    def extract_image_references(self, text: str) -> List[Dict]:
        """
        从文本中提取所有图片引用
        
        Returns:
            列表，每个元素为 {chapter_id, index, filename, path}
        """
        
        references = []
        
        for match in PlaceholderResolver.PLACEHOLDER_PATTERN.finditer(text):
            chapter_id = match.group(1)
            index = int(match.group(2))
            
            images = self.resolver.get_images_for_chapter(chapter_id)
            if index < len(images):
                img = images[index]
                references.append({
                    'chapter_id': chapter_id,
                    'index': index,
                    'filename': img.filename,
                    'path': str(img.image_path),
                })
        
        return references
