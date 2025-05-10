"""
Azure OpenAI API服务实现
"""

import logging
import json
from typing import Dict, Any, Optional
import requests
from .base import BaseLLMService

logger = logging.getLogger(__name__)


class AzureService(BaseLLMService):
    """Azure OpenAI API服务实现"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化Azure OpenAI服务

        Args:
            config: 配置参数，包含api_key、endpoint、deployment_name等
        """
        super().__init__(config)
        self.client = None
        self.setup_client()

    def setup_client(self):
        """设置Azure OpenAI客户端"""
        try:
            api_key = self.config.get("api_key")
            endpoint = self.config.get("endpoint")
            deployment_name = self.config.get("deployment_name")
            api_version = self.config.get("api_version", "2023-05-15")

            if not api_key or not endpoint or not deployment_name:
                logger.error("Azure OpenAI配置不完整")
                self.is_available = False
                return

            self.api_key = api_key
            self.endpoint = endpoint
            self.deployment_name = deployment_name
            self.api_version = api_version
            self.is_available = True
            logger.info("Azure OpenAI客户端初始化成功")
        except Exception as e:
            logger.error(f"Azure OpenAI客户端初始化失败: {e}")
            self.is_available = False

    def check_availability(self) -> bool:
        """
        检查Azure OpenAI服务是否可用

        Returns:
            bool: 服务是否可用
        """
        if not self.is_available:
            return False

        try:
            # 简单的配置检查
            return len(self.api_key) > 10 and len(self.endpoint) > 10
        except Exception as e:
            logger.error(f"Azure OpenAI服务不可用: {e}")
            return False

    async def generate_text(self, prompt: str, **kwargs) -> str:
        """
        使用Azure OpenAI生成文本

        Args:
            prompt: 提示文本
            **kwargs: 其他参数

        Returns:
            str: 生成的文本
        """
        if not self.is_available:
            logger.error("Azure OpenAI服务不可用")
            return "服务不可用，请检查API配置"

        try:
            # 获取模型参数
            temperature = (
                kwargs.get("temperature") or self.config.get("temperature") or 0.7
            )
            max_tokens = (
                kwargs.get("max_tokens") or self.config.get("max_tokens") or 1000
            )

            # 构建请求URL
            url = f"{self.endpoint}/openai/deployments/{self.deployment_name}/chat/completions?api-version={self.api_version}"

            # 构建请求头
            headers = {"Content-Type": "application/json", "api-key": self.api_key}

            # 构建请求体
            payload = {
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
                    return result["choices"][0]["message"]["content"]
                else:
                    logger.error(f"Azure OpenAI响应格式异常: {result}")
                    return "响应格式异常"
            else:
                logger.error(
                    f"Azure OpenAI请求失败: {response.status_code}, {response.text}"
                )
                return f"请求失败: {response.text}"
        except Exception as e:
            logger.error(f"Azure OpenAI文本生成失败: {e}")
            return f"文本生成失败: {str(e)}"

    async def get_available_models(self) -> list:
        """
        获取Azure OpenAI可用的模型列表

        Returns:
            list: 模型列表
        """
        if not self.is_available:
            logger.error("Azure OpenAI服务不可用，无法获取模型列表")
            return []

        try:
            # 构建请求URL - 获取部署列表
            url = f"{self.endpoint}/openai/deployments?api-version={self.api_version}"

            # 构建请求头
            headers = {"api-key": self.api_key}

            # 发送请求
            response = requests.get(url, headers=headers)

            # 处理响应
            if response.status_code == 200:
                result = response.json()
                models = []

                # 提取部署名称
                if "data" in result:
                    for deployment in result["data"]:
                        if "id" in deployment:
                            models.append(deployment["id"])

                # 如果没有找到任何模型，返回当前配置的部署名称
                if not models and self.deployment_name:
                    models = [self.deployment_name]

                # 如果仍然没有模型，返回默认模型列表
                if not models:
                    models = ["gpt-35-turbo", "gpt-4", "gpt-4-32k"]

                logger.info(f"成功获取Azure OpenAI模型列表: {models}")
                return models
            else:
                logger.error(
                    f"Azure OpenAI获取模型列表失败: {response.status_code}, {response.text}"
                )
                # 返回当前配置的部署名称
                if self.deployment_name:
                    return [self.deployment_name]
                # 返回默认模型列表
                return ["gpt-35-turbo", "gpt-4", "gpt-4-32k"]
        except Exception as e:
            logger.error(f"获取Azure OpenAI模型列表失败: {e}")
            # 返回默认模型列表
            if self.deployment_name:
                return [self.deployment_name]
            return ["gpt-35-turbo", "gpt-4", "gpt-4-32k"]
