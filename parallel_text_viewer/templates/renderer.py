"""
模板渲染器

负责渲染HTML模板，支持变量替换。
"""

import html as html_module
from pathlib import Path
from typing import Dict, List, Any

from .chapter_template import CHAPTER_HTML_TEMPLATE
from .index_template import INDEX_HTML_TEMPLATE


class TemplateRenderer:
    """模板渲染器"""

    def __init__(self):
        self.templates_dir = Path(__file__).parent

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
        html_out = CHAPTER_HTML_TEMPLATE.replace("__TITLE__", html_module.escape(title))
        html_out = html_out.replace("__COUNT__", str(count))
        html_out = html_out.replace("__PAIRS_JSON__", pairs_json)
        html_out = html_out.replace("__TITLES_JSON__", titles_json)
        html_out = html_out.replace("__STATE_MANAGER_CODE__", state_manager_code)
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
        nav_info: Dict = None,
    ) -> str:
        """渲染章节模板（包含导航）"""
        html_out = CHAPTER_HTML_TEMPLATE.replace("__TITLE__", html_module.escape(title))
        html_out = html_out.replace("__COUNT__", str(count))
        html_out = html_out.replace("__PAIRS_JSON__", pairs_json)
        html_out = html_out.replace("__TITLES_JSON__", titles_json)
        html_out = html_out.replace("__STATE_MANAGER_CODE__", state_manager_code)
        html_out = html_out.replace("__ORIENTATION__", orientation)

        if nav_info:
            html_out = html_out.replace("__PREV_CHAPTER_URL__", nav_info.get("prev_chapter_url", "#"))
            html_out = html_out.replace("__NEXT_CHAPTER_URL__", nav_info.get("next_chapter_url", "#"))
            html_out = html_out.replace("__PREV_VOLUME_URL__", nav_info.get("prev_volume_url", "#"))
            html_out = html_out.replace("__NEXT_VOLUME_URL__", nav_info.get("next_volume_url", "#"))
            html_out = html_out.replace("__INDEX_URL__", nav_info.get("index_url", "#"))

        # 在header后插入导航
        header_end = html_out.find('<div class="header">')
        if header_end != -1:
            header_end = html_out.find("</div>", header_end) + 6
            html_out = html_out[:header_end] + nav_html + html_out[header_end:]

        return html_out

    def render_index(self, index_data: List[Dict[str, Any]]) -> str:
        """渲染索引模板"""
        # 为索引页面生成文档ID
        import hashlib
        import json
        index_json = json.dumps(index_data, ensure_ascii=False, sort_keys=True)
        doc_id = hashlib.sha1(index_json.encode("utf-8")).hexdigest()[:10]

        # 获取状态管理器代码
        from .state_manager import get_state_manager_code
        state_manager_code = get_state_manager_code(doc_id)

        # 准备索引数据
        index_data_json = json.dumps(index_data, ensure_ascii=False)

        html_out = INDEX_HTML_TEMPLATE.replace("__TITLE__", "Index")
        html_out = html_out.replace("__DESCRIPTION__", f"{len(index_data)} works")
        html_out = html_out.replace("__STATE_MANAGER_CODE__", state_manager_code)
        html_out = html_out.replace("__INDEX_DATA__", index_data_json)

        return html_out