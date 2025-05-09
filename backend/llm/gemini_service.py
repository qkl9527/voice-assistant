"""
Google Gemini API服务实现
"""
import logging
import json
from typing import Dict, Any, Optional
import requests
from .base import BaseLLMService

logger = logging.getLogger(__name__)

class GeminiService(BaseLLMService):
    """Google Gemini API服务实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化Google Gemini服务
        
        Args:
            config: 配置参数，包含api_key等
        """
        super().__init__(config)
        self.client = None
        self.setup_client()
        
    def setup_client(self):
        """设置Google Gemini客户端"""
        try:
            api_key = self.config.get("api_key")
            base_url = self.config.get("base_url", "https://generativelanguage.googleapis.com/v1")
            
            if not api_key:
                logger.error("Google Gemini API密钥未配置")
                self.is_available = False
                return
                
            self.api_key = api_key
            self.base_url = base_url
            self.is_available = True
            logger.info("Google Gemini客户端初始化成功")
        except Exception as e:
            logger.error(f"Google Gemini客户端初始化失败: {e}")
            self.is_available = False
            
    def check_availability(self) -> bool:
        """
        检查Google Gemini服务是否可用
        
        Returns:
            bool: 服务是否可用
        """
        if not self.is_available:
            return False
            
        try:
            # 简单的API密钥检查
            return len(self.api_key) > 10
        except Exception as e:
            logger.error(f"Google Gemini服务不可用: {e}")
            return False
            
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """
        使用Google Gemini生成文本
        
        Args:
            prompt: 提示文本
            **kwargs: 其他参数
            
        Returns:
            str: 生成的文本
        """
        if not self.is_available:
            logger.error("Google Gemini服务不可用")
            return "服务不可用，请检查API配置"
            
        try:
            # 获取模型参数
            model = kwargs.get("model") or self.config.get("model") or "gemini-pro"
            temperature = kwargs.get("temperature") or self.config.get("temperature") or 0.7
            max_tokens = kwargs.get("max_tokens") or self.config.get("max_tokens") or 1000
            
            # 构建请求URL
            url = f"{self.base_url}/models/{model}:generateContent?key={self.api_key}"
            
            # 构建请求体
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": prompt}]
                    }
                ],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens
                }
            }
            
            # 发送请求
            response = requests.post(url, json=payload)
            
            # 处理响应
            if response.status_code == 200:
                result = response.json()
                if "candidates" in result and len(result["candidates"]) > 0:
                    return result["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    logger.error(f"Google Gemini响应格式异常: {result}")
                    return "响应格式异常"
            else:
                logger.error(f"Google Gemini请求失败: {response.status_code}, {response.text}")
                return f"请求失败: {response.text}"
        except Exception as e:
            logger.error(f"Google Gemini文本生成失败: {e}")
            return f"文本生成失败: {str(e)}"
