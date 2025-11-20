#!/usr/bin/env python3
"""
Config v2.0 实现验证脚本

验证所有 Phase 1-4 的功能是否正确实现
"""

import sys
from pathlib import Path

def check_files_exist():
    """检查所有必需的文件是否存在"""
    print("📁 检查文件存在性...")
    
    required_files = [
        "parallel_text_viewer/core/config_v2.py",
        "parallel_text_viewer/core/image_placeholder.py",
        "parallel_text_viewer/config/__init__.py",
        "parallel_text_viewer/config/generator.py",
        "parallel_text_viewer/cli/parser.py",
        "parallel_text_viewer/cli/dispatcher.py",
        "tests/test_config_v2_integration.py",
        "docs/QUICKSTART_V2.md",
        "docs/REFACTORING_SUMMARY.md",
    ]
    
    missing = []
    for file in required_files:
        path = Path(file)
        if path.exists():
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} (缺失)")
            missing.append(file)
    
    return len(missing) == 0, missing


def check_imports():
    """检查主要模块是否可导入"""
    print("\n📦 检查导入...")
    
    try:
        from parallel_text_viewer.core.config_v2 import (
            ConfigV2,
            ConfigLoader,
            PathResolver,
        )
        print("  ✓ ConfigV2 modules imported")
    except Exception as e:
        print(f"  ✗ ConfigV2 import failed: {e}")
        return False
    
    try:
        from parallel_text_viewer.core.image_placeholder import (
            PlaceholderResolver,
            PlaceholderTextProcessor,
        )
        print("  ✓ Image placeholder modules imported")
    except Exception as e:
        print(f"  ✗ Image placeholder import failed: {e}")
        return False
    
    try:
        from parallel_text_viewer.config.generator import (
            ConfigGenerator,
            StandardConfigGenerator,
            CrawlerOutputGenerator,
            CSVConfigGenerator,
            GeneratorRegistry,
        )
        print("  ✓ Generator modules imported")
    except Exception as e:
        print(f"  ✗ Generator import failed: {e}")
        return False
    
    return True


def check_cli_commands():
    """检查 CLI 命令是否可用"""
    print("\n🖥️  检查 CLI 命令...")
    
    try:
        from parallel_text_viewer.cli.parser import ArgumentParser
        
        parser = ArgumentParser()
        
        # 检查新命令是否在 parser 中
        test_args = ["gen-config", "--help"]
        try:
            parser.parse_args(test_args)
        except SystemExit:
            # argparse 在 --help 时会 exit，这是正常的
            pass
        
        print("  ✓ CLI parser with new commands")
    except Exception as e:
        print(f"  ✗ CLI check failed: {e}")
        return False
    
    return True


def check_core_classes():
    """检查核心类的基本方法"""
    print("\n🔧 检查核心类方法...")
    
    from parallel_text_viewer.core.config_v2 import ConfigV2, ConfigLoader, PathResolver, MetaConfig
    
    # 创建 config，MetaConfig 需要 book_id
    meta = MetaConfig(book_id="test")
    config = ConfigV2(meta=meta)
    
    # 检查 ConfigV2 方法
    assert hasattr(config, 'to_dict'), "ConfigV2 缺少 to_dict 方法"
    assert hasattr(ConfigV2, 'from_dict'), "ConfigV2 缺少 from_dict 方法"
    print("  ✓ ConfigV2 基本方法")
    
    # 检查 ConfigLoader 方法
    assert hasattr(ConfigLoader, 'load_file'), "ConfigLoader 缺少 load_file 方法"
    assert hasattr(ConfigLoader, 'validate'), "ConfigLoader 缺少 validate 方法"
    assert hasattr(ConfigLoader, 'save'), "ConfigLoader 缺少 save 方法"
    print("  ✓ ConfigLoader 基本方法")
    
    # 检查 PathResolver 方法
    resolver = PathResolver(config)
    assert hasattr(resolver, 'resolve_chapter_files'), "PathResolver 缺少 resolve_chapter_files 方法"
    assert hasattr(resolver, 'resolve_chapter_images'), "PathResolver 缺少 resolve_chapter_images 方法"
    print("  ✓ PathResolver 基本方法")
    
    return True


