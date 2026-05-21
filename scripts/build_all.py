#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量构建脚本 — 一键构建 data/ 下所有作品

扫描 data/catalogs/ 下的所有 catalog JSON 文件来确定可用的 book_id，
然后逐一调用 build_from_data 进行构建。

用法：
    python scripts/build_all.py                           # 构建所有作品
    python scripts/build_all.py --books 2580 2930          # 仅构建指定作品
    python scripts/build_all.py --output-dir output        # 指定输出根目录
    python scripts/build_all.py --no-images                # 跳过图片复制
    python scripts/build_all.py --serve                    # 构建完成后启动本地服务器
"""

import sys
import os
import json
import logging
import argparse
from pathlib import Path

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", encoding="utf-8"
)
logger = logging.getLogger(__name__)


def discover_books(data_root: Path) -> list:
    """从 catalogs/ 和 chapters/ 发现可用的 book_id"""
    books = set()

    # 从 catalogs/*.json 发现
    catalogs_dir = data_root / "catalogs"
    if catalogs_dir.exists():
        for f in catalogs_dir.glob("*.json"):
            book_id = f.stem
            if book_id.isdigit():
                books.add(book_id)

    # 从 chapters/* 发现
    chapters_dir = data_root / "chapters"
    if chapters_dir.exists():
        for d in chapters_dir.iterdir():
            if d.is_dir() and d.name.isdigit():
                books.add(d.name)

    # 从 novel_* 发现
    for d in data_root.iterdir():
        if d.is_dir() and d.name.startswith("novel_") and d.name[5:].isdigit():
            books.add(d.name[5:])

    return sorted(books, key=int)


def main():
    parser = argparse.ArgumentParser(description="并行文本查看器 — 批量构建工具")
    parser.add_argument(
        "--data-root", type=str, default="data", help="数据根目录（默认 data）"
    )
    parser.add_argument(
        "--output-dir", type=str, default="output", help="输出根目录（默认 output）"
    )
    parser.add_argument(
        "--books",
        type=str,
        nargs="+",
        help="要构建的 book_id 列表（默认自动发现所有作品）",
    )
    parser.add_argument("--no-images", action="store_true", help="跳过图片复制")
    parser.add_argument("--no-validate", action="store_true", help="跳过配置验证")
    parser.add_argument("--serve", "-s", action="store_true", help="构建完成后启动本地服务器")
    parser.add_argument("--serve-port", type=int, default=8080, help="本地服务器端口（默认 8080）")
    args = parser.parse_args()

    # 切换到项目根目录
    project_root = Path(__file__).resolve().parents[1]
    try:
        os.chdir(project_root)
    except Exception:
        pass

    data_root = Path(args.data_root)
    if not data_root.is_absolute():
        data_root = project_root / data_root

    output_root = Path(args.output_dir)
    if not output_root.is_absolute():
        output_root = project_root / output_root

    # 发现作品列表
    if args.books:
        book_ids = args.books
    else:
        book_ids = discover_books(data_root)

    if not book_ids:
        logger.error(f"在 {data_root} 中未发现任何作品！")
        return 1

    logger.info("=" * 70)
    logger.info(f"批量构建工具 — 发现 {len(book_ids)} 部作品")
    logger.info("=" * 70)

    for book_id in book_ids:
        logger.info(f"\n{'─' * 50}")
        logger.info(f"开始构建作品 {book_id}")
        logger.info(f"{'─' * 50}")

        try:
            from parallel_text_viewer.core import build_from_data, BuildOptions

            result = build_from_data(
                BuildOptions(
                    data_root=data_root,
                    output_dir=output_root,
                    book_id=book_id,
                    validate_config=not args.no_validate,
                    copy_images=not args.no_images,
                    preserve_image_structure=True,
                    search_recursive_images=False,
                )
            )

            if result.success:
                logger.info(f"  ✓ 作品 {book_id} 构建成功 → {result.output_dir}")
            else:
                logger.error(f"  ✗ 作品 {book_id} 构建失败")
                for error in result.errors:
                    logger.error(f"    - {error}")

        except Exception as e:
            logger.error(f"  ✗ 作品 {book_id} 构建异常: {e}")
            import traceback

            traceback.print_exc()

    logger.info(f"\n{'=' * 70}")
    logger.info(f"批量构建完成！输出目录: {output_root}")
    logger.info(f"{'=' * 70}")

    # 生成索引页面（列出所有作品）
    _generate_master_index(output_root, book_ids)

    if args.serve:
        _start_server(output_root, args.serve_port)

    return 0


def _generate_master_index(output_root: Path, book_ids: list):
    """生成一个汇总索引页面，列出所有已构建的作品"""
    index_html = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>轻小说文库 — 本地镜像</title>
<style>
  body { font-family: system-ui, -apple-system, sans-serif; max-width: 800px;
         margin: 0 auto; padding: 40px 20px; background: #0f1724; color: #e6eef8; }
  h1 { font-size: 1.8em; margin-bottom: 8px; }
  p { color: #94a3b8; margin-bottom: 32px; }
  ul { list-style: none; padding: 0; }
  li { margin: 12px 0; }
  a { display: block; padding: 16px 20px; background: rgba(255,255,255,0.03);
      border: 1px solid rgba(255,255,255,0.06); border-radius: 8px;
      color: #e6eef8; text-decoration: none; font-size: 1.1em;
      transition: background 0.2s, border-color 0.2s; }
  a:hover { background: rgba(96,165,250,0.1); border-color: #60a5fa; }
  .book-id { font-size: 0.75em; color: #94a3b8; margin-left: 8px; }
</style>
</head>
<body>
<h1>📚 轻小说文库</h1>
<p>本地镜像 · 共 """ + str(len(book_ids)) + """ 部作品</p>
<ul>
"""
    for book_id in book_ids:
        # 尝试读取 catalog 获取真实标题
        catalog_title = None
        catalog_path = Path(__file__).resolve().parents[1] / "data" / "catalogs" / f"{book_id}.json"
        if catalog_path.exists():
            try:
                with open(catalog_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    catalog_title = data.get("title", "")
            except Exception:
                pass

        display_title = catalog_title or f"作品 #{book_id}"
        index_html += f'  <li><a href="{book_id}/index.html">{display_title} <span class="book-id">#{book_id}</span></a></li>\n'

    index_html += """
</ul>
<div style="text-align:center;color:#94a3b8;font-size:13px;margin-top:48px">
  由 Parallel Text Viewer 生成
</div>
</body>
</html>"""

    index_path = output_root / "index.html"
    output_root.mkdir(parents=True, exist_ok=True)
    index_path.write_text(index_html, encoding="utf-8")
    logger.info(f"  汇总索引页面: {index_path}")


def _start_server(directory: Path, port: int):
    """启动本地 HTTP 服务器"""
    import http.server
    import socketserver

    os.chdir(directory)

    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, fmt, *args):
            logger.info(f"  [server] {fmt % args}")

    try:
        url = f"http://localhost:{port}"
        logger.info(f"\n{'=' * 50}")
        logger.info(f"  启动本地服务器: {url}")
        logger.info(f"  目录: {directory}")
        logger.info(f"  按 Ctrl+C 停止")
        logger.info(f"{'=' * 50}")

        with socketserver.TCPServer(("", port), QuietHandler) as httpd:
            import webbrowser
            webbrowser.open(url)
            httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("\n服务器已停止。")


if __name__ == "__main__":
    sys.exit(main())
