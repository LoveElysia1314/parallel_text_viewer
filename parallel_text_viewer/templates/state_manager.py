"""
状态管理器 - HTML 状态保留的 JavaScript 代码生成

负责生成 JavaScript 代码来管理和持久化用户界面状态。
状态管理器代码从独立文件 templates/html/state_manager.js 中读取。
"""

from pathlib import Path

# 缓存文件内容，避免每次读取
_cache: dict = {}


def _get_state_manager_js() -> str:
    """读取 state_manager.js 文件内容（带缓存）"""
    if "state_manager_js" not in _cache:
        js_path = Path(__file__).parent / "html" / "state_manager.js"
        _cache["state_manager_js"] = js_path.read_text(encoding="utf-8")
    return _cache["state_manager_js"]


def get_state_manager_code(doc_id: str) -> str:
    """
    获取状态管理器代码，并替换文档 ID

    Args:
        doc_id: 文档 ID（SHA1 hash）

    Returns:
        替换后的 JavaScript 代码
    """
    js = _get_state_manager_js()
    return js.replace("__DOC_ID__", doc_id)
