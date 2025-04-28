"""
Linux 平台的文本插入实现
"""
import logging
import pyautogui
import pyperclip
import time
import subprocess

logger = logging.getLogger(__name__)

try:
    from Xlib import display
except ImportError:
    logger.warning("Xlib 模块未安装，某些功能可能不可用")

from .base import BaseTextInserter

class LinuxTextInserter(BaseTextInserter):
    """Linux 平台的文本插入器实现"""
    
    def insert_text(self, text):
        """
        使用剪贴板和键盘快捷键在 Linux 上插入文本
        
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
            pyautogui.hotkey('ctrl', 'v')
            
            # 等待一小段时间确保粘贴完成
            time.sleep(0.1)
            
            # 恢复原始剪贴板内容
            pyperclip.copy(original_clipboard)
            
            logger.info(f"成功在 Linux 上插入文本: {text[:20]}...")
            return True
        except Exception as e:
            logger.error(f"在 Linux 上插入文本失败: {e}")
            
            # 尝试使用 xdotool 作为备选方案
            try:
                # 保存文本到临时文件
                with open('/tmp/asr_text.txt', 'w') as f:
                    f.write(text)
                
                # 使用 xdotool 模拟键盘输入
                subprocess.run(['xdotool', 'type', '--file', '/tmp/asr_text.txt'], check=True)
                logger.info(f"使用 xdotool 成功在 Linux 上插入文本: {text[:20]}...")
                return True
            except Exception as e2:
                logger.error(f"使用 xdotool 在 Linux 上插入文本失败: {e2}")
                return False
    
    def get_current_focus(self):
        """
        获取当前 Linux 焦点窗口信息
        
        Returns:
            dict: 包含当前焦点窗口信息的字典
        """
        try:
            # 使用 xdotool 获取当前窗口信息
            window_id = subprocess.check_output(['xdotool', 'getactivewindow']).decode().strip()
            window_name = subprocess.check_output(['xdotool', 'getwindowname', window_id]).decode().strip()
            window_class = subprocess.check_output(['xdotool', 'getwindowclassname', window_id]).decode().strip()
            
            return {
                'window_id': window_id,
                'window_name': window_name,
                'window_class': window_class
            }
        except Exception as e:
            logger.error(f"获取 Linux 焦点窗口信息失败: {e}")
            
            # 尝试使用 Xlib 作为备选方案
            try:
                d = display.Display()
                window = d.get_input_focus().focus
                window_name = window.get_wm_name()
                window_class = window.get_wm_class()
                
                return {
                    'window_name': window_name,
                    'window_class': window_class
                }
            except Exception as e2:
                logger.error(f"使用 Xlib 获取 Linux 焦点窗口信息失败: {e2}")
                return {
                    'error': str(e)
                }
