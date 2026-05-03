"""
Config v2.0 和 ConfigGenerator 集成测试

测试 Phase 1-4 的完整功能
"""

import tempfile
import json
from pathlib import Path
from typing import Dict, Any

import pytest

from parallel_text_viewer.core import (
    ConfigV2,
    ConfigLoader,
    PathResolver,
    MetaConfig,
    Work,
    Volume,
    Chapter,
    StandardConfigGenerator,
    GeneratorOptions,
)


class TestConfigV2DataModels:
    """测试 Config v2.0 数据模型（Phase 1）"""

    def test_create_config_v2(self):
        """测试创建 Config v2.0"""
        config = ConfigV2(meta=MetaConfig(book_id="test"))
        assert config.version == "2.0"
        assert config.meta is not None
        assert len(config.works) == 0

    def test_add_work_volume_chapter(self):
        """测试添加作品、卷、章节"""
        config = ConfigV2(meta=MetaConfig(book_id="test"))

        work = Work(title="My Book", volumes=[])
        volume = Volume(id="001", title="Volume 1", chapters=[])
        chapter = Chapter(id="001", title="Chapter 1")

        volume.chapters.append(chapter)
        work.volumes.append(volume)
        config.works.append(work)

        assert len(config.works) == 1
        assert len(config.works[0].volumes) == 1
        assert len(config.works[0].volumes[0].chapters) == 1


class TestConfigLoader:
    """测试 ConfigLoader（Phase 1）"""

    def test_config_to_dict_and_back(self):
        """测试 config 序列化和反序列化"""
        config = ConfigV2(meta=MetaConfig(book_id="test_book", title="Test Book"))

        work = Work(title="Test Work", volumes=[])
        volume = Volume(id="001", title="Vol 1", chapters=[])
        chapter = Chapter(id="001", title="Ch 1")

        volume.chapters.append(chapter)
        work.volumes.append(volume)
        config.works.append(work)

        # 序列化
        data = config.to_dict()

        # 反序列化
        config2 = ConfigV2.from_dict(data)

        assert config2.meta.book_id == "test_book"
        assert len(config2.works) == 1
        assert len(config2.works[0].volumes) == 1

    def test_save_and_load_config(self):
        """测试保存和加载 config 文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ConfigV2(meta=MetaConfig(book_id="test_book", title="Test Book"))

            config_file = Path(tmpdir) / "config.json"
            ConfigLoader.save(config, config_file)

            assert config_file.exists()

            loaded_config = ConfigLoader.load_file(config_file)
            assert loaded_config.meta.book_id == "test_book"


class TestPathResolver:
    """测试 PathResolver（Phase 1）"""

    def test_path_resolver_basic(self):
        """测试基础路径解析"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件结构
            tmppath = Path(tmpdir)
            vol_dir = tmppath / "vol_001" / "cn"
            vol_dir.mkdir(parents=True)
            (vol_dir / "001.md").write_text("# Chapter 1")

            # 创建 config
            config = ConfigV2(meta=MetaConfig(book_id="test", working_dir=str(tmppath)))
            config.meta.structure.type = "standard"

            work = Work(title="Book", volumes=[])
            volume = Volume(id="001", title="Vol 1", chapters=[])
            chapter = Chapter(id="001", title="Ch 1")

            volume.chapters.append(chapter)
            work.volumes.append(volume)
            config.works.append(work)

            # 测试路径解析
            resolver = PathResolver(tmppath)
            main_file, side_file = resolver.resolve_chapter_files(
                chapter, config.meta.structure, volume.id
            )

            assert main_file is not None
            assert main_file.exists()


class TestStandardConfigGenerator:
    """测试标准 ConfigGenerator（Phase 3）"""

    def test_generate_from_standard_structure(self):
        """测试从标准结构生成 config"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # 创建标准文件结构
            vol_dir = tmppath / "vol_001" / "cn"
            vol_dir.mkdir(parents=True)
            (vol_dir / "001.md").write_text("# Chapter 1\nContent")
            (vol_dir / "002.md").write_text("# Chapter 2\nContent")

            # 生成 config
            gen = StandardConfigGenerator()
            options = GeneratorOptions(
                book_id="test",
                title="Test Book",
                working_dir=str(tmppath),
            )

            config = gen.generate(options)

            assert config.meta.book_id == "test"
            assert len(config.works) > 0
            assert len(config.works[0].volumes) > 0

    def test_save_generated_config(self):
        """测试保存生成的 config"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # 创建文件结构
            vol_dir = tmppath / "vol_001" / "cn"
            vol_dir.mkdir(parents=True)
            (vol_dir / "001.md").write_text("Content")

            # 生成和保存
            gen = StandardConfigGenerator()
            options = GeneratorOptions(
                book_id="test",
                title="Test Book",
                working_dir=str(tmppath),
            )

            config = gen.generate(options)
            output_file = tmppath / "config.json"
            gen.save(output_file)

            assert output_file.exists()

            # 验证可以加载
            loaded_config = ConfigLoader.load_file(output_file)
            assert loaded_config.meta.book_id == "test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
