"""
Anthropic API服务实现
"""
import logging
import json
from typing import Dict, Any, Optional
import anthropic
from .base import BaseLLMService

logger = logging.getLogger(__name__)

class AnthropicService(BaseLLMService):
    """Anthropic API服务实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化Anthropic服务
        
        Args:
            config: 配置参数，包含api_key等
        """
        super().__init__(config)
        self.client = None
        self.setup_client()
        
    def setup_client(self):
        """设置Anthropic客户端"""
        try:
            api_key = self.config.get("api_key")
            
            if not api_key:
                logger.error("Anthropic API密钥未配置")
                self.is_available = False
                return
                
            self.client = anthropic.Anthropic(api_key=api_key)
            self.is_available = True
            logger.info("Anthropic客户端初始化成功")
        except Exception as e:
            logger.error(f"Anthropic客户端初始化失败: {e}")
            self.is_available = False
            
    def check_availability(self) -> bool:
        """
        检查Anthropic服务是否可用
        
        Returns:
            bool: 服务是否可用
        """
        if not self.is_available or not self.client:
            return False
            
        try:
            # 尝试发送一个简单的请求来检查服务是否可用
            # 注意：Anthropic API可能没有简单的健康检查端点，这里只检查客户端是否存在
            return True
        except Exception as e:
            logger.error(f"Anthropic服务不可用: {e}")
            return False
            
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """
        使用Anthropic生成文本
        
        Args:
            prompt: 提示文本
            **kwargs: 其他参数
            
        Returns:
            str: 生成的文本
        """
        if not self.is_available or not self.client:
            logger.error("Anthropic服务不可用")
            return "服务不可用，请检查API配置"
            
        try:
            # 获取模型参数
            model = kwargs.get("model") or self.config.get("model") or "claude-3-haiku-20240307"
            max_tokens = kwargs.get("max_tokens") or self.config.get("max_tokens") or 1000
            temperature = kwargs.get("temperature") or self.config.get("temperature") or 0.7
            
            # 创建消息
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system="你是一个有用的助手。",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # 提取生成的文本
            generated_text = response.content[0].text
            return generated_text
        except Exception as e:
            logger.error(f"Anthropic文本生成失败: {e}")
            return f"文本生成失败: {str(e)}"
