#!/usr/bin/env python3
"""简单双语故事演示"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from parallel_text_viewer import GeneratorFactory


def main():
    print("🚀 生成双语故事演示...")

    # 文件路径
    main_file = Path(__file__).parent / "demo_story_cn.md"
    side_file = Path(__file__).parent / "demo_story_en.md"
    output_file = Path(__file__).parent / "demo_output.html"

    # 创建生成器工厂
    factory = GeneratorFactory()

    # 生成HTML
    generator = factory.create_single_file_generator(
        main_file=main_file,
        side_file=side_file,
        title="双语故事演示",
        primary="a",
        orientation="vertical",
        sync=False,
        ignore_empty=True,
    )

    generator.generate(output_file)

    size_kb = output_file.stat().st_size / 1024
    print("✅ 演示生成完成!")
    print(f"📄 输出文件: {output_file.name}")
    print(".1f")
    print("🌐 用浏览器打开查看")


if __name__ == "__main__":
    main()
