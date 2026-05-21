#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端构建脚本：从 data/ 文件夹直接生成最终的 HTML 输出

这是一个简化的命令行界面，使用 parallel_text_viewer.core.build 提供的高层 API。

用法：
    python scripts/build_from_data.py [data_path] [output_dir] [book_id]

示例：
    # 使用默认参数
    python scripts/build_from_data.py

    # 自定义输出目录
    python scripts/build_from_data.py data output_book 2930

    # 跳过图片复制
    python scripts/build_from_data.py data output 2930 --no-images
"""

import sys
import os
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", encoding="utf-8"
)
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    try:
        from parallel_text_viewer.core import build_from_data, BuildOptions
    except ImportError as e:
        logger.error(f"无法导入 parallel_text_viewer 模块: {e}")
        return 1
    # 将工作目录切换到项目根（脚本上一级目录），以保证相对路径正确
    project_root = Path(__file__).resolve().parents[1]
    try:
        os.chdir(project_root)
        logger.info(f"已切换工作目录: {project_root}")
    except Exception:
        logger.warning(f"无法切换工作目录到 {project_root}, 将使用当前工作目录")

    # 解析命令行参数
    import argparse

    parser = argparse.ArgumentParser(description="并行文本查看器 — 构建工具")
    parser.add_argument("data_root", nargs="?", default="data", help="数据根目录（默认 data）")
    parser.add_argument("output_dir", nargs="?", default="output", help="输出目录（默认 output）")
    parser.add_argument("book_id", nargs="?", default="2930", help="作品 ID（默认 2930）")
    parser.add_argument("--no-images", action="store_true", help="跳过图片复制")
    parser.add_argument("--no-validate", action="store_true", help="跳过配置验证")
    parser.add_argument("--serve", "-s", action="store_true", help="构建完成后启动本地服务器")
    parser.add_argument("--serve-port", type=int, default=8080, help="本地服务器端口（默认 8080）")
    parser.add_argument("--open", "-o", action="store_true", help="构建完成后在浏览器中打开")
    args = parser.parse_args()

    data_root = args.data_root
    output_dir = args.output_dir
    book_id = args.book_id
    skip_images = args.no_images
    skip_validation = args.no_validate

    logger.info("=" * 70)
    logger.info("parallel_text_viewer 构建工具")
    logger.info("=" * 70)

    try:
        # 将相对路径解析到项目根，确保从任何工作目录运行脚本都能正确定位
        data_path = Path(data_root)
        if not data_path.is_absolute():
            data_path = project_root / data_path

        output_path = Path(output_dir)
        if not output_path.is_absolute():
            output_path = project_root / output_path

        # 使用核心 API 执行构建
        result = build_from_data(
            BuildOptions(
                data_root=data_path,
                output_dir=output_path,
                book_id=book_id,
                validate_config=not skip_validation,
                copy_images=not skip_images,
                preserve_image_structure=True,
                search_recursive_images=False,
            )
        )

        # 输出结果
        if result.success:
            logger.info("\n" + "=" * 70)
            logger.info("[OK] 构建成功！")
            logger.info("=" * 70)
            logger.info(f"工作目录: {result.working_dir}")
            logger.info(f"输出位置: {result.output_dir}")
            logger.info(f"配置文件: {result.config_file}")

            if not skip_images and result.images_copied > 0:
                logger.info(
                    f"复制图片: {result.images_copied} 张成功, {result.images_failed} 张失败"
                )

            logger.info("=" * 70)

            # 启动本地服务器
            if args.serve or args.open:
                _start_local_server(output_path, args.serve_port, args.open)

            return 0
        else:
            logger.error("\n" + "=" * 70)
            logger.error("[ERROR] 构建失败！")
            logger.error("=" * 70)

            for error in result.errors:
                logger.error(f"  - {error}")

            logger.error("=" * 70)
            return 1

    except Exception as e:
        logger.error(f"[ERROR] 构建过程出错: {e}")
        import traceback

        traceback.print_exc()
        return 1


def _start_local_server(directory: Path, port: int, open_browser: bool = False):
    """启动本地 HTTP 服务器"""
    import http.server
    import socketserver
    import webbrowser

    os.chdir(directory)

    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, fmt, *args):
            logger.info(f"  [server] {fmt % args}")

    try:
        url = f"http://localhost:{port}"
        logger.info(f"\n{'=' * 50}")
        logger.info(f"  本地服务器: {url}")
        logger.info(f"  目录: {directory}")
        logger.info(f"  按 Ctrl+C 停止")
        logger.info(f"{'=' * 50}")

        if open_browser:
            webbrowser.open(url)

        with socketserver.TCPServer(("", port), QuietHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("\n服务器已停止。")


if __name__ == "__main__":
    sys.exit(main())
