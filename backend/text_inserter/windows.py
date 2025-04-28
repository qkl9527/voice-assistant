"""
Windows 平台的文本插入实现
"""

import logging
import pyautogui
import pyperclip
import time

try:
    import win32gui
    import win32api
    import win32con
except ImportError:
    logging.warning("win32gui 模块未安装，某些功能可能不可用")

from .base import BaseTextInserter

logger = logging.getLogger(__name__)


class WindowsTextInserter(BaseTextInserter):
    """Windows 平台的文本插入器实现"""

    def insert_text(self, text):
        """
        使用剪贴板和键盘快捷键在 Windows 上插入文本

        Args:
            text (str): 要插入的文本

        Returns:
            bool: 是否成功插入
        """
        try:
            # 保存当前剪贴板内容
            original_clipboard = pyperclip.paste()

            # 将文本复制到剪贴板
            pyperclip.copy(text)

            # 模拟 Ctrl+V 粘贴
            pyautogui.hotkey("ctrl", "v")

            # 等待一小段时间确保粘贴完成
            time.sleep(0.1)

            # 恢复原始剪贴板内容
            pyperclip.copy(original_clipboard)

            logger.info(f"成功在 Windows 上插入文本: {text[:20]}...")
            return True
        except Exception as e:
            logger.error(f"在 Windows 上插入文本失败: {e}")
            return False

    def get_current_focus(self):
        """
        获取当前 Windows 焦点窗口信息

        Returns:
            dict: 包含当前焦点窗口信息的字典
        """
        try:
            hwnd = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)

            return {"hwnd": hwnd, "title": title, "class_name": class_name}
        except Exception as e:
            logger.error(f"获取 Windows 焦点窗口信息失败: {e}")
            return {"error": str(e)}
