"""
工具函数

提供文件、图片、路径处理的实用函数。
合并自：file_utils.py, image_utils.py, path_utils.py
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Tuple, List, Iterable, Optional, Dict, Any

logger = logging.getLogger(__name__)


# ── file_utils ──────────────────────────────────────────────


def ensure_dir(path: Path) -> None:
    """确保目录存在，如果不存在则创建"""
    path.mkdir(parents=True, exist_ok=True)


def read_file_safe(file_path: Path, encoding: str = "utf-8") -> Optional[str]:
    """安全地读取文件内容"""
    try:
        return file_path.read_text(encoding=encoding)
    except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
        logger.warning("Failed to read %s: %s", file_path, e)
        return None


# ── path_utils ──────────────────────────────────────────────


def resolve_path(base_path: Path, relative_path: str) -> Path:
    """解析相对路径为绝对路径"""
    path = Path(relative_path)
    if path.is_absolute():
        return path
    return base_path / path


def find_working_directory(
    data_root: Path, book_id: str, candidates: Optional[List[str]] = None
) -> Optional[Path]:
    """
    查找工作目录（包含章节文件的目录）

    按优先级尝试多个候选位置。如果目录中含有 vol_* 子目录，优先返回该目录。

    Args:
        data_root: 数据根目录
        book_id: 书籍 ID
        candidates: 自定义候选路径列表（默认为推荐结构）

    Returns:
        找到的工作目录路径，若全部不存在则返回 None
    """
    data_root = Path(data_root)

    # 默认候选位置（按优先级排序）
    if candidates is None:
        candidates = [
            f"novel_{book_id}",  # 1. novel_<book_id>
            book_id,  # 2. <book_id>
            f"chapters/{book_id}",  # 3. chapters/<book_id>
            ".",  # 4. 直接在 data_root
        ]

    # 尝试每个候选位置
    for candidate in candidates:
        candidate_path = data_root / candidate
        if not candidate_path.exists():
            continue

        # 检查是否有卷目录 (vol_*)
        vol_dirs = list(candidate_path.glob("vol_*"))
        if vol_dirs:
            return candidate_path.resolve()

    # 如果没有找到含 vol_* 的目录，返回第一个存在的候选
    for candidate in candidates:
        candidate_path = data_root / candidate
        if candidate_path.exists():
            return candidate_path.resolve()

    return None


# ── image_utils ─────────────────────────────────────────────


def compute_relative_image_path(html_output_path: Path, image_abs_path: Path) -> str:
    """
    计算从 HTML 文件到图片文件的相对路径。
    """
    try:
        html_dir = html_output_path.parent
        rel = os.path.relpath(str(image_abs_path), start=str(html_dir))
        return rel.replace("\\", "/")
    except (ValueError, TypeError):
        return image_abs_path.as_posix()


def resolve_image_path(base_dir: Path, image_ref: str, base_image_path: str = None) -> Path:
    """
    解析配置中的图片路径。

    支持：相对路径、绝对路径、URL（返回原样）
    """
    if image_ref.startswith(("http://", "https://")):
        return image_ref

    if Path(image_ref).is_absolute():
        return Path(image_ref)

    if base_image_path:
        base_img_path = base_dir / base_image_path
        return (base_img_path / image_ref).resolve()
    else:
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
        (成功复制数, 失败数)
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

            if preserve_structure:
                try:
                    rel_path = source_path.relative_to(data_root)
                    dest_path = output_dir / rel_path
                except ValueError:
                    dest_path = output_dir / source_path.name
            else:
                dest_path = output_dir / source_path.name

            if not dry_run:
                dest_path.parent.mkdir(parents=True, exist_ok=True)

            if dest_path.exists() and not overwrite:
                logger.debug(f"跳过已存在的文件: {dest_path}")
                continue

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
        (成功复制数, 失败数)
    """
    import json

    config_path = Path(config_path)
    data_root = Path(data_root)
    output_dir = Path(output_dir)

    if not config_path.exists():
        logger.warning(f"配置文件不存在: {config_path}")
        return 0, 0

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        logger.error(f"读取配置文件失败: {e}")
        return 0, 0

    images_to_copy: Dict[str, Path] = {}

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
                            source_path = data_root / img_filename
                            if source_path.exists():
                                images_to_copy[img_filename] = source_path
                            elif search_recursive:
                                filename = Path(img_filename).name
                                matches = list(data_root.rglob(filename))
                                if matches:
                                    images_to_copy[img_filename] = matches[0]
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

    return copy_files(
        images_to_copy.values(),
        data_root,
        output_dir,
        preserve_structure=preserve_structure,
        overwrite=overwrite,
        dry_run=dry_run,
    )
