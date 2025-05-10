"""
LiteLLM API服务实现
"""

import logging
import json
from typing import Dict, Any, Optional
import requests
from .base import BaseLLMService

logger = logging.getLogger(__name__)


class LiteLLMService(BaseLLMService):
    """LiteLLM API服务实现"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化LiteLLM服务

        Args:
            config: 配置参数，包含api_key、base_url等
        """
        super().__init__(config)
        self.client = None
        self.setup_client()

    def setup_client(self):
        """设置LiteLLM客户端"""
        try:
            api_key = self.config.get("api_key")
            base_url = self.config.get("base_url", "http://localhost:8000")

            if not base_url:
                logger.error("LiteLLM API基础URL未配置")
                self.is_available = False
                return

            self.api_key = api_key
            self.base_url = base_url
            self.is_available = True
            logger.info("LiteLLM客户端初始化成功")
        except Exception as e:
            logger.error(f"LiteLLM客户端初始化失败: {e}")
            self.is_available = False

    def check_availability(self) -> bool:
        """
        检查LiteLLM服务是否可用

        Returns:
            bool: 服务是否可用
        """
        if not self.is_available:
            return False

        try:
            # 尝试连接LiteLLM服务
            response = requests.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"LiteLLM服务不可用: {e}")
            return False

    async def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        使用LiteLLM生成文本

        Args:
            prompt: 提示文本
            **kwargs: 其他参数

        Returns:
            Dict[str, Any]: 包含以下键的字典:
                - success (bool): 操作是否成功
                - result (str, 可选): 如果成功，返回生成的文本
                - error (str, 可选): 如果失败，返回错误信息
        """
        if not self.is_available:
            error_msg = "LiteLLM服务不可用，请检查API配置"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

        try:
            # 获取模型参数
            model = kwargs.get("model") or self.config.get("model") or "gpt-3.5-turbo"
            temperature = (
                kwargs.get("temperature") or self.config.get("temperature") or 0.7
            )
            max_tokens = (
                kwargs.get("max_tokens") or self.config.get("max_tokens") or 1000
            )

            # 构建请求URL
            url = f"{self.base_url}/chat/completions"

            # 构建请求头
            headers = {"Content-Type": "application/json"}

            # 如果有API密钥，添加到请求头
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            # 构建请求体
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "你是一个有用的助手。"},
                    {"role": "user", "content": prompt},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            # 发送请求
            response = requests.post(url, headers=headers, json=payload)

            # 处理响应
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return {
                        "success": True,
                        "result": result["choices"][0]["message"]["content"],
                    }
                else:
                    error_msg = f"LiteLLM响应格式异常: {result}"
                    logger.error(error_msg)
                    return {"success": False, "error": error_msg}
            else:
                error_msg = f"LiteLLM请求失败: {response.status_code}, {response.text}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"LiteLLM文本生成失败: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
