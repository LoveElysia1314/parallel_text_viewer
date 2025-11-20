"""
配置验证器

负责验证配置文件和输入文件的有效性。
"""

from pathlib import Path
from typing import Dict, Any, List


class ConfigValidator:
    """配置验证器"""

    def validate_book_config(self, config: Dict[str, Any]) -> List[str]:
        """验证书目配置"""
        errors = []

        if "works" not in config:
            errors.append("Missing 'works' key in config")
            return errors

        works = config["works"]
        if not isinstance(works, list):
            errors.append("'works' must be a list")
            return errors

        for i, work in enumerate(works):
            work_errors = self._validate_work(work, i)
            errors.extend(work_errors)

        return errors

    def _validate_work(self, work: Dict, work_idx: int) -> List[str]:
        """验证单个作品"""
        errors = []

        if "title" not in work:
            errors.append(f"Work {work_idx}: missing 'title'")
        if "volumes" not in work:
            errors.append(f"Work {work_idx}: missing 'volumes'")
            return errors

        volumes = work["volumes"]
        if not isinstance(volumes, list):
            errors.append(f"Work {work_idx}: 'volumes' must be a list")
            return errors

        for j, volume in enumerate(volumes):
            vol_errors = self._validate_volume(volume, work_idx, j)
            errors.extend(vol_errors)

        return errors

    def _validate_volume(self, volume: Dict, work_idx: int, vol_idx: int) -> List[str]:
        """验证单个卷"""
        errors = []

        if "title" not in volume:
            errors.append(f"Work {work_idx}, Volume {vol_idx}: missing 'title'")
        if "chapters" not in volume:
            errors.append(f"Work {work_idx}, Volume {vol_idx}: missing 'chapters'")
            return errors

        chapters = volume["chapters"]
        if not isinstance(chapters, list):
            errors.append(f"Work {work_idx}, Volume {vol_idx}: 'chapters' must be a list")
            return errors

        for k, chapter in enumerate(chapters):
            chap_errors = self._validate_chapter(chapter, work_idx, vol_idx, k)
            errors.extend(chap_errors)

        return errors

    def _validate_chapter(self, chapter: Dict, work_idx: int, vol_idx: int, chap_idx: int) -> List[str]:
        """验证单个章节"""
        errors = []

        if "title" not in chapter:
            errors.append(f"Work {work_idx}, Volume {vol_idx}, Chapter {chap_idx}: missing 'title'")
        if "main_file" not in chapter:
            errors.append(f"Work {work_idx}, Volume {vol_idx}, Chapter {chap_idx}: missing 'main_file'")

        # 检查文件存在性（如果提供了相对路径）
        main_file = chapter.get("main_file")
        if main_file and not Path(main_file).is_absolute():
            # 相对路径，暂时跳过验证（需要在运行时验证）
            pass

        return errors

    def validate_files_exist(self, base_path: Path, config: Dict[str, Any]) -> List[str]:
        """验证文件是否存在"""
        errors = []

        for work in config.get("works", []):
            for volume in work.get("volumes", []):
                for chapter in volume.get("chapters", []):
                    main_file = chapter.get("main_file")
                    if main_file:
                        file_path = Path(main_file)
                        if not file_path.is_absolute():
                            file_path = base_path / file_path
                        if not file_path.exists():
                            errors.append(f"File not found: {file_path}")

                    side_file = chapter.get("side_file")
                    if side_file:
                        file_path = Path(side_file)
                        if not file_path.is_absolute():
                            file_path = base_path / file_path
                        if not file_path.exists():
                            errors.append(f"File not found: {file_path}")

        return errors