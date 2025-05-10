"""
AWS Bedrock API服务实现
"""

import logging
import json
from typing import Dict, Any, Optional
import requests
from .base import BaseLLMService

logger = logging.getLogger(__name__)


class AWSService(BaseLLMService):
    """AWS Bedrock API服务实现"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化AWS Bedrock服务

        Args:
            config: 配置参数，包含access_key、secret_key、region等
        """
        super().__init__(config)
        self.client = None
        self.setup_client()

    def setup_client(self):
        """设置AWS Bedrock客户端"""
        try:
            access_key = self.config.get("access_key")
            secret_key = self.config.get("secret_key")
            region = self.config.get("region", "us-east-1")
            base_url = self.config.get("base_url")

            if not access_key or not secret_key:
                logger.error("AWS Bedrock访问密钥未完全配置")
                self.is_available = False
                return

            self.access_key = access_key
            self.secret_key = secret_key
            self.region = region

            # 如果提供了自定义base_url，使用它
            if base_url:
                self.base_url = base_url
            else:
                self.base_url = f"https://bedrock-runtime.{region}.amazonaws.com"

            self.is_available = True
            logger.info("AWS Bedrock客户端初始化成功")
        except Exception as e:
            logger.error(f"AWS Bedrock客户端初始化失败: {e}")
            self.is_available = False

    def check_availability(self) -> bool:
        """
        检查AWS Bedrock服务是否可用

        Returns:
            bool: 服务是否可用
        """
        if not self.is_available:
            return False

        try:
            # 简单的密钥检查
            return len(self.access_key) > 10 and len(self.secret_key) > 10
        except Exception as e:
            logger.error(f"AWS Bedrock服务不可用: {e}")
            return False

    async def generate_text(self, prompt: str, **kwargs) -> str:
        """
        使用AWS Bedrock生成文本

        Args:
            prompt: 提示文本
            **kwargs: 其他参数

        Returns:
            str: 生成的文本
        """
        if not self.is_available:
            logger.error("AWS Bedrock服务不可用")
            return "服务不可用，请检查API配置"

        try:
            # 获取模型参数
            model = (
                kwargs.get("model") or self.config.get("model") or "anthropic.claude-v2"
            )
            temperature = (
                kwargs.get("temperature") or self.config.get("temperature") or 0.7
            )
            max_tokens = (
                kwargs.get("max_tokens") or self.config.get("max_tokens") or 1000
            )

            # 根据模型类型构建不同的请求体
            if "anthropic" in model:
                # Anthropic Claude模型
                payload = {
                    "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
                    "max_tokens_to_sample": max_tokens,
                    "temperature": temperature,
                }
            elif "amazon" in model:
                # Amazon Titan模型
                payload = {
                    "inputText": prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": max_tokens,
                        "temperature": temperature,
                    },
                }
            elif "ai21" in model:
                # AI21 Jurassic模型
                payload = {
                    "prompt": prompt,
                    "maxTokens": max_tokens,
                    "temperature": temperature,
                }
            elif "cohere" in model:
                # Cohere模型
                payload = {
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                }
            else:
                # 默认格式
                payload = {
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                }

            # 构建AWS签名请求（简化版，实际应用中需要完整的AWS签名V4）
            # 注意：这里简化了AWS签名过程，实际应用中应使用boto3或其他AWS SDK
            headers = {
                "Content-Type": "application/json",
                "X-Amz-Content-Sha256": "required",
                "X-Amz-Date": "required",
                "Authorization": "AWS4-HMAC-SHA256 Credential=required",
            }

            # 发送请求
            url = f"{self.base_url}/model/{model}/invoke"
            response = requests.post(url, headers=headers, json=payload)

            # 处理响应
            if response.status_code == 200:
                result = response.json()

                # 根据模型类型解析不同的响应格式
                if "anthropic" in model:
                    return result.get("completion", "")
                elif "amazon" in model:
                    return result.get("results", [{}])[0].get("outputText", "")
                elif "ai21" in model:
                    return (
                        result.get("completions", [{}])[0]
                        .get("data", {})
                        .get("text", "")
                    )
                elif "cohere" in model:
                    return result.get("generations", [{}])[0].get("text", "")
                else:
                    return str(result)
            else:
                logger.error(
                    f"AWS Bedrock请求失败: {response.status_code}, {response.text}"
                )
                return f"请求失败: {response.text}"
        except Exception as e:
            logger.error(f"AWS Bedrock文本生成失败: {e}")
            return f"文本生成失败: {str(e)}"

    async def get_available_models(self) -> list:
        """
        获取AWS Bedrock可用的模型列表

        Returns:
            list: 模型列表
        """
        if not self.is_available:
            logger.error("AWS Bedrock服务不可用，无法获取模型列表")
            return []

        try:
            # AWS Bedrock的模型列表是相对固定的，这里返回常用模型
            # 实际应用中应该通过AWS SDK获取可用模型列表
            models = [
                "anthropic.claude-v2",
                "anthropic.claude-v2:1",
                "anthropic.claude-instant-v1",
                "amazon.titan-text-express-v1",
                "amazon.titan-text-lite-v1",
                "ai21.j2-ultra-v1",
                "ai21.j2-mid-v1",
                "cohere.command-text-v14",
                "cohere.command-light-text-v14",
                "meta.llama2-13b-chat-v1",
                "meta.llama2-70b-chat-v1",
            ]

            logger.info(f"成功获取AWS Bedrock模型列表: {models}")
            return models
        except Exception as e:
            logger.error(f"获取AWS Bedrock模型列表失败: {e}")
            # 返回默认模型列表
            return ["anthropic.claude-v2", "amazon.titan-text-express-v1"]
