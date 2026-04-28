#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高层构建 API - 端到端数据 → HTML 构建

提供 build_from_data() 函数来简化整个构建流程，支持通过 Pattern 灵活指定
主文档、副文档和图片位置。
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from .config_v2 import ConfigV2, ConfigLoader
from ..cli.dispatcher import CommandDispatcher
from ..config.generator import StandardConfigGenerator, GeneratorOptions
from ..utils.path_utils import find_working_directory
from ..utils.image_utils import copy_images_from_config

logger = logging.getLogger(__name__)


@dataclass
class BuildOptions:
    """构建选项"""
    data_root: Path
    output_dir: Path
    book_id: str
    title: str = ""
    
    # 可选的 Pattern 覆盖（用于灵活指定文件位置）
    main_pattern: Optional[str] = None        # e.g., "vol_{volume}/{lang}/{chapter}.md"
    side_pattern: Optional[str] = None        # e.g., "vol_{volume}/{lang}/{chapter}.md"
    image_pattern: Optional[str] = None       # e.g., "images/{book_id}/vol_{volume}/{chapter}_*.jpg"
    
    # 可选的工作目录候选（用于目录发现）
    working_dir_candidates: Optional[List[str]] = None
    
    # 选项控制
    validate_config: bool = True              # 是否验证生成的 config
    copy_images: bool = True                  # 是否复制图片
    preserve_image_structure: bool = True     # 是否保留图片目录结构
    search_recursive_images: bool = False     # 是否递归搜索缺失的图片
    
    def __post_init__(self):
        """转换路径字符串为 Path 对象"""
        if isinstance(self.data_root, str):
            self.data_root = Path(self.data_root)
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)


@dataclass
class BuildResult:
    """构建结果"""
    success: bool
    config_file: Optional[Path] = None        # 生成的 config 文件
    output_dir: Optional[Path] = None         # 输出目录
    working_dir: Optional[Path] = None        # 工作目录
    images_copied: int = 0                    # 复制的图片数
    images_failed: int = 0                    # 失败的图片数
    errors: List[str] = None                  # 错误列表
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class PatternPathResolver:
    """
    Pattern 路径解析器
    
    支持占位符格式的路径 Pattern，自动展开为实际文件路径。
    支持 glob 通配符。
    
    示例：
        >>> resolver = PatternPathResolver(base_dir=Path("data"), book_id="2930")
        >>> resolver.expand_pattern(
        ...     "vol_{volume}/cn/{chapter}.md",
        ...     volume="001",
        ...     chapter="118359"
        ... )
        [PosixPath('data/vol_001/cn/118359.md')]
    """
    
    PLACEHOLDER_PATTERN = r'\{([^}]+)\}'
    
    def __init__(self, base_dir: Path, book_id: str):
        self.base_dir = Path(base_dir)
        self.book_id = book_id
    
    def expand_pattern(
        self,
        pattern: str,
        **context
    ) -> List[Path]:
        """
        展开 Pattern 并返回匹配的文件路径
        
        Args:
            pattern: Pattern 字符串，支持占位符 {volume}, {chapter}, {lang}, {book_id}
            **context: 占位符值，例如 volume="001", chapter="118359", lang="cn"
            
        Returns:
            匹配的文件路径列表（glob 通配符会返回所有匹配）
            
        示例：
            >>> resolver.expand_pattern(
            ...     "vol_{volume}/{lang}/{chapter}.md",
            ...     volume="001",
            ...     chapter="118359",
            ...     lang="cn"
            ... )
            [PosixPath('data/vol_001/cn/118359.md')]
            
            >>> resolver.expand_pattern(
            ...     "images/{book_id}/vol_{volume}/{chapter}_*.jpg",
            ...     volume="001",
            ...     chapter="118359"
            ... )
            [PosixPath('data/images/2930/vol_001/118359_1.jpg'),
             PosixPath('data/images/2930/vol_001/118359_2.jpg')]
        """
        import re
        
        # 自动添加 book_id 到 context（如果没有指定）
        if 'book_id' not in context:
            context['book_id'] = self.book_id
        
        # 替换所有占位符
        expanded = pattern
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            expanded = expanded.replace(placeholder, str(value))
        
        # 构造完整路径
        full_path = self.base_dir / expanded
        
        # 检查是否包含通配符
        if '*' in str(full_path) or '?' in str(full_path):
            # 使用 glob 查找匹配的文件
            parent = full_path.parent
            pattern_str = full_path.name
            
            if parent.exists():
                return sorted(parent.glob(pattern_str))
            else:
                return []
        else:
            # 直接返回路径（即使不存在）
            return [full_path]


