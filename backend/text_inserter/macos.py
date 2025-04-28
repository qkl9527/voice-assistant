"""
macOS 平台的文本插入实现
"""
import logging
import pyautogui
import pyperclip
import time
import subprocess

logger = logging.getLogger(__name__)

try:
    from AppKit import NSWorkspace
    from Quartz import (
        CGWindowListCopyWindowInfo,
        kCGWindowListOptionOnScreenOnly,
        kCGNullWindowID
    )
except ImportError:
    logger.warning("AppKit 或 Quartz 模块未安装，某些功能可能不可用")

from .base import BaseTextInserter

class MacOSTextInserter(BaseTextInserter):
    """macOS 平台的文本插入器实现"""
    
    def insert_text(self, text):
        """
        使用剪贴板和键盘快捷键在 macOS 上插入文本
        
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
            
            # 模拟 Command+V 粘贴
            pyautogui.hotkey('command', 'v')
            
            # 等待一小段时间确保粘贴完成
            time.sleep(0.1)
            
            # 恢复原始剪贴板内容
            pyperclip.copy(original_clipboard)
            
            logger.info(f"成功在 macOS 上插入文本: {text[:20]}...")
            return True
        except Exception as e:
            logger.error(f"在 macOS 上插入文本失败: {e}")
            return False
    
    def get_current_focus(self):
        """
        获取当前 macOS 焦点窗口信息
        
        Returns:
            dict: 包含当前焦点窗口信息的字典
        """
        try:
            # 获取当前活动应用
            active_app = NSWorkspace.sharedWorkspace().activeApplication()
            
            # 获取窗口信息
            window_info = CGWindowListCopyWindowInfo(
                kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
            
            # 查找活动应用的窗口
            for window in window_info:
                if window.get('kCGWindowOwnerName') == active_app['NSApplicationName']:
                    return {
                        'app_name': active_app['NSApplicationName'],
                        'window_name': window.get('kCGWindowName', ''),
                        'bundle_id': active_app['NSApplicationBundleIdentifier']
                    }
            
            return {
                'app_name': active_app['NSApplicationName'],
                'bundle_id': active_app['NSApplicationBundleIdentifier']
            }
        except Exception as e:
            logger.error(f"获取 macOS 焦点窗口信息失败: {e}")
            return {
                'error': str(e)
            }
