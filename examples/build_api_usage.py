#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高层 API 使用示例

演示如何使用 parallel_text_viewer 的新高层 API 来构建书籍。
"""

import logging
from pathlib import Path
from parallel_text_viewer.core.build import build_from_data, BuildOptions

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def example_1_basic_build():
    """示例 1: 基础构建"""
    print("\n" + "=" * 70)
    print("示例 1: 基础构建")
    print("=" * 70)
    
    result = build_from_data(BuildOptions(
        data_root=Path("data"),
        output_dir=Path("output"),
        book_id="2930",
        title="My Novel"
    ))
    
    if result.success:
        print(f"✓ 构建成功！")
        print(f"  工作目录: {result.working_dir}")
        print(f"  输出目录: {result.output_dir}")
        print(f"  Config: {result.config_file}")
        print(f"  复制图片: {result.images_copied} 张")
    else:
        print(f"✗ 构建失败:")
        for error in result.errors:
            print(f"  - {error}")


def example_2_custom_working_dir():
    """示例 2: 自定义工作目录候选"""
    print("\n" + "=" * 70)
    print("示例 2: 自定义工作目录候选")
    print("=" * 70)
    
    result = build_from_data(BuildOptions(
        data_root=Path("data"),
        output_dir=Path("output_custom"),
        book_id="2930",
        title="My Novel",
        # 指定工作目录的查找顺序
        working_dir_candidates=[
            "my_books/2930",      # 首先查找这个
            "novel_2930",         # 然后查找这个
            "2930",               # 再查找这个
            "."                   # 最后查找根目录
        ]
    ))
    
    print(f"工作目录: {result.working_dir}")


def example_3_skip_images():
    """示例 3: 跳过图片复制"""
    print("\n" + "=" * 70)
    print("示例 3: 跳过图片复制")
    print("=" * 70)
    
    result = build_from_data(BuildOptions(
        data_root=Path("data"),
        output_dir=Path("output_no_images"),
        book_id="2930",
        title="My Novel",
        copy_images=False  # 不复制图片
    ))
    
    print(f"Config 文件: {result.config_file}")
    print(f"输出目录: {result.output_dir}")


def example_4_skip_validation():
    """示例 4: 跳过 Config 验证"""
    print("\n" + "=" * 70)
    print("示例 4: 跳过 Config 验证")
    print("=" * 70)
    
    result = build_from_data(BuildOptions(
        data_root=Path("data"),
        output_dir=Path("output_no_validate"),
        book_id="2930",
        title="My Novel",
        validate_config=False  # 不验证 config
    ))
    
    print(f"生成成功: {result.success}")


def example_5_recursive_image_search():
    """示例 5: 递归搜索缺失的图片"""
    print("\n" + "=" * 70)
    print("示例 5: 递归搜索缺失的图片")
    print("=" * 70)
    
    result = build_from_data(BuildOptions(
        data_root=Path("data"),
        output_dir=Path("output_recursive"),
        book_id="2930",
        title="My Novel",
        search_recursive_images=True,  # 递归搜索缺失的图片
        copy_images=True
    ))
    
    print(f"复制的图片: {result.images_copied}")
    print(f"失败的图片: {result.images_failed}")


def example_6_all_options():
    """示例 6: 所有选项配置"""
    print("\n" + "=" * 70)
    print("示例 6: 完整的选项配置")
    print("=" * 70)
    
    result = build_from_data(BuildOptions(
        # 路径配置
        data_root=Path("data"),
        output_dir=Path("output_full"),
        book_id="2930",
        title="Complete Example",
        
        # 工作目录发现
        working_dir_candidates=[
            "novels/2930",
            "novel_2930",
            "2930"
        ],
        
        # 构建流程控制
        validate_config=True,
        copy_images=True,
        preserve_image_structure=True,
        search_recursive_images=False
    ))
    
    if result.success:
        print("✓ 完整构建成功！")
        print(f"  工作目录: {result.working_dir}")
        print(f"  Config 文件: {result.config_file}")
        print(f"  输出目录: {result.output_dir}")
        print(f"  成功复制图片: {result.images_copied}")
        if result.images_failed > 0:
            print(f"  失败的图片: {result.images_failed}")
    else:
        print("✗ 构建失败")
        for error in result.errors:
            print(f"  错误: {error}")


if __name__ == "__main__":
    print("\n")
    print("parallel_text_viewer 高层 API 使用示例")
    print("=" * 70)
    
    # 注意：以下示例假设相应的 data/ 目录结构存在
    # 在实际使用中，请确保数据目录存在
    
    try:
        example_1_basic_build()
    except FileNotFoundError as e:
        print(f"✗ 示例 1 失败: {e}")
    
    try:
        example_2_custom_working_dir()
    except Exception as e:
        print(f"✗ 示例 2 失败: {e}")
    
    try:
        example_3_skip_images()
    except Exception as e:
        print(f"✗ 示例 3 失败: {e}")
    
    try:
        example_4_skip_validation()
    except Exception as e:
        print(f"✗ 示例 4 失败: {e}")
    
    try:
        example_5_recursive_image_search()
    except Exception as e:
        print(f"✗ 示例 5 失败: {e}")
    
    try:
        example_6_all_options()
    except Exception as e:
        print(f"✗ 示例 6 失败: {e}")
    
    print("\n" + "=" * 70)
    print("示例运行完成")
    print("=" * 70 + "\n")
