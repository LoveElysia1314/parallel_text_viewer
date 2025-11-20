"""
Config v2.0 和 ConfigGenerator 集成测试

测试 Phase 1-4 的完整功能
"""

import tempfile
import json
from pathlib import Path
from typing import Dict, Any

import pytest

from parallel_text_viewer.core.config_v2 import (
    ConfigV2,
    ConfigLoader,
    PathResolver,
    MetaConfig,
    Work,
    Volume,
    Chapter,
)
from parallel_text_viewer.core.image_placeholder import (
    PlaceholderResolver,
    PlaceholderTextProcessor,
)
from parallel_text_viewer.config.generator import (
    StandardConfigGenerator,
    CrawlerOutputGenerator,
    CSVConfigGenerator,
    GeneratorOptions,
    GeneratorRegistry,
)


class TestConfigV2DataModels:
    """测试 Config v2.0 数据模型（Phase 1）"""
    
    def test_create_config_v2(self):
        """测试创建 Config v2.0"""
        config = ConfigV2()
        assert config.version == "2.0"
        assert config.meta is not None
        assert len(config.works) == 0
    
    def test_add_work_volume_chapter(self):
        """测试添加作品、卷、章节"""
        config = ConfigV2()
        
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
        config = ConfigV2()
        config.meta.book_id = "test_book"
        config.meta.title = "Test Book"
        
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
            config = ConfigV2()
            config.meta.book_id = "test_book"
            config.meta.title = "Test Book"
            
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
            config = ConfigV2()
            config.meta.working_dir = str(tmppath)
            config.meta.structure.type = "standard"
            
            work = Work(title="Book", volumes=[])
            volume = Volume(id="001", title="Vol 1", chapters=[])
            chapter = Chapter(id="001", title="Ch 1")
            
            volume.chapters.append(chapter)
            work.volumes.append(volume)
            config.works.append(work)
            
            # 测试路径解析
            resolver = PathResolver(config, tmppath)
            main_file, side_file = resolver.resolve_chapter_files(chapter, volume, work)
            
            assert main_file is not None
            assert main_file.exists()


class TestPlaceholderSystem:
    """测试占位符图片引用系统（Phase 2）"""
    
    def test_placeholder_resolver_basic(self):
        """测试占位符解析器基础功能"""
        config = ConfigV2()
        config.meta.images.enabled = True
        config.meta.images.base_path = "images"
        
        resolver = PlaceholderResolver(config)
        
        # 测试正则表达式
        text = "这是一个占位符 {IMG:001_001} 图片"
        matches = resolver.PLACEHOLDER_PATTERN.findall(text)
        
        assert len(matches) == 1
        assert matches[0] == ("001", "001")
    
    def test_placeholder_text_processor(self):
        """测试占位符文本处理器"""
        config = ConfigV2()
        config.meta.images.enabled = True
        config.meta.images.reference_style = "filename"
        
        processor = PlaceholderTextProcessor(config)
        
        text = "图片: {IMG:001_000}"
        # 应该保留占位符（因为没有对应的图片）
        result = processor.process(text, chapter_id="001", preserve_placeholders=True)
        
        assert "INVALID_IMG" in result or "{IMG:001_000}" in result


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


class TestCrawlerOutputGenerator:
    """测试爬虫输出 ConfigGenerator（Phase 3）"""
    
    def test_generate_from_crawler_json(self):
        """测试从爬虫输出生成 config"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # 创建爬虫输出 JSON
            crawler_data = {
                "title": "Book from Crawler",
                "volumes": [
                    {
                        "id": "001",
                        "title": "Volume 1",
                        "chapters": [
                            {
                                "id": "001",
                                "title": "Chapter 1",
                                "main_file": "vol_001/cn/001.md",
                                "side_file": "vol_001/en/001.md",
                                "images": ["img1.png", "img2.png"]
                            }
                        ]
                    }
                ]
            }
            
            crawler_file = tmppath / "crawler_output.json"
            with open(crawler_file, "w") as f:
                json.dump(crawler_data, f)
            
            # 生成 config
            gen = CrawlerOutputGenerator()
            options = GeneratorOptions(
                book_id="crawler_test",
                title="Test",
            )
            
            config = gen.generate(options, crawler_file)
            
            assert config.meta.book_id == "crawler_test"
            assert len(config.works) > 0
            assert len(config.works[0].volumes) > 0
            assert len(config.works[0].volumes[0].chapters) > 0


class TestGeneratorRegistry:
    """测试 GeneratorRegistry（Phase 3）"""
    
    def test_registry_has_builtins(self):
        """测试注册表有内置生成器"""
        registry = GeneratorRegistry()
        
        generators = registry.list_generators()
        assert "standard" in generators
        assert "crawler" in generators
        assert "csv" in generators
    
    def test_create_generator(self):
        """测试创建生成器"""
        registry = GeneratorRegistry()
        
        gen = registry.create("standard")
        assert isinstance(gen, StandardConfigGenerator)
    
    def test_register_custom_generator(self):
        """测试注册自定义生成器"""
        from parallel_text_viewer.config.generator import ConfigGenerator
        
        class CustomGenerator(ConfigGenerator):
            def generate(self, options):
                return ConfigV2()
        
        registry = GeneratorRegistry()
        registry.register("custom", CustomGenerator)
        
        gen = registry.create("custom")
        assert isinstance(gen, CustomGenerator)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
