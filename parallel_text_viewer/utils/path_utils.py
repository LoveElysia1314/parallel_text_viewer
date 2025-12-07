"""
路径工具

提供路径处理的实用函数。
"""

from pathlib import Path
from typing import Optional, List


def resolve_path(base_path: Path, relative_path: str) -> Path:
    """解析相对路径为绝对路径"""
    path = Path(relative_path)
    if path.is_absolute():
        return path
    return base_path / path


def find_working_directory(
    data_root: Path,
    book_id: str,
    candidates: Optional[List[str]] = None
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
        
    示例：
        >>> find_working_directory(Path("data"), "2930")
        PosixPath('data/novel_2930')  # 若该目录存在且含 vol_* 子目录
    """
    data_root = Path(data_root)
    
    # 默认候选位置（按优先级排序）
    if candidates is None:
        candidates = [
            f"novel_{book_id}",      # 1. novel_<book_id>
            book_id,                  # 2. <book_id>
            f"chapters/{book_id}",    # 3. chapters/<book_id>
            ".",                      # 4. 直接在 data_root
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