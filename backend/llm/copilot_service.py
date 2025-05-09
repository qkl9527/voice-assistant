"""
GitHub Copilot API服务实现
"""
import logging
import json
from typing import Dict, Any, Optional
import requests
from .base import BaseLLMService

logger = logging.getLogger(__name__)

class CopilotService(BaseLLMService):
    """GitHub Copilot API服务实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化GitHub Copilot服务
        
        Args:
            config: 配置参数，包含api_key等
        """
        super().__init__(config)
        self.client = None
        self.setup_client()
        
    def setup_client(self):
        """设置GitHub Copilot客户端"""
        try:
            api_key = self.config.get("api_key")
            base_url = self.config.get("base_url", "https://api.githubcopilot.com")
            
            if not api_key:
                logger.error("GitHub Copilot API密钥未配置")
                self.is_available = False
                return
                
            self.api_key = api_key
            self.base_url = base_url
            self.is_available = True
            logger.info("GitHub Copilot客户端初始化成功")
        except Exception as e:
            logger.error(f"GitHub Copilot客户端初始化失败: {e}")
            self.is_available = False
            
    def check_availability(self) -> bool:
        """
        检查GitHub Copilot服务是否可用
        
        Returns:
            bool: 服务是否可用
        """
        if not self.is_available:
            return False
            
        try:
            # 简单的API密钥检查
            return len(self.api_key) > 10
        except Exception as e:
            logger.error(f"GitHub Copilot服务不可用: {e}")
            return False
            
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """
        使用GitHub Copilot生成文本
        
        Args:
            prompt: 提示文本
            **kwargs: 其他参数
            
        Returns:
            str: 生成的文本
        """
        if not self.is_available:
            logger.error("GitHub Copilot服务不可用")
            return "服务不可用，请检查API配置"
            
        try:
            # 获取模型参数
            temperature = kwargs.get("temperature") or self.config.get("temperature") or 0.7
            max_tokens = kwargs.get("max_tokens") or self.config.get("max_tokens") or 1000
            
            # 构建请求URL
            url = f"{self.base_url}/v1/chat/completions"
            
            # 构建请求头
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # 构建请求体
            payload = {
                "messages": [
                    {"role": "system", "content": "你是一个有用的助手。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # 发送请求
            response = requests.post(url, headers=headers, json=payload)
            
            # 处理响应
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                else:
                    logger.error(f"GitHub Copilot响应格式异常: {result}")
                    return "响应格式异常"
            else:
                logger.error(f"GitHub Copilot请求失败: {response.status_code}, {response.text}")
                return f"请求失败: {response.text}"
        except Exception as e:
            logger.error(f"GitHub Copilot文本生成失败: {e}")
            return f"文本生成失败: {str(e)}"
