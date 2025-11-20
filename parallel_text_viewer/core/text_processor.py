"""
文本处理模块

提供文本读取、解析和行对齐功能。
"""

from pathlib import Path
import re
from typing import Optional, List, Tuple


def parse_lines(path: Path, ignore_empty: bool = True) -> list[str]:
    """
    从文件读取并解析行。

    Args:
        path: 输入文件路径
        ignore_empty: 是否忽略空白行（默认 True）

    Returns:
        处理后的行列表。若 ignore_empty=True，会移除空行并统一添加 4 空格缩进。
    """
    s = path.read_text(encoding="utf-8")
    lines = s.splitlines()
    if ignore_empty:
        lines = [l for l in lines if l.strip() != ""]
        # 去除行首空格后统一缩进 4 个空格
        lines = ["    " + l.lstrip() for l in lines]
    return lines


def parse_md_lines(
    path: Path,
    ignore_empty: bool = True,
    base_path: Optional[Path] = None
) -> Tuple[Optional[str], List[str]]:
    """
    从MD文件读取并解析行，提取标题。

    Args:
        path: 输入文件路径
        ignore_empty: 是否忽略空白行（默认 True）
        base_path: 基础路径，用于解析相对图片路径

    Returns:
        (标题, 处理后的行列表)。标题为None如果没有。
    """
    s = path.read_text(encoding="utf-8")
    lines = s.splitlines()
    
    title = None
    if lines and lines[0].strip().startswith("#"):
        # 提取标题
        title_match = re.match(r'^#\s*(.+)', lines[0].strip())
        if title_match:
            title = title_match.group(1).strip()
        lines = lines[1:]  # 移除标题行
    
    # 处理图片链接 - 将Markdown语法转换为HTML img标签
    processed_lines = []
    for line in lines:
        # 替换 ![alt](url) 为 <img src="url" alt="alt">
        def replace_image(match):
            alt_text = match.group(1)
            img_path = match.group(2)
            # 清理和规范化图片路径
            img_path = img_path.strip()
            # 只保留文件名，忽略原始路径 —— 方便在生成阶段根据配置映射到 output/images
            try:
                from pathlib import Path as _P
                img_basename = _P(img_path).name
            except Exception:
                img_basename = img_path
            return f'<img src="{img_basename}" alt="{alt_text}">'
        
        # 处理标准Markdown图片语法 ![alt](url)
        line = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace_image, line)
        
        # 处理可能的其他图片格式，如 <img> 标签或其他变体
        # 这里可以添加更多处理逻辑，如果需要
        
        processed_lines.append(line)
    
    if ignore_empty:
        processed_lines = [l for l in processed_lines if l.strip() != ""]
        # 去除行首空格后统一缩进 4 个空格
        processed_lines = ["    " + l.lstrip() for l in processed_lines]
    return title, processed_lines


def validate_line_counts(
    main_lines: list[str],
    side_lines: list[str],
    main_identifier: Optional[str] = None,
    side_identifier: Optional[str] = None,
) -> tuple[list[str], list[str]]:
    """
    验证并对齐主从文档的行数。

    若行数不一致，会用空字符串填充短的一侧。
    在统计行数前会过滤掉空行。

    Args:
        main_lines: 主文档行列表
        side_lines: 从文档行列表
        main_identifier: 可选，主文档的标识（文件路径或名称），用于调试输出
        side_identifier: 可选，从文档的标识（文件路径或名称），用于调试输出

    Returns:
        对齐后的 (main_lines, side_lines) 元组
    """
    # 在统计行数前过滤空行（只包含空白字符的行）
    filtered_main_lines = [line for line in main_lines if line.strip()]
    filtered_side_lines = [line for line in side_lines if line.strip()]

    if len(filtered_main_lines) != len(filtered_side_lines):
        m_id = main_identifier if main_identifier else '<main>'
        s_id = side_identifier if side_identifier else '<side>'
        print(
            f"Warning: different line counts: main={len(filtered_main_lines)} side={len(filtered_side_lines)} file_main={m_id} file_side={s_id}"
        )
        # 填充较短的一侧
        if len(filtered_main_lines) < len(filtered_side_lines):
            main_lines += [""] * (len(filtered_side_lines) - len(filtered_main_lines))
        else:
            side_lines += [""] * (len(filtered_main_lines) - len(filtered_side_lines))
        print(f"Padded to {len(main_lines)} lines (identifiers: {m_id}, {s_id}).")
    return main_lines, side_lines
