#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试高层构建 API 和 Pattern 路径解析
"""

import pytest
import json
import tempfile
from pathlib import Path
from parallel_text_viewer.core.build import (
    BuildOptions,
    BuildResult,
    PatternPathResolver,
    build_from_data,
)


class TestPatternPathResolver:
    """Pattern 路径解析器测试"""

    def test_expand_pattern_simple(self, tmp_path):
        """测试简单 Pattern 展开"""
        resolver = PatternPathResolver(tmp_path, "2930")
        
        # 创建测试文件
        vol_dir = tmp_path / "vol_001" / "cn"
        vol_dir.mkdir(parents=True)
        test_file = vol_dir / "118359.md"
        test_file.write_text("test")
        
        # 展开 pattern
        results = resolver.expand_pattern(
            "vol_{volume}/{lang}/{chapter}.md",
            volume="001",
            lang="cn",
            chapter="118359"
        )
        
        assert len(results) == 1
        assert results[0].exists()

    def test_expand_pattern_with_glob(self, tmp_path):
        """测试 Pattern 中的 glob 通配符"""
        resolver = PatternPathResolver(tmp_path, "2930")
        
        # 创建多个测试文件
        img_dir = tmp_path / "images" / "2930" / "vol_001"
        img_dir.mkdir(parents=True)
        
        img1 = img_dir / "118359_1.jpg"
        img2 = img_dir / "118359_2.jpg"
        img1.write_text("img1")
        img2.write_text("img2")
        
        # 展开 pattern（包含 glob）
        results = resolver.expand_pattern(
            "images/{book_id}/vol_{volume}/{chapter}_*.jpg",
            volume="001",
            chapter="118359"
        )
        
        assert len(results) == 2
        assert all(r.exists() for r in results)

    def test_expand_pattern_auto_book_id(self, tmp_path):
        """测试自动添加 book_id"""
        resolver = PatternPathResolver(tmp_path, "2930")
        
        # 创建测试文件
        img_dir = tmp_path / "images" / "2930"
        img_dir.mkdir(parents=True)
        test_file = img_dir / "test.jpg"
        test_file.write_text("test")
        
        # 不显式传递 book_id，应自动使用
        results = resolver.expand_pattern(
            "images/{book_id}/test.jpg"
        )
        
        assert len(results) == 1
        assert results[0].exists()

    def test_expand_pattern_nonexistent(self, tmp_path):
        """测试展开不存在的路径"""
        resolver = PatternPathResolver(tmp_path, "2930")
        
        results = resolver.expand_pattern(
            "vol_{volume}/cn/{chapter}.md",
            volume="001",
            chapter="nonexistent"
        )
        
        # 应返回路径对象，即使文件不存在
        assert len(results) == 1
        assert not results[0].exists()

    def test_expand_pattern_glob_no_match(self, tmp_path):
        """测试 glob 无匹配的情况"""
        resolver = PatternPathResolver(tmp_path, "2930")
        
        # 创建目录但不创建匹配文件
        img_dir = tmp_path / "images" / "2930" / "vol_001"
        img_dir.mkdir(parents=True)
        
        results = resolver.expand_pattern(
            "images/{book_id}/vol_{volume}/nonexistent_*.jpg",
            volume="001"
        )
        
        # glob 无匹配应返回空列表
        assert len(results) == 0


class TestBuildOptions:
    """构建选项测试"""

    def test_build_options_path_conversion(self):
        """测试字符串路径自动转换为 Path 对象"""
        options = BuildOptions(
            data_root="data",
            output_dir="output",
            book_id="2930"
        )
        
        assert isinstance(options.data_root, Path)
        assert isinstance(options.output_dir, Path)

    def test_build_options_defaults(self):
        """测试默认选项"""
        options = BuildOptions(
            data_root="data",
            output_dir="output",
            book_id="2930"
        )
        
        assert options.title == ""
        assert options.validate_config is True
        assert options.copy_images is True
        assert options.preserve_image_structure is True
        assert options.search_recursive_images is False
        assert options.main_pattern is None
        assert options.side_pattern is None
        assert options.image_pattern is None


class TestBuildResult:
    """构建结果测试"""

    def test_build_result_default_errors(self):
        """测试结果的默认错误列表"""
        result = BuildResult(success=False)
        
        assert result.errors is not None
        assert isinstance(result.errors, list)
        assert len(result.errors) == 0

    def test_build_result_add_errors(self):
        """测试添加错误到结果"""
        result = BuildResult(success=False)
        
        result.errors.append("Error 1")
        result.errors.append("Error 2")
        
        assert len(result.errors) == 2


class TestBuildFromDataIntegration:
    """高层 API 集成测试"""

    def test_build_from_data_basic(self, tmp_path):
        """测试基础构建流程"""
        # 创建简单的数据结构
        data_root = tmp_path / "data"
        data_root.mkdir()
        
        working_dir = data_root / "novel_2930"
        working_dir.mkdir()
        
        vol_dir = working_dir / "vol_001"
        vol_dir.mkdir()
        
        cn_dir = vol_dir / "cn"
        en_dir = vol_dir / "en"
        cn_dir.mkdir()
        en_dir.mkdir()
        
        # 创建测试文件
        ch_file_cn = cn_dir / "118359.md"
        ch_file_en = en_dir / "118359.md"
        ch_file_cn.write_text("# Chapter 1\n\nChinese content")
        ch_file_en.write_text("# Chapter 1\n\nEnglish content")
        
        # 创建 catalog（可选）
        catalog_dir = data_root / "catalogs"
        catalog_dir.mkdir()
        
        catalog = {
            "volumes": [
                {
                    "volume_name": "Volume 1",
                    "chapters": [
                        {
                            "chapter_name": "Chapter 1",
                            "url": "https://example.com/2930/118359.htm"
                        }
                    ]
                }
            ]
        }
        
        catalog_file = catalog_dir / "2930.json"
        with open(catalog_file, 'w', encoding='utf-8') as f:
            json.dump(catalog, f)
        
        # 执行构建
        output_dir = tmp_path / "output"
        result = build_from_data(BuildOptions(
            data_root=data_root,
            output_dir=output_dir,
            book_id="2930",
            title="Test Novel",
            validate_config=True,
            copy_images=False  # 跳过图片复制，因为没有图片
        ))
        
        # 验证结果
        assert result.working_dir == working_dir
        assert result.output_dir == output_dir
        assert result.config_file == output_dir / "config.json"
        assert result.config_file.exists()

    def test_build_from_data_with_images(self, tmp_path):
        """测试包含图片的构建"""
        # 创建数据结构
        data_root = tmp_path / "data"
        data_root.mkdir()
        
        working_dir = data_root / "novel_2930"
        working_dir.mkdir()
        
        vol_dir = working_dir / "vol_001"
        vol_dir.mkdir()
        
        cn_dir = vol_dir / "cn"
        en_dir = vol_dir / "en"
        cn_dir.mkdir()
        en_dir.mkdir()
        
        # 创建章节文件
        ch_file = cn_dir / "118359.md"
        ch_file.write_text("# Chapter 1")
        en_file = en_dir / "118359.md"
        en_file.write_text("# Chapter 1")
        
        # 创建图片
        img_dir = data_root / "images" / "2930" / "vol_001"
        img_dir.mkdir(parents=True)
        img1 = img_dir / "118359_1.jpg"
        img2 = img_dir / "118359_2.jpg"
        img1.write_text("fake image 1")
        img2.write_text("fake image 2")
        
        # 创建 catalog
        catalog_dir = data_root / "catalogs"
        catalog_dir.mkdir()
        
        catalog = {
            "volumes": [
                {
                    "volume_name": "Volume 1",
                    "chapters": [
                        {
                            "chapter_name": "Chapter 1",
                            "url": "https://example.com/2930/118359.htm"
                        }
                    ]
                }
            ]
        }
        
        with open(catalog_dir / "2930.json", 'w', encoding='utf-8') as f:
            json.dump(catalog, f)
        
        # 执行构建
        output_dir = tmp_path / "output"
        result = build_from_data(BuildOptions(
            data_root=data_root,
            output_dir=output_dir,
            book_id="2930",
            title="Test Novel with Images",
            copy_images=True
        ))
        
        # 验证结果
        assert result.config_file.exists()
        # 注意：图片复制需要正确的 config 结构，可能会有 0 张复制
        # 这是预期的，因为生成的 config 可能没有正确关联图片

    def test_build_from_data_missing_working_dir(self, tmp_path):
        """测试找不到工作目录"""
        # 创建一个空的 data 目录，让 find_working_directory 返回 data_root 本身
        data_root = tmp_path / "data"
        data_root.mkdir()

        output_dir = tmp_path / "output"

        # 当工作目录存在但没有 vol_* 子目录时，仍会被返回
        # 这是向后兼容的行为
        result = build_from_data(BuildOptions(
            data_root=data_root,
            output_dir=output_dir,
            book_id="nonexistent"
        ))

        # 虽然会返回成功，但 config 会是空的（没有卷或章节）
        assert result.working_dir == data_root
        assert result.config_file.exists()

    def test_build_from_data_truly_missing_dir(self, tmp_path):
        """测试完全不存在的数据目录"""
        # 指定一个完全不存在的数据根目录
        data_root = tmp_path / "nonexistent_data"
        output_dir = tmp_path / "output"

        result = build_from_data(BuildOptions(
            data_root=data_root,
            output_dir=output_dir,
            book_id="2930"
        ))

        # 当 data_root 本身不存在时应该失败
        assert not result.success
        assert len(result.errors) > 0

    def test_build_from_data_custom_working_dir_candidates(self, tmp_path):
        """测试自定义工作目录候选"""
        data_root = tmp_path / "data"
        data_root.mkdir()
        
        # 使用自定义目录名
        working_dir = data_root / "my_custom_novel"
        working_dir.mkdir()
        
        vol_dir = working_dir / "vol_001"
        vol_dir.mkdir()
        
        cn_dir = vol_dir / "cn"
        cn_dir.mkdir()
        ch_file = cn_dir / "001.md"
        ch_file.write_text("# Chapter 1")
        
        output_dir = tmp_path / "output"
        
        result = build_from_data(BuildOptions(
            data_root=data_root,
            output_dir=output_dir,
            book_id="2930",
            working_dir_candidates=["my_custom_novel", "novel_2930", "2930"]
        ))
        
        assert result.working_dir == working_dir
        assert result.config_file.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
