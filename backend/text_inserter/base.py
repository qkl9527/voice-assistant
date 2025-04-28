"""
文本插入器基类
"""
import abc
import logging

logger = logging.getLogger(__name__)

class BaseTextInserter(abc.ABC):
    """文本插入器基类，定义了插入文本的接口"""
    
    @abc.abstractmethod
    def insert_text(self, text):
        """
        将文本插入到当前系统焦点位置
        
        Args:
            text (str): 要插入的文本
            
        Returns:
            bool: 是否成功插入
        """
        pass
    
    @abc.abstractmethod
    def get_current_focus(self):
        """
        获取当前系统焦点信息
        
        Returns:
            dict: 包含当前焦点信息的字典
        """
        pass
