"""
路径推导引擎

根据 config 中的规则自动推导文件路径和图片位置
"""

from pathlib import Path
from typing import Tuple, Optional, List, Dict
import re
from .config_v2 import Chapter, ConfigV2, StructureConfig, ImageAssociationParams


class PathResolver:
    """路径解析器"""
    
    def __init__(self, working_dir: Path = None):
        """初始化
        
        Args:
            working_dir: 工作目录，所有相对路径的基准
        """
        self.working_dir = Path(working_dir) if working_dir else Path.cwd()
        self._cache = {}  # 缓存已解析的路径
    
    def resolve_chapter_files(
        self,
        chapter: Chapter,
        structure: StructureConfig,
        volume_id: str,
    ) -> Tuple[Optional[Path], Optional[Path]]:
        """
        推导章节的 main_file 和 side_file
        
        Args:
            chapter: 章节对象
            structure: 文件结构配置
            volume_id: 卷 ID
        
        Returns:
            (main_file, side_file) 的绝对路径，如果推导失败返回 None
        
        推导规则：
            {working_dir} / {volume_pattern} / {lang} / {chapter_id}.md
        
        示例：
            working_dir = "."
            volume_pattern = "vol_{:03d}"
            volume_id = "vol_001"
            chapter_id = "118227"
            langs = {"main": "cn", "side": "en"}
            
            → ./vol_001/cn/118227.md
            → ./vol_001/en/118227.md
        """
        # 如果已显式指定文件，直接返回
        if chapter.main_file or chapter.side_file:
            main_file = Path(chapter.main_file) if chapter.main_file else None
            side_file = Path(chapter.side_file) if chapter.side_file else None
            
            # 转为绝对路径
            if main_file and not main_file.is_absolute():
                main_file = self.working_dir / main_file
            if side_file and not side_file.is_absolute():
                side_file = self.working_dir / side_file
            
            return main_file, side_file
        
        # 如果有缓存，返回缓存
        cache_key = (volume_id, chapter.id)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # 推导卷目录
        vol_dir = self._derive_volume_directory(volume_id, structure)
        
        # 推导文件名
        chapter_filename = f"{chapter.id}.md"
        
        # 获取语言配置
        main_lang = structure.languages.get("main", "cn")
        side_lang = structure.languages.get("side", "en")
        
        # 构造路径
        main_file = self.working_dir / vol_dir / main_lang / chapter_filename
        side_file = self.working_dir / vol_dir / side_lang / chapter_filename
        
        # 缓存结果
        result = (main_file, side_file)
        self._cache[cache_key] = result
        
        return result
    
    def _derive_volume_directory(self, volume_id: str, structure: StructureConfig) -> str:
        """推导卷目录名"""
        pattern = structure.volume_pattern
        
        # 如果 volume_id 已经包含 "vol_"，直接使用
        if volume_id.startswith("vol_"):
            return volume_id
        
        # 否则根据 pattern 构造
        # pattern 格式: "vol_{:03d}" 或 "vol_{}" 等
        try:
            # 尝试从 ID 提取数字
            if volume_id.isdigit():
                num = int(volume_id)
                return pattern.format(num)
            else:
                # 如果不是纯数字，尝试其他方式
                return volume_id
        except:
            return volume_id
    
    def resolve_chapter_images(
        self,
        chapter_id: str,
        image_root: Path,
        strategy: str,
        params: ImageAssociationParams,
    ) -> List[Path]:
        """
        推导章节对应的图片文件列表
        
        Args:
            chapter_id: 章节 ID
            image_root: 图片根目录
            strategy: 关联策略 (directory / filename / custom)
            params: 策略参数
        
        Returns:
            图片文件列表
        """
        if not image_root.exists():
            return []
        
        cache_key = (chapter_id, str(image_root), strategy)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        images = []
        
        if strategy == "directory":
            # 策略：按目录名关联
            # 假设目录结构：images/vol_001/118227/
            chapter_dir = image_root / chapter_id
            if chapter_dir.is_dir():
                images = sorted(list(chapter_dir.glob("*")))
        
        elif strategy == "filename":
            # 策略：按文件名模式关联
            pattern = params.filename_pattern or "{chapter_id}_*.jpg"
            pattern = pattern.replace("{chapter_id}", chapter_id)
            
            images = sorted(list(image_root.glob(pattern)))
        
        elif strategy == "custom":
            # 策略：自定义映射
            rel_path = params.mappings.get(chapter_id)
            if rel_path:
                path = image_root / rel_path
                if path.is_file():
                    images = [path]
                elif path.is_dir():
                    images = sorted(list(path.glob("*")))
                else:
                    # 尝试 glob
                    parent = image_root / Path(rel_path).parent
                    if parent.exists():
                        images = sorted(parent.glob(Path(rel_path).name))
        
        # 缓存结果
        self._cache[cache_key] = images
        
        return images
    
    def compute_relative_path(
        self,
        from_file: Path,
        to_file: Path,
    ) -> str:
        """
        计算从一个文件到另一个文件的相对路径
        
        Args:
            from_file: 源文件（通常是输出的 HTML 文件）
            to_file: 目标文件（通常是图片或资源文件）
        
        Returns:
            相对路径字符串（使用 / 作为分隔符）
        """
        try:
            rel = to_file.relative_to(from_file.parent)
            # 转换为使用 / 的路径
            return rel.as_posix()
        except ValueError:
            # 如果无法计算相对路径（如在不同驱动器上），返回绝对路径
            return to_file.as_posix()
    
    def clear_cache(self):
        """清除缓存"""
        self._cache.clear()


