"""
图片路径处理工具

提供将相对或绝对图片路径转换为 HTML 文件相对路径的函数。
"""

import os
from pathlib import Path


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
