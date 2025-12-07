"""
图片路径处理工具

提供将相对或绝对图片路径转换为 HTML 文件相对路径的函数。
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Tuple, List, Iterable, Optional, Dict, Any

# 获取日志记录器
logger = logging.getLogger(__name__)


def compute_relative_image_path(html_output_path: Path, image_abs_path: Path) -> str:
    """
    计算从 HTML 文件到图片文件的相对路径。
    
    用于在生成 HTML 时替换 <img src="..."> 的值，确保无论输出目录如何组织，
    图片都能被正确引用。
    
    Args:
        html_output_path: 输出的 HTML 文件的完整路径
        image_abs_path: 图片文件的完整（绝对）路径
    
    Returns:
        相对于 HTML 文件所在目录的相对路径（POSIX 格式，使用 /）
    
    示例：
        >>> html_path = Path("output/vol_001/ch01.html")
        >>> img_path = Path("data/images/2930/vol_001/ch01/001.jpg")
        >>> compute_relative_image_path(html_path, img_path)
        '../../data/images/2930/vol_001/ch01/001.jpg'
    """
    try:
        # 使用 os.path.relpath 计算相对路径
        html_dir = html_output_path.parent
        rel = os.path.relpath(str(image_abs_path), start=str(html_dir))
        # 转换为 POSIX 格式（使用 /）
        return rel.replace('\\', '/')
    except (ValueError, TypeError):
        # fallback：返回绝对路径的 POSIX 格式
        return image_abs_path.as_posix()


def resolve_image_path(base_dir: Path, image_ref: str, base_image_path: str = None) -> Path:
    """
    解析配置中的图片路径。
    
    支持三种输入格式：
    1. 相对路径（相对于 base_image_path 或 base_dir）
    2. 绝对路径
    3. URL（返回原样）
    
    Args:
        base_dir: 配置文件所在的目录
        image_ref: 配置中的 images[].filename
        base_image_path: 来自 meta.base_image_path 的值
    
    Returns:
        图片的绝对路径（Path 对象）或 URL（str）
    
    示例：
        >>> base_dir = Path("demo/")
        >>> image_ref = "vol_001/001.jpg"
        >>> base_image_path = "data/images/2930/"
        >>> resolve_image_path(base_dir, image_ref, base_image_path)
        PosixPath('data/images/2930/vol_001/001.jpg')
    """
    # 如果是 URL，直接返回
    if image_ref.startswith(("http://", "https://")):
        return image_ref
    
    # 如果是绝对路径，直接返回
    if Path(image_ref).is_absolute():
        return Path(image_ref)
    
    # 相对路径处理
    if base_image_path:
        # 优先基于 base_image_path
        base_img_path = base_dir / base_image_path
        return (base_img_path / image_ref).resolve()
    else:
        # fallback：基于 base_dir
        return (base_dir / image_ref).resolve()


def copy_files(
    sources: Iterable[Path],
    data_root: Path,
    output_dir: Path,
    *,
    preserve_structure: bool = True,
    overwrite: bool = False,
    dry_run: bool = False,
) -> Tuple[int, int]:
    """
    复制多个文件到输出目录
    
    Args:
        sources: 源文件路径列表
        data_root: 数据根目录（用于计算相对路径）
        output_dir: 输出目录
        preserve_structure: 是否保留原目录结构
        overwrite: 是否覆盖已存在的文件
        dry_run: 只计算，不实际复制
        
    Returns:
        Tuple[int, int]: (成功复制数, 失败数)
        
    示例：
        >>> sources = [Path("data/images/2930/vol_001/001.jpg")]
        >>> copy_files(sources, Path("data"), Path("output"), preserve_structure=True)
        (1, 0)
    """
    data_root = Path(data_root)
    output_dir = Path(output_dir)
    
    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
    
    copied = 0
    failed = 0
    
    for source_path in sources:
        source_path = Path(source_path)
        
        try:
            if not source_path.exists():
                logger.warning(f"源文件不存在: {source_path}")
                failed += 1
                continue
            
            # 计算目标路径
            if preserve_structure:
                try:
                    # 计算相对路径
                    rel_path = source_path.relative_to(data_root)
                    dest_path = output_dir / rel_path
                except ValueError:
                    # 如果 source_path 不在 data_root 下，直接使用文件名
                    dest_path = output_dir / source_path.name
            else:
                dest_path = output_dir / source_path.name
            
            # 创建目标目录（仅在 dry_run=False 时创建）
            if not dry_run:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 检查目标文件是否已存在
            if dest_path.exists() and not overwrite:
                logger.debug(f"跳过已存在的文件: {dest_path}")
                continue
            
            # 复制文件
            if not dry_run:
                shutil.copy2(source_path, dest_path)
            
            logger.debug(f"复制: {source_path} -> {dest_path}")
            copied += 1
            
        except Exception as e:
            logger.error(f"复制失败 {source_path}: {e}")
            failed += 1
    
    return copied, failed


def copy_images_from_config(
    config_path: Path,
    data_root: Path,
    output_dir: Path,
    *,
    preserve_structure: bool = True,
    search_recursive: bool = False,
    overwrite: bool = False,
    dry_run: bool = False,
) -> Tuple[int, int]:
    """
    根据 ConfigV2 配置文件复制图片到输出目录
    
    Args:
        config_path: 配置文件路径
        data_root: 数据根目录（从中查找图片）
        output_dir: 输出目录（复制到此处）
        preserve_structure: 是否保留原目录结构
        search_recursive: 如果图片路径不存在，是否递归搜索
        overwrite: 是否覆盖已存在的文件
        dry_run: 只计算，不实际复制
        
    Returns:
        Tuple[int, int]: (成功复制数, 失败数)
        
    示例：
        >>> config_path = Path("output/config.json")
        >>> copy_images_from_config(
        ...     config_path,
        ...     Path("data"),
        ...     Path("output"),
        ...     preserve_structure=True
        ... )
        (42, 0)
    """
    import json
    
    config_path = Path(config_path)
    data_root = Path(data_root)
    output_dir = Path(output_dir)
    
    # 读取配置
    if not config_path.exists():
        logger.warning(f"配置文件不存在: {config_path}")
        return 0, 0
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        logger.error(f"读取配置文件失败: {e}")
        return 0, 0
    
    # 收集所有图片文件
    images_to_copy: Dict[str, Path] = {}  # {相对路径: 源路径}
    
    try:
        works = config.get("works", [])
        for work in works:
            volumes = work.get("volumes", [])
            for volume in volumes:
                chapters = volume.get("chapters", [])
                for chapter in chapters:
                    chapter_images = chapter.get("images", {})
                    if chapter_images:
                        files = chapter_images.get("files", [])
                        for img_ref in files:
                            img_filename = img_ref.get("filename")
                            if not img_filename:
                                continue
                            
                            # 尝试从 data_root 查找源文件
                            source_path = data_root / img_filename
                            
                            if source_path.exists():
                                images_to_copy[img_filename] = source_path
                            elif search_recursive:
                                # 递归搜索
                                filename = Path(img_filename).name
                                matches = list(data_root.rglob(filename))
                                if matches:
                                    images_to_copy[img_filename] = matches[0]
                                    logger.debug(f"递归找到: {filename} -> {matches[0]}")
                                else:
                                    logger.debug(f"图片未找到 (递归): {img_filename}")
                            else:
                                logger.debug(f"图片未找到: {img_filename}")
    except Exception as e:
        logger.error(f"解析配置文件失败: {e}")
        return 0, 0
    
    logger.info(f"发现 {len(images_to_copy)} 张图片")
    
    if not images_to_copy:
        logger.info("无图片需要复制")
        return 0, 0
    
    # 复制图片
    return copy_files(
        images_to_copy.values(),
        data_root,
        output_dir,
        preserve_structure=preserve_structure,
        overwrite=overwrite,
        dry_run=dry_run,
    )
