"""
智谱AI API服务实现
"""
import logging
import json
from typing import Dict, Any, Optional
import zhipuai
from .base import BaseLLMService

logger = logging.getLogger(__name__)

class ZhipuService(BaseLLMService):
    """智谱AI API服务实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化智谱AI服务
        
        Args:
            config: 配置参数，包含api_key等
        """
        super().__init__(config)
        self.client = None
        self.setup_client()
        
    def setup_client(self):
        """设置智谱AI客户端"""
        try:
            api_key = self.config.get("api_key")
            
            if not api_key:
                logger.error("智谱AI API密钥未配置")
                self.is_available = False
                return
                
            self.client = zhipuai.ZhipuAI(api_key=api_key)
            self.is_available = True
            logger.info("智谱AI客户端初始化成功")
        except Exception as e:
            logger.error(f"智谱AI客户端初始化失败: {e}")
            self.is_available = False
            
    def check_availability(self) -> bool:
        """
        检查智谱AI服务是否可用
        
        Returns:
            bool: 服务是否可用
        """
        if not self.is_available or not self.client:
            return False
            
        try:
            # 尝试发送一个简单的请求来检查服务是否可用
            return True
        except Exception as e:
            logger.error(f"智谱AI服务不可用: {e}")
            return False
            
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """
        使用智谱AI生成文本
        
        Args:
            prompt: 提示文本
            **kwargs: 其他参数
            
        Returns:
            str: 生成的文本
        """
        if not self.is_available or not self.client:
            logger.error("智谱AI服务不可用")
            return "服务不可用，请检查API配置"
            
        try:
            # 获取模型参数
            model = kwargs.get("model") or self.config.get("model") or "glm-4"
            temperature = kwargs.get("temperature") or self.config.get("temperature") or 0.7
            max_tokens = kwargs.get("max_tokens") or self.config.get("max_tokens") or 1000
            
            # 创建聊天完成请求
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是一个有用的助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # 提取生成的文本
            generated_text = response.choices[0].message.content
            return generated_text
        except Exception as e:
            logger.error(f"智谱AI文本生成失败: {e}")
            return f"文本生成失败: {str(e)}"