class BuildExecutor:
    """构建执行器 - 负责构建流程的各个步骤"""
    
    def __init__(self, options: BuildOptions):
        self.options = options
        self.dispatcher = CommandDispatcher()
        self.config: Optional[ConfigV2] = None
        self.working_dir: Optional[Path] = None
    
    def execute(self) -> BuildResult:
        """执行完整的构建流程"""
        
        logger.info("=" * 70)
        logger.info("开始构建流程")
        logger.info("=" * 70)
        logger.info(f"数据根目录: {self.options.data_root.absolute()}")
        logger.info(f"输出目录: {self.options.output_dir.absolute()}")
        logger.info(f"书籍 ID: {self.options.book_id}")
        
        result = BuildResult(success=False, output_dir=self.options.output_dir)
        
        # 步骤 1: 发现工作目录
        if not self._step_find_working_dir(result):
            return result
        
        # 步骤 2: 生成 config
        if not self._step_generate_config(result):
            return result
        
        # 步骤 3: 验证 config（可选）
        if self.options.validate_config:
            if not self._step_validate_config(result):
                return result
        
        # 步骤 4: 生成 HTML
        if not self._step_generate_html(result):
            return result
        
        # 步骤 5: 复制图片（可选）
        if self.options.copy_images:
            if not self._step_copy_images(result):
                # 图片复制失败不影响整体成功（记录警告即可）
                logger.warning("[WARN] 图片复制步骤出错，但继续处理")
        
        result.success = True
        logger.info("\n" + "=" * 70)
        logger.info("[OK] 构建完成！")
        logger.info("=" * 70)
        logger.info(f"工作目录: {result.working_dir}")
        logger.info(f"输出位置: {result.output_dir}")
        logger.info(f"配置文件: {result.config_file}")
        if result.images_copied > 0:
            logger.info(f"复制图片: {result.images_copied} 张成功, {result.images_failed} 张失败")
        logger.info("=" * 70)
        
        return result
    
    def _step_find_working_dir(self, result: BuildResult) -> bool:
        """步骤 1: 发现工作目录"""
        logger.info("\n步骤 1: 发现工作目录")
        
        try:
            # 首先检查 data_root 是否存在
            if not self.options.data_root.exists():
                msg = f"数据根目录不存在: {self.options.data_root}"
                logger.error(f"[ERROR] {msg}")
                result.errors.append(msg)
                return False
            
            working_dir = find_working_directory(
                self.options.data_root,
                self.options.book_id,
                candidates=self.options.working_dir_candidates
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
        """步骤 2: 生成 config"""
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
                "output": str(config_file)
            }
            
            # 调用 dispatcher 生成 config
            self.dispatcher.dispatch(config_dict)
            
            # 加载生成的 config
            self.config = ConfigLoader.load_file(config_file)
            result.config_file = config_file
            
            logger.info(f"[OK] Config 已生成: {config_file}")
            logger.info(f"  - 作品: {len(self.config.works)}")
            for work in self.config.works:
                total_ch = sum(len(v.chapters) for v in work.volumes)
                logger.info(f"    - {work.title}: {len(work.volumes)} 卷, {total_ch} 章")
            
            return True
            
        except Exception as e:
            msg = f"生成配置文件时出错: {e}"
            logger.error(f"[ERROR] {msg}")
            import traceback
            traceback.print_exc()
            result.errors.append(msg)
            return False
    
    def _step_validate_config(self, result: BuildResult) -> bool:
        """步骤 3: 验证 config"""
        logger.info("\n步骤 3: 验证配置文件")
        
        try:
            is_valid, errors = ConfigLoader.validate(self.config, self.working_dir)
            
            if is_valid:
                logger.info("[OK] Config 验证通过")
                return True
            else:
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
        """步骤 4: 生成 HTML"""
        logger.info("\n步骤 4: 生成 HTML 输出")
        
        try:
            html_dict = {
                "mode": "book_index",
                "index": result.config_file,
                "output_dir": str(self.options.output_dir)
            }
            
            self.dispatcher.dispatch(html_dict)
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
        """步骤 5: 复制图片"""
        logger.info("\n步骤 5: 复制图片文件")
        
        try:
            copied, failed = copy_images_from_config(
                result.config_file,
                self.options.data_root,
                self.options.output_dir,
                preserve_structure=self.options.preserve_image_structure,
                search_recursive=self.options.search_recursive_images,
                overwrite=False
            )
            
            result.images_copied = copied
            result.images_failed = failed
            
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
    """
    端到端数据构建 API
    
    从数据目录生成配置、生成 HTML 和复制图片的完整流程。
    
    Args:
        options: 构建选项（BuildOptions 对象）
        
    Returns:
        BuildResult 对象，包含成功标志、输出文件和错误信息
        
    示例 - 基础用法：
        ```python
        from parallel_text_viewer.core.build import build_from_data, BuildOptions
        from pathlib import Path
        
        result = build_from_data(BuildOptions(
            data_root=Path("data"),
            output_dir=Path("output"),
            book_id="2930",
            title="My Novel"
        ))
        
        if result.success:
            print(f"构建成功！输出到: {result.output_dir}")
        else:
            print(f"构建失败: {result.errors}")
        ```
    
    示例 - 指定目录结构候选：
        ```python
        result = build_from_data(BuildOptions(
            data_root=Path("data"),
            output_dir=Path("output"),
            book_id="2930",
            working_dir_candidates=["my_novel", "novel_2930", "chapters/2930"]
        ))
        ```
    
    示例 - 跳过图片复制：
        ```python
        result = build_from_data(BuildOptions(
            data_root=Path("data"),
            output_dir=Path("output"),
            book_id="2930",
            copy_images=False  # 只生成 config 和 HTML，不复制图片
        ))
        ```
    """
    
    executor = BuildExecutor(options)
    return executor.execute()
