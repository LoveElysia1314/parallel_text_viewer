#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试图片复制和工作目录查找功能
"""

import pytest
import json
import tempfile
from pathlib import Path
from parallel_text_viewer.utils import copy_files, copy_images_from_config, find_working_directory


class TestFindWorkingDirectory:
    """工作目录查找测试"""

    def test_find_novel_directory(self, tmp_path):
        """测试查找 novel_<book_id> 目录"""
        # 创建测试结构
        data_root = tmp_path / "data"
        data_root.mkdir()

        working_dir = data_root / "novel_2930"
        working_dir.mkdir()

        # 创建 vol_001
        vol_dir = working_dir / "vol_001"
        vol_dir.mkdir()

        # 查找
        result = find_working_directory(data_root, "2930")
        assert result == working_dir

    def test_find_book_id_directory(self, tmp_path):
        """测试查找 <book_id> 目录"""
        data_root = tmp_path / "data"
        data_root.mkdir()

        working_dir = data_root / "2930"
        working_dir.mkdir()

        vol_dir = working_dir / "vol_001"
        vol_dir.mkdir()

        result = find_working_directory(data_root, "2930")
        assert result == working_dir

    def test_find_chapters_subdirectory(self, tmp_path):
        """测试查找 chapters/<book_id> 目录"""
        data_root = tmp_path / "data"
        data_root.mkdir()

        chapters_dir = data_root / "chapters"
        chapters_dir.mkdir()

        working_dir = chapters_dir / "2930"
        working_dir.mkdir()

        vol_dir = working_dir / "vol_001"
        vol_dir.mkdir()

        result = find_working_directory(data_root, "2930")
        assert result == working_dir

    def test_find_with_custom_candidates(self, tmp_path):
        """测试自定义候选目录"""
        data_root = tmp_path / "data"
        data_root.mkdir()

        custom_dir = data_root / "custom_path"
        custom_dir.mkdir()

        vol_dir = custom_dir / "vol_001"
        vol_dir.mkdir()

        result = find_working_directory(data_root, "2930", candidates=["custom_path"])
        assert result == custom_dir

    def test_find_not_exists(self, tmp_path):
        """测试目录不存在的情况"""
        data_root = tmp_path / "data"
        data_root.mkdir()

        # 传入一个完全不存在的候选
        result = find_working_directory(data_root, "nonexistent", candidates=["nonexistent_path"])
        assert result is None

    def test_find_returns_first_existing_without_volumes(self, tmp_path):
        """测试没有 vol_* 子目录时返回第一个存在的"""
        data_root = tmp_path / "data"
        data_root.mkdir()

        working_dir = data_root / "novel_2930"
        working_dir.mkdir()

        result = find_working_directory(data_root, "2930")
        assert result == working_dir


class TestCopyFiles:
    """文件复制测试"""

    def test_copy_files_preserve_structure(self, tmp_path):
        """测试保留目录结构的复制"""
        # 创建源文件
        data_root = tmp_path / "data"
        data_root.mkdir()

        img_dir = data_root / "images" / "2930" / "vol_001"
        img_dir.mkdir(parents=True)

        img_file = img_dir / "001.jpg"
        img_file.write_text("fake image")

        # 复制
        output_dir = tmp_path / "output"
        copied, failed = copy_files([img_file], data_root, output_dir, preserve_structure=True)

        # 验证
        assert copied == 1
        assert failed == 0
        assert (output_dir / "images" / "2930" / "vol_001" / "001.jpg").exists()

    def test_copy_files_no_structure(self, tmp_path):
        """测试不保留目录结构的复制"""
        data_root = tmp_path / "data"
        data_root.mkdir()

        img_dir = data_root / "images" / "2930" / "vol_001"
        img_dir.mkdir(parents=True)

        img_file = img_dir / "001.jpg"
        img_file.write_text("fake image")

        output_dir = tmp_path / "output"
        copied, failed = copy_files([img_file], data_root, output_dir, preserve_structure=False)

        assert copied == 1
        assert failed == 0
        assert (output_dir / "001.jpg").exists()

    def test_copy_files_dry_run(self, tmp_path):
        """测试 dry_run 模式"""
        data_root = tmp_path / "data"
        data_root.mkdir()

        img_dir = data_root / "images"
        img_dir.mkdir()

        img_file = img_dir / "001.jpg"
        img_file.write_text("fake image")

        output_dir = tmp_path / "output"
        copied, failed = copy_files(
            [img_file], data_root, output_dir, preserve_structure=True, dry_run=True
        )

        # 虽然返回成功，但不应该实际复制
        assert copied == 1
        assert not output_dir.exists()

    def test_copy_files_overwrite_false(self, tmp_path):
        """测试不覆盖已存在文件"""
        data_root = tmp_path / "data"
        data_root.mkdir()

        img_file = data_root / "001.jpg"
        img_file.write_text("fake image v1")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        existing_file = output_dir / "001.jpg"
        existing_file.write_text("existing v2")

        copied, failed = copy_files(
            [img_file], data_root, output_dir, preserve_structure=False, overwrite=False
        )

        # 应该跳过而不是复制
        assert (output_dir / "001.jpg").read_text() == "existing v2"

    def test_copy_nonexistent_file(self, tmp_path):
        """测试复制不存在的文件"""
        data_root = tmp_path / "data"
        data_root.mkdir()

        nonexistent = data_root / "nonexistent.jpg"

        output_dir = tmp_path / "output"
        copied, failed = copy_files([nonexistent], data_root, output_dir)

        assert copied == 0
        assert failed == 1


class TestCopyImagesFromConfig:
    """从配置文件复制图片的测试"""

    def test_copy_images_from_config(self, tmp_path):
        """测试从配置文件复制图片"""
        # 创建数据结构
        data_root = tmp_path / "data"
        data_root.mkdir()

        img_dir = data_root / "images" / "2930" / "vol_001"
        img_dir.mkdir(parents=True)

        img1 = img_dir / "001_1.jpg"
        img1.write_text("image1")

        img2 = img_dir / "001_2.jpg"
        img2.write_text("image2")

        # 创建配置文件
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        config = {
            "works": [
                {
                    "volumes": [
                        {
                            "chapters": [
                                {
                                    "images": {
                                        "files": [
                                            {"filename": "images/2930/vol_001/001_1.jpg"},
                                            {"filename": "images/2930/vol_001/001_2.jpg"},
                                        ]
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        config_file = output_dir / "config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f)

        # 复制图片
        copied, failed = copy_images_from_config(
            config_file, data_root, output_dir, preserve_structure=True
        )

        # 验证
        assert copied == 2
        assert failed == 0
        assert (output_dir / "images" / "2930" / "vol_001" / "001_1.jpg").exists()
        assert (output_dir / "images" / "2930" / "vol_001" / "001_2.jpg").exists()

    def test_copy_images_no_config(self, tmp_path):
        """测试配置文件不存在"""
        config_file = tmp_path / "nonexistent.json"

        copied, failed = copy_images_from_config(config_file, tmp_path, tmp_path / "output")

        assert copied == 0
        assert failed == 0

    def test_copy_images_empty_config(self, tmp_path):
        """测试空配置文件"""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        config_file = output_dir / "config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump({}, f)

        copied, failed = copy_images_from_config(config_file, tmp_path, output_dir)

        assert copied == 0
        assert failed == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
