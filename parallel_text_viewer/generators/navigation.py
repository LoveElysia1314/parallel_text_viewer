"""
导航生成器

负责生成章节导航HTML。
"""

from typing import Dict


class NavigationGenerator:
    """导航HTML生成器"""

    def generate_navigation(self, nav_info: Dict) -> str:
        """生成导航HTML"""
        html = f"""
        <!-- Breadcrumb navigation -->
        <div class="breadcrumb">
            <a href="{nav_info['index_url']}">Index</a> &gt;
            <span>{nav_info['work_title']}</span> &gt;
            <span>{nav_info['volume_title']}</span> &gt;
            <span>{nav_info['chapter_title']}</span>
        </div>
        """
        return html