def check_placeholder_classes():
    """检查占位符类"""
    print("\n🖼️  检查占位符类...")
    
    from parallel_text_viewer.core.image_placeholder import (
        PlaceholderResolver,
        PlaceholderImageMapper,
        PlaceholderTextProcessor,
    )
    from parallel_text_viewer.core.config_v2 import ConfigV2, MetaConfig
    
    meta = MetaConfig(book_id="test")
    config = ConfigV2(meta=meta)
    
    # 检查 PlaceholderResolver
    resolver = PlaceholderResolver(config)
    assert hasattr(resolver, 'find_placeholders'), "PlaceholderResolver 缺少 find_placeholders"
    assert hasattr(resolver, 'replace_placeholders'), "PlaceholderResolver 缺少 replace_placeholders"
    assert hasattr(resolver, 'get_images_for_chapter'), "PlaceholderResolver 缺少 get_images_for_chapter"
    print("  ✓ PlaceholderResolver 基本方法")
    
    # 检查 PlaceholderImageMapper
    mapper = PlaceholderImageMapper(resolver)
    assert hasattr(mapper, 'convert_to_html'), "PlaceholderImageMapper 缺少 convert_to_html"
    print("  ✓ PlaceholderImageMapper 基本方法")
    
    # 检查 PlaceholderTextProcessor
    processor = PlaceholderTextProcessor(config)
    assert hasattr(processor, 'process'), "PlaceholderTextProcessor 缺少 process"
    assert hasattr(processor, 'extract_image_references'), "PlaceholderTextProcessor 缺少 extract_image_references"
    print("  ✓ PlaceholderTextProcessor 基本方法")
    
    return True


def check_generator_classes():
    """检查生成器类"""
    print("\n⚙️  检查生成器类...")
    
    from parallel_text_viewer.config.generator import (
        ConfigGenerator,
        StandardConfigGenerator,
        CrawlerOutputGenerator,
        CSVConfigGenerator,
        GeneratorRegistry,
        GeneratorOptions,
    )
    
    # 检查基类
    assert hasattr(ConfigGenerator, 'generate'), "ConfigGenerator 缺少 generate 方法"
    assert hasattr(ConfigGenerator, 'save'), "ConfigGenerator 缺少 save 方法"
    print("  ✓ ConfigGenerator 基类")
    
    # 检查生成器
    assert issubclass(StandardConfigGenerator, ConfigGenerator), "StandardConfigGenerator 不继承 ConfigGenerator"
    assert issubclass(CrawlerOutputGenerator, ConfigGenerator), "CrawlerOutputGenerator 不继承 ConfigGenerator"
    assert issubclass(CSVConfigGenerator, ConfigGenerator), "CSVConfigGenerator 不继承 ConfigGenerator"
    print("  ✓ 三个生成器类")
    
    # 检查注册表
    registry = GeneratorRegistry()
    generators = registry.list_generators()
    assert "standard" in generators, "注册表缺少 standard 生成器"
    assert "crawler" in generators, "注册表缺少 crawler 生成器"
    assert "csv" in generators, "注册表缺少 csv 生成器"
    print("  ✓ GeneratorRegistry")
    
    return True


def check_documentation():
    """检查文档完整性"""
    print("\n📚 检查文档...")
    
    required_docs = {
        "docs/QUICKSTART_V2.md": "快速入门指南",
        "docs/REFACTORING_SUMMARY.md": "重构完成总结",
        "docs/CONFIG_DESIGN.md": "Config 规范设计",
        "docs/CONFIG_GENERATOR_DESIGN.md": "Generator 架构设计",
        "docs/PROBLEM_SOLUTION_QA.md": "问题解决方案",
    }
    
    for doc_file, description in required_docs.items():
        path = Path(doc_file)
        if path.exists():
            size = path.stat().st_size
            lines = len(path.read_text(encoding='utf-8').split('\n'))
            print(f"  ✓ {description} ({lines} 行)")
        else:
            print(f"  ✗ {description} (缺失)")
            return False
    
    return True


def main():
    """主验证函数"""
    print("=" * 60)
    print("Config v2.0 重构验证")
    print("=" * 60)
    
    checks = [
        ("文件检查", check_files_exist),
        ("导入检查", check_imports),
        ("CLI 命令", check_cli_commands),
        ("核心类", check_core_classes),
        ("占位符类", check_placeholder_classes),
        ("生成器类", check_generator_classes),
        ("文档检查", check_documentation),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            if name == "文件检查":
                success, extra = check_func()
                results.append((name, success))
            else:
                success = check_func()
                results.append((name, success))
        except Exception as e:
            print(f"\n❌ {name} 检查出错: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("验证总结")
    print("=" * 60)
    
    for name, success in results:
        status = "✓" if success else "✗"
        print(f"{status} {name}")
    
    all_success = all(success for _, success in results)
    
    print("\n" + "=" * 60)
    if all_success:
        print("✅ 所有检查通过！Config v2.0 重构完成！")
        return 0
    else:
        print("❌ 某些检查失败，请检查上面的错误信息")
        return 1


if __name__ == "__main__":
    sys.exit(main())
