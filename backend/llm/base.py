"""
大语言模型基础类 - 定义LLM服务的通用接口
"""
import abc
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class BaseLLMService(abc.ABC):
    """大语言模型服务基类，定义了与LLM交互的通用接口"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化LLM服务
        
        Args:
            config: LLM配置参数
        """
        self.config = config
        self.name = self.__class__.__name__
        self.is_available = False
        
    @abc.abstractmethod
    def check_availability(self) -> bool:
        """
        检查LLM服务是否可用
        
        Returns:
            bool: 服务是否可用
        """
        pass
    
    @abc.abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """
        生成文本
        
        Args:
            prompt: 提示文本
            **kwargs: 其他参数
            
        Returns:
            str: 生成的文本
        """
        pass
    
    async def fix_typos(self, text: str) -> str:
        """
        修正文本中的错别字
        
        Args:
            text: 原始文本
            
        Returns:
            str: 修正后的文本
        """
        prompt = f"""请修正以下文本中可能存在的错别字，保持原意，只返回修正后的文本：

{text}"""
        return await self.generate_text(prompt)
    
    async def polish_text(self, text: str) -> str:
        """
        润色文本
        
        Args:
            text: 原始文本
            
        Returns:
            str: 润色后的文本
        """
        prompt = f"""请润色以下文本，使其更加流畅、专业，但保持原意，只返回润色后的文本：

{text}"""
        return await self.generate_text(prompt)
    
    async def summarize(self, text: str) -> str:
        """
        概述文本内容
        
        Args:
            text: 原始文本
            
        Returns:
            str: 概述文本
        """
        prompt = f"""请简洁地概述以下文本的主要内容，只返回概述：

{text}"""
        return await self.generate_text(prompt)
    
    async def translate(self, text: str, target_language: str = "英文") -> str:
        """
        翻译文本
        
        Args:
            text: 原始文本
            target_language: 目标语言
            
        Returns:
            str: 翻译后的文本
        """
        prompt = f"""请将以下文本翻译成{target_language}，只返回翻译结果：

{text}"""
        return await self.generate_text(prompt)
