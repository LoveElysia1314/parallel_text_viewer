"""
模板渲染器 + 状态管理器

负责渲染 HTML 模板，支持变量替换。
模板内容从 html_templates/ 目录的独立文件中读取。
合并自: templates/renderer.py, templates/state_manager.py
"""

import html as html_module
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# ── 状态管理器 ──────────────────────────────────────────────

_cache: dict = {}


def _get_state_manager_js() -> str:
    """读取 state_manager.js 文件内容（带缓存）"""
    if "state_manager_js" not in _cache:
        js_path = Path(__file__).parent / "html_templates" / "state_manager.js"
        _cache["state_manager_js"] = js_path.read_text(encoding="utf-8")
    return _cache["state_manager_js"]


def get_state_manager_code(doc_id: str) -> str:
    """获取状态管理器代码，并替换文档 ID"""
    js = _get_state_manager_js()
    return js.replace("__DOC_ID__", doc_id)


# ── 模板渲染器 ──────────────────────────────────────────────


class TemplateRenderer:
    """模板渲染器"""

    _file_cache: Dict[str, str] = {}

    def __init__(self):
        self.html_dir = Path(__file__).parent / "html_templates"

    def _read_file(self, name: str) -> str:
        """读取模板文件（带缓存）"""
        if name not in self._file_cache:
            path = self.html_dir / name
            self._file_cache[name] = path.read_text(encoding="utf-8")
        return self._file_cache[name]

    def _assemble_chapter_html(self, state_manager_code: str) -> str:
        """组装章节页面 HTML"""
        common_css = self._read_file("common.css")
        chapter_css = self._read_file("chapter.css")
        common_js_raw = self._read_file("common.js")
        chapter_js = self._read_file("chapter.js")
        chapter_html = self._read_file("chapter.html")

        common_js = common_js_raw.replace("__STATE_MANAGER_CODE__", state_manager_code)

        html = chapter_html
        html = html.replace("{{COMMON_CSS}}", common_css)
        html = html.replace("{{CHAPTER_CSS}}", chapter_css)
        html = html.replace("{{COMMON_JS}}", common_js)
        html = html.replace("{{CHAPTER_JS}}", chapter_js)
        return html

    def _assemble_index_html(self, state_manager_code: str) -> str:
        """组装索引页面 HTML"""
        common_css = self._read_file("common.css")
        index_css = self._read_file("index.css")
        common_js_raw = self._read_file("common.js")
        index_js = self._read_file("index.js")
        index_html = self._read_file("index.html")

        common_js = common_js_raw.replace("__STATE_MANAGER_CODE__", state_manager_code)

        html = index_html
        html = html.replace("{{COMMON_CSS}}", common_css)
        html = html.replace("{{INDEX_CSS}}", index_css)
        html = html.replace("{{COMMON_JS}}", common_js)
        html = html.replace("{{INDEX_JS}}", index_js)
        return html

    def render_single_file(
        self,
        title: str,
        count: int,
        pairs_json: str,
        titles_json: str,
        state_manager_code: str,
        orientation: str,
    ) -> str:
        """渲染单文件模板"""
        html_out = self._assemble_chapter_html(state_manager_code)
        html_out = html_out.replace("__TITLE__", html_module.escape(title))
        html_out = html_out.replace("__COUNT__", str(count))
        html_out = html_out.replace("__PAIRS_JSON__", pairs_json)
        html_out = html_out.replace("__TITLES_JSON__", titles_json)
        html_out = html_out.replace("__ORIENTATION__", orientation)
        return html_out

    def render_chapter(
        self,
        title: str,
        count: int,
        pairs_json: str,
        titles_json: str,
        state_manager_code: str,
        orientation: str,
        nav_html: str,
        nav_info: Optional[Dict] = None,
    ) -> str:
        """渲染章节模板（包含导航）"""
        html_out = self._assemble_chapter_html(state_manager_code)
        html_out = html_out.replace("__TITLE__", html_module.escape(title))
        html_out = html_out.replace("__COUNT__", str(count))
        html_out = html_out.replace("__PAIRS_JSON__", pairs_json)
        html_out = html_out.replace("__TITLES_JSON__", titles_json)
        html_out = html_out.replace("__ORIENTATION__", orientation)

        if nav_info:
            html_out = html_out.replace(
                "__PREV_CHAPTER_URL__", nav_info.get("prev_chapter_url", "#")
            )
            html_out = html_out.replace(
                "__NEXT_CHAPTER_URL__", nav_info.get("next_chapter_url", "#")
            )
            html_out = html_out.replace("__PREV_VOLUME_URL__", nav_info.get("prev_volume_url", "#"))
            html_out = html_out.replace("__NEXT_VOLUME_URL__", nav_info.get("next_volume_url", "#"))
            html_out = html_out.replace("__INDEX_URL__", nav_info.get("index_url", "#"))

        header_end = html_out.find('<div class="header">')
        if header_end != -1:
            header_end = html_out.find("</div>", header_end) + 6
            html_out = html_out[:header_end] + nav_html + html_out[header_end:]

        return html_out

    def render_index(self, index_data: List[Dict[str, Any]]) -> str:
        """渲染索引模板"""
        index_json = json.dumps(index_data, ensure_ascii=False, sort_keys=True)
        doc_id = hashlib.sha1(index_json.encode("utf-8")).hexdigest()[:10]

        state_manager_code = get_state_manager_code(doc_id)
        index_data_json = json.dumps(index_data, ensure_ascii=False)

        html_out = self._assemble_index_html(state_manager_code)
        html_out = html_out.replace("__TITLE__", "Index")
        html_out = html_out.replace("__DESCRIPTION__", f"{len(index_data)} works")
        html_out = html_out.replace("__INDEX_DATA__", index_data_json)

        return html_out
