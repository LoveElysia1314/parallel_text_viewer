"""
文件工具

提供文件操作的实用函数。
"""

from pathlib import Path
from typing import Optional


def ensure_dir(path: Path) -> None:
    """确保目录存在，如果不存在则创建"""
    path.mkdir(parents=True, exist_ok=True)


def read_file_safe(file_path: Path, encoding: str = "utf-8") -> Optional[str]:
    """安全地读取文件内容"""
    try:
        return file_path.read_text(encoding=encoding)
    except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
        print(f"Warning: Failed to read {file_path}: {e}")
        return None