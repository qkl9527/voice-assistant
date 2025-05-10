"""
DeepSeek API服务实现
"""

import logging
import json
from typing import Dict, Any, Optional, List
import requests
from .base import BaseLLMService

logger = logging.getLogger(__name__)


class DeepSeekService(BaseLLMService):
    """DeepSeek API服务实现"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化DeepSeek服务

        Args:
            config: 配置参数，包含api_key、base_url等
        """
        super().__init__(config)
        self.client = None
        self.setup_client()

    def setup_client(self):
        """设置DeepSeek客户端"""
        try:
            api_key = self.config.get("api_key")
            base_url = self.config.get("base_url", "https://api.deepseek.com")

            if not api_key:
                logger.error("DeepSeek API密钥未配置")
                self.is_available = False
                return

            self.api_key = api_key
            self.base_url = base_url
            self.is_available = True
            logger.info("DeepSeek客户端初始化成功")
        except Exception as e:
            logger.error(f"DeepSeek客户端初始化失败: {e}")
            self.is_available = False

    def check_availability(self) -> bool:
        """
        检查DeepSeek服务是否可用

        Returns:
            bool: 服务是否可用
        """
        if not self.is_available:
            return False

        try:
            # 简单的API密钥检查
            return len(self.api_key) > 10
        except Exception as e:
            logger.error(f"DeepSeek服务不可用: {e}")
            return False

    async def generate_text(self, prompt: str, **kwargs) -> str:
        """
        使用DeepSeek生成文本

        Args:
            prompt: 提示文本
            **kwargs: 其他参数

        Returns:
            str: 生成的文本
        """
        if not self.is_available:
            logger.error("DeepSeek服务不可用")
            return "服务不可用，请检查API配置"

        try:
            # 获取模型参数
            model = kwargs.get("model") or self.config.get("model") or "deepseek-chat"
            temperature = kwargs.get("temperature") or self.config.get("temperature") or 0.7
            max_tokens = kwargs.get("max_tokens") or self.config.get("max_tokens") or 1000

            # 构建请求URL
            url = f"{self.base_url}/v1/chat/completions"

            # 构建请求头
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            # 构建请求体
            payload = {
                "model": model,
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
                    logger.error(f"DeepSeek响应格式异常: {result}")
                    return "响应格式异常"
            else:
                logger.error(f"DeepSeek请求失败: {response.status_code}, {response.text}")
                return f"请求失败: {response.text}"
        except Exception as e:
            logger.error(f"DeepSeek文本生成失败: {e}")
            return f"文本生成失败: {str(e)}"

    async def get_available_models(self) -> List[str]:
        """
        获取DeepSeek可用的模型列表

        Returns:
            List[str]: 模型列表
        """
        if not self.is_available:
            logger.error("DeepSeek服务不可用，无法获取模型列表")
            return []

        try:
            # 构建请求URL
            url = f"{self.base_url}/v1/models"

            # 构建请求头
            headers = {"Authorization": f"Bearer {self.api_key}"}

            # 发送请求
            response = requests.get(url, headers=headers)

            # 处理响应
            if response.status_code == 200:
                result = response.json()
                models = []

                # 提取模型ID
                if "data" in result:
                    for model_info in result["data"]:
                        if "id" in model_info:
                            models.append(model_info["id"])

                # 如果没有找到任何模型，返回默认模型列表
                if not models:
                    models = [
                        "deepseek-chat",
                        "deepseek-coder",
                        "deepseek-v2",
                        "deepseek-lite"
                    ]

                logger.info(f"成功获取DeepSeek模型列表: {models}")
                return models
            else:
                logger.error(f"DeepSeek获取模型列表失败: {response.status_code}, {response.text}")
                # 返回默认模型列表
                return [
                    "deepseek-chat",
                    "deepseek-coder",
                    "deepseek-v2",
                    "deepseek-lite"
                ]
        except Exception as e:
            logger.error(f"获取DeepSeek模型列表失败: {e}")
            # 返回默认模型列表
            return [
                "deepseek-chat",
                "deepseek-coder",
                "deepseek-v2",
                "deepseek-lite"
            ]
