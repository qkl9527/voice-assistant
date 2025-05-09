"""
阿里云百炼API服务实现
"""
import logging
import json
from typing import Dict, Any, Optional
import requests
from .base import BaseLLMService

logger = logging.getLogger(__name__)

class QwenService(BaseLLMService):
    """阿里云百炼API服务实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化阿里云百炼服务
        
        Args:
            config: 配置参数，包含api_key等
        """
        super().__init__(config)
        self.client = None
        self.setup_client()
        
    def setup_client(self):
        """设置阿里云百炼客户端"""
        try:
            api_key = self.config.get("api_key")
            base_url = self.config.get("base_url", "https://dashscope.aliyuncs.com/api/v1")
            
            if not api_key:
                logger.error("阿里云百炼API密钥未配置")
                self.is_available = False
                return
                
            self.api_key = api_key
            self.base_url = base_url
            self.is_available = True
            logger.info("阿里云百炼客户端初始化成功")
        except Exception as e:
            logger.error(f"阿里云百炼客户端初始化失败: {e}")
            self.is_available = False
            
    def check_availability(self) -> bool:
        """
        检查阿里云百炼服务是否可用
        
        Returns:
            bool: 服务是否可用
        """
        if not self.is_available:
            return False
            
        try:
            # 简单的API密钥检查
            return len(self.api_key) > 10
        except Exception as e:
            logger.error(f"阿里云百炼服务不可用: {e}")
            return False
            
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """
        使用阿里云百炼生成文本
        
        Args:
            prompt: 提示文本
            **kwargs: 其他参数
            
        Returns:
            str: 生成的文本
        """
        if not self.is_available:
            logger.error("阿里云百炼服务不可用")
            return "服务不可用，请检查API配置"
            
        try:
            # 获取模型参数
            model = kwargs.get("model") or self.config.get("model") or "qwen-max"
            temperature = kwargs.get("temperature") or self.config.get("temperature") or 0.7
            max_tokens = kwargs.get("max_tokens") or self.config.get("max_tokens") or 1000
            
            # 构建请求URL
            url = f"{self.base_url}/services/aigc/text-generation/generation"
            
            # 构建请求头
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # 构建请求体
            payload = {
                "model": model,
                "input": {
                    "messages": [
                        {"role": "system", "content": "你是一个有用的助手。"},
                        {"role": "user", "content": prompt}
                    ]
                },
                "parameters": {
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            }
            
            # 发送请求
            response = requests.post(url, headers=headers, json=payload)
            
            # 处理响应
            if response.status_code == 200:
                result = response.json()
                if "output" in result and "text" in result["output"]:
                    return result["output"]["text"]
                else:
                    logger.error(f"阿里云百炼响应格式异常: {result}")
                    return "响应格式异常"
            else:
                logger.error(f"阿里云百炼请求失败: {response.status_code}, {response.text}")
                return f"请求失败: {response.text}"
        except Exception as e:
            logger.error(f"阿里云百炼文本生成失败: {e}")
            return f"文本生成失败: {str(e)}"
