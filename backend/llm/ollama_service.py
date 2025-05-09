"""
Ollama API服务实现
"""
import logging
import json
from typing import Dict, Any, Optional
import requests
from .base import BaseLLMService

logger = logging.getLogger(__name__)

class OllamaService(BaseLLMService):
    """Ollama API服务实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化Ollama服务
        
        Args:
            config: 配置参数，包含base_url等
        """
        super().__init__(config)
        self.client = None
        self.setup_client()
        
    def setup_client(self):
        """设置Ollama客户端"""
        try:
            base_url = self.config.get("base_url", "http://localhost:11434/api")
            
            self.base_url = base_url
            self.is_available = True
            logger.info("Ollama客户端初始化成功")
        except Exception as e:
            logger.error(f"Ollama客户端初始化失败: {e}")
            self.is_available = False
            
    def check_availability(self) -> bool:
        """
        检查Ollama服务是否可用
        
        Returns:
            bool: 服务是否可用
        """
        if not self.is_available:
            return False
            
        try:
            # 尝试连接Ollama服务
            response = requests.get(f"{self.base_url}/tags")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama服务不可用: {e}")
            return False
            
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """
        使用Ollama生成文本
        
        Args:
            prompt: 提示文本
            **kwargs: 其他参数
            
        Returns:
            str: 生成的文本
        """
        if not self.is_available:
            logger.error("Ollama服务不可用")
            return "服务不可用，请检查API配置"
            
        try:
            # 获取模型参数
            model = kwargs.get("model") or self.config.get("model") or "llama3"
            temperature = kwargs.get("temperature") or self.config.get("temperature") or 0.7
            
            # 构建请求URL
            url = f"{self.base_url}/chat"
            
            # 构建请求体
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "你是一个有用的助手。"},
                    {"role": "user", "content": prompt}
                ],
                "options": {
                    "temperature": temperature
                }
            }
            
            # 发送请求
            response = requests.post(url, json=payload)
            
            # 处理响应
            if response.status_code == 200:
                result = response.json()
                if "message" in result and "content" in result["message"]:
                    return result["message"]["content"]
                else:
                    logger.error(f"Ollama响应格式异常: {result}")
                    return "响应格式异常"
            else:
                logger.error(f"Ollama请求失败: {response.status_code}, {response.text}")
                return f"请求失败: {response.text}"
        except Exception as e:
            logger.error(f"Ollama文本生成失败: {e}")
            return f"文本生成失败: {str(e)}"
