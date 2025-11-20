"""
CLI 模块初始化
"""

from .parser import ArgumentParser
from .dispatcher import CommandDispatcher

__all__ = ["ArgumentParser", "CommandDispatcher"]