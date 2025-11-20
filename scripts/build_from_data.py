#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端构建脚本：从 data/ 文件夹直接生成最终的 HTML 输出

用法：
    python scripts/build_from_data.py [data_path] [output_dir] [book_id]

示例：
    # 使用默认参数
    python scripts/build_from_data.py
    
    # 自定义输出目录
    python scripts/build_from_data.py data output_book 2930
"""

import sys
import re
import json
from pathlib import Path
from typing import Dict, Any, Set
import logging
import shutil

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)


class DataToHTML:
    """完整的数据转换流程：data → config → HTML"""
    
    def __init__(self, data_root: str = "data", output_dir: str = "output", book_id: str = "2930"):
        self.data_root = Path(data_root)
        self.output_dir = Path(output_dir)
        self.book_id = book_id
        self.config_file = self.output_dir / "config.json"
        self.working_dir = None  # 将在 _find_working_dir 中设置
        
        # 导入必要的模块
        try:
            from parallel_text_viewer.cli.dispatcher import CommandDispatcher
            from parallel_text_viewer.core.config_v2 import ConfigLoader
            
            self.dispatcher = CommandDispatcher()
            self.ConfigLoader = ConfigLoader
        except ImportError as e:
            raise ImportError(f"无法导入 parallel_text_viewer 模块: {e}")
    
    def _find_working_dir(self) -> Path:
        """查找实际的工作目录（包含章节文件的目录）"""
        
        # 尝试多个可能的位置
        candidates = [
            # 1. novel_<book_id>
            self.data_root / f"novel_{self.book_id}",
            # 2. <book_id>
            self.data_root / self.book_id,
            # 3. chapters/<book_id>
            self.data_root / "chapters" / self.book_id,
            # 4. 直接在 data_root
            self.data_root,
        ]
        
        for candidate in candidates:
            if candidate.exists():
                # 检查是否有卷目录
                vol_dirs = list(candidate.glob("vol_*"))
                if vol_dirs:
                    logger.info(f"[OK] Found data directory: {candidate}")
                    return candidate
        
        # 如果没找到，返回第一个存在的
        for candidate in candidates:
            if candidate.exists():
                logger.warning(f"[WARN] Data directory has no volumes, using: {candidate}")
                return candidate
        
        raise FileNotFoundError(f"无法找到数据目录（尝试了：{', '.join(str(c) for c in candidates)}）")
    
    def generate_config(self) -> bool:
        """步骤 1: 从 data/ 生成 Config v2.0"""
        logger.info("=" * 70)
        logger.info("步骤 1: 生成配置文件")
        logger.info("=" * 70)
        
        try:
            # 查找实际的工作目录
            if self.working_dir is None:
                self.working_dir = self._find_working_dir()
            
            # 确保工作目录是绝对路径
            working_dir_abs = self.working_dir.resolve()
            
            config = {
                "mode": "gen-config",
                "book_id": self.book_id,
                "title": f"Book {self.book_id}",
                "working_dir": str(working_dir_abs),
                "volume_pattern": "vol_*",
                "image_strategy": "directory",
                "output_structure": "by_volume",  # 按卷组织输出
                "output": str(self.config_file)
            }
            self.dispatcher.dispatch(config)
            logger.info(f"[OK] Config file generated: {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"[ERROR] Failed to generate config: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def validate_config(self) -> bool:
        """步骤 2: 验证配置文件"""
        logger.info("\n" + "=" * 70)
        logger.info("步骤 2: 验证配置文件")
        logger.info("=" * 70)
        
        try:
            if not self.config_file.exists():
                logger.error(f"[ERROR] Config file not found: {self.config_file}")
                return False
            
            # 确保已找到工作目录
            if self.working_dir is None:
                self.working_dir = self._find_working_dir()
            
            working_dir_abs = self.working_dir.resolve()
            
            # 直接进行验证
            config = {
                "mode": "validate-config",
                "config_file": self.config_file,
                "working_dir": str(working_dir_abs)
            }
            self.dispatcher.dispatch(config)
            logger.info(f"[OK] Config validation passed")
            return True
        except Exception as e:
            logger.error(f"[ERROR] Validation failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def generate_html(self) -> bool:
        """步骤 3: 生成 HTML 输出"""
        logger.info("\n" + "=" * 70)
        logger.info("步骤 3: 生成 HTML 输出")
        logger.info("=" * 70)
        
        try:
            config = {
                "mode": "book_index",
                "index": self.config_file,
                "output_dir": str(self.output_dir)
            }
            self.dispatcher.dispatch(config)
            logger.info(f"[OK] HTML generated at: {self.output_dir}")
            return True
        except Exception as e:
            logger.error(f"[ERROR] Failed to generate HTML: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def copy_images(self) -> bool:
        """步骤 4: 根据配置复制图片到输出目录（保持原始组织形式）"""
        logger.info("\n" + "=" * 70)
        logger.info("步骤 4: 复制图片文件到输出目录")
        logger.info("=" * 70)
        
        try:
            # 读取配置文件获取图片信息
            if not self.config_file.exists():
                logger.warning(f"[WARN] Config file not found: {self.config_file}")
                return True
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 提取所有章节的图片
            images_to_copy: Dict[str, Path] = {}  # {relative_path: source_path}
            
            works = config.get("works", [])
            for work in works:
                volumes = work.get("volumes", [])
                for volume in volumes:
                    chapters = volume.get("chapters", [])
                    for chapter in chapters:
                        chapter_images = chapter.get("images", {})
                        if chapter_images:
                            files = chapter_images.get("files", [])
                            for img_ref in files:
                                img_filename = img_ref.get("filename")
                                if img_filename:
                                    # 从 data 目录查找源文件
                                    source_path = self.data_root / img_filename
                                    if source_path.exists():
                                        images_to_copy[img_filename] = source_path
                                    else:
                                        logger.debug(f"[DEBUG] Image not found: {source_path}")
            
            logger.info(f"[INFO] Found {len(images_to_copy)} images to copy from config")
            
            if not images_to_copy:
                logger.info("[INFO] No images to copy")
                return True
            
            # 复制图片，保持原始目录结构
            copied_count = 0
            for rel_path, source_path in images_to_copy.items():
                try:
                    # 在输出目录中保持相同的相对路径结构
                    dest_path = self.output_dir / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    if not dest_path.exists():
                        shutil.copy2(source_path, dest_path)
                    copied_count += 1
                    logger.debug(f"[DEBUG] Copied: {rel_path}")
                except Exception as e:
                    logger.warning(f"[WARN] Failed to copy {rel_path}: {e}")
            
            logger.info(f"[OK] Copied {copied_count}/{len(images_to_copy)} images to: {self.output_dir}")
            
            return True
        except Exception as e:
            logger.error(f"[ERROR] Failed to copy images: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run(self) -> bool:
        """执行完整流程"""
        logger.info("\n" + "=" * 70)
        logger.info("开始 DATA → HTML 构建流程")
        logger.info("=" * 70)
        logger.info(f"数据根目录: {self.data_root.absolute()}")
        logger.info(f"输出目录: {self.output_dir.absolute()}")
        logger.info(f"书籍 ID: {self.book_id}")
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 执行四个步骤
        steps = [
            ("生成配置", self.generate_config),
            ("验证配置", self.validate_config),
            ("生成HTML", self.generate_html),
            ("复制图片", self.copy_images)
        ]
        
        for step_name, step_func in steps:
            if not step_func():
                logger.error(f"\n[ERROR] {step_name} failed, process aborted")
                return False
        
        # 完成
        logger.info("\n" + "=" * 70)
        logger.info("[OK] Process completed!")
        logger.info("=" * 70)
        logger.info(f"工作目录: {self.working_dir.absolute()}")
        logger.info(f"输出位置: {self.output_dir.absolute()}")
        logger.info(f"打开浏览器访问: {(self.output_dir / 'index.html').absolute()}")
        logger.info("=" * 70)
        return True


def main():
    """主函数"""
    if len(sys.argv) > 1:
        data_root = sys.argv[1]
    else:
        data_root = "data"
    
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    else:
        output_dir = "output"
    
    if len(sys.argv) > 3:
        book_id = sys.argv[3]
    else:
        book_id = "2930"
    
    try:
        builder = DataToHTML(data_root, output_dir, book_id)
        success = builder.run()
        return 0 if success else 1
    except Exception as e:
        logger.error(f"[ERROR] Build failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
