#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地开发服务器 — 为构建输出提供 HTTP 服务

支持：
  - 静态文件服务（直接浏览 output/ 目录）
  - 自动列出目录
  - 可定制端口和目录

用法：
    python scripts/serve.py              # 默认端口 8080，服务 output/ 目录
    python scripts/serve.py --port 3000  # 指定端口
    python scripts/serve.py --dir my_output  # 指定目录
    python scripts/serve.py --open       # 自动在浏览器中打开
"""

import argparse
import http.server
import socketserver
import webbrowser
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

PORT = 8080
DIR = "output"


class CustomHandler(http.server.SimpleHTTPRequestHandler):
    """自定义 HTTP 请求处理器"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        logger.info(f"[{self.address_string()}] {format % args}")


def main():
    parser = argparse.ArgumentParser(description="并行文本查看器 — 本地开发服务器")
    parser.add_argument("--port", type=int, default=PORT, help=f"端口号（默认 {PORT}）")
    parser.add_argument(
        "--dir",
        type=str,
        default=DIR,
        help=f"服务目录（默认 {DIR}）",
    )
    parser.add_argument(
        "--open",
        "-o",
        action="store_true",
        help="自动在浏览器中打开",
    )
    args = parser.parse_args()

    # 切换到项目根目录
    project_root = Path(__file__).resolve().parents[1]
    serve_dir = project_root / args.dir

    if not serve_dir.exists():
        logger.error(f"目录不存在: {serve_dir}")
        logger.error("请先运行构建脚本生成输出文件。")
        return 1

    os.chdir(serve_dir)

    handler = CustomHandler

    try:
        with socketserver.TCPServer(("", args.port), handler) as httpd:
            url = f"http://localhost:{args.port}"
            logger.info("")
            logger.info("=" * 60)
            logger.info(f"  本地开发服务器已启动")
            logger.info(f"  URL: {url}")
            logger.info(f"  目录: {serve_dir}")
            logger.info(f"  按 Ctrl+C 停止")
            logger.info("=" * 60)
            logger.info("")

            if args.open:
                webbrowser.open(url)

            httpd.serve_forever()
    except OSError as e:
        logger.error(f"无法启动服务器（端口 {args.port} 可能已被占用）: {e}")
        logger.info(f"提示: 使用 --port 参数指定其他端口")
        return 1
    except KeyboardInterrupt:
        logger.info("\n服务器已停止。")
        return 0


if __name__ == "__main__":
    import os
    main()