class PathNormalizer:
    """路径规范化器"""
    
    @staticmethod
    def normalize_path(path: str) -> str:
        """
        规范化路径
        
        - 统一使用 / 作为分隔符
        - 移除重复的 /
        - 简化 ../
        """
        # 转换为 Path 对象处理
        p = Path(path)
        # 再转回字符串，使用 posix 格式
        return p.as_posix()
    
    @staticmethod
    def resolve_path_with_vars(
        path_template: str,
        variables: Dict[str, str],
    ) -> str:
        """
        从模板和变量解析路径
        
        Args:
            path_template: 包含变量的路径模板，如 "chapters/{book_id}/vol_{volume_id}/"
            variables: 变量字典，如 {"book_id": "2930", "volume_id": "001"}
        
        Returns:
            解析后的路径
        """
        result = path_template
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", value)
        return result


class VolumePatternParser:
    """卷目录名模式解析器"""
    
    @staticmethod
    def parse_volume_id_from_dir(dir_name: str, pattern: str) -> Optional[str]:
        """
        从目录名解析卷 ID
        
        Args:
            dir_name: 目录名，如 "vol_001"
            pattern: 模式，如 "vol_{:03d}"
        
        Returns:
            卷 ID，如 "001" 或 "1"
        """
        # 将 Python 格式的模式转换为正则表达式
        # "vol_{:03d}" → "vol_(\d{3})"
        regex_pattern = pattern.replace("{:03d}", r"(\d{3})")
        regex_pattern = regex_pattern.replace("{}", r"(\d+)")
        regex_pattern = f"^{regex_pattern}$"
        
        match = re.match(regex_pattern, dir_name)
        if match:
            return match.group(1)
        return None
    
    @staticmethod
    def generate_volume_dir_name(volume_id: str, pattern: str) -> str:
        """
        根据卷 ID 和模式生成目录名
        
        Args:
            volume_id: 卷 ID，如 "1" 或 "001"
            pattern: 模式，如 "vol_{:03d}"
        
        Returns:
            目录名，如 "vol_001"
        """
        # 将 Python 格式的模式转换为可用的参数
        if "{:03d}" in pattern:
            # 需要 3 位数字
            num = int(volume_id) if volume_id.isdigit() else 1
            return pattern.format(num)
        elif "{}" in pattern:
            # 可变位数
            return pattern.format(volume_id)
        else:
            return pattern
