"""
命令行界面入口

提供 CLI 接口用于生成 HTML 文件。
"""

import sys

from .cli.parser import ArgumentParser
from .cli.dispatcher import CommandDispatcher


def main():
    """主入口函数"""
    parser = ArgumentParser()
    config = parser.parse_args()

    dispatcher = CommandDispatcher()
    dispatcher.dispatch(config)


if __name__ == "__main__":
    main()
