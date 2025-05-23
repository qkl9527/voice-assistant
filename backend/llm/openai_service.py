"""
OpenAI API服务实现
"""

import logging
import json
from typing import Dict, Any, Optional
import openai
from .base import BaseLLMService

logger = logging.getLogger(__name__)


class OpenAIService(BaseLLMService):
    """OpenAI API服务实现"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化OpenAI服务

        Args:
            config: 配置参数，包含api_key等
        """
        super().__init__(config)
        self.client = None
        self.setup_client()

    def setup_client(self):
        """设置OpenAI客户端"""
        try:
            api_key = self.config.get("api_key")
            base_url = self.config.get("base_url")

            if not api_key:
                logger.error("OpenAI API密钥未配置")
                self.is_available = False
                return

            client_kwargs = {"api_key": api_key}

            # 如果配置了自定义base_url，添加到客户端参数中
            if base_url:
                client_kwargs["base_url"] = base_url

            self.client = openai.OpenAI(**client_kwargs)
            self.is_available = True
            logger.info("OpenAI客户端初始化成功")
        except Exception as e:
            logger.error(f"OpenAI客户端初始化失败: {e}")
            self.is_available = False

    def check_availability(self) -> bool:
        """
        检查OpenAI服务是否可用

        Returns:
            bool: 服务是否可用
        """
        if not self.is_available or not self.client:
            return False

        try:
            # 尝试发送一个简单的请求来检查服务是否可用
            self.client.models.list(limit=1)
            return True
        except Exception as e:
            logger.error(f"OpenAI服务不可用: {e}")
            return False

    async def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        使用OpenAI生成文本

        Args:
            prompt: 提示文本
            **kwargs: 其他参数

        Returns:
            Dict[str, Any]: 包含以下键的字典:
                - success (bool): 操作是否成功
                - result (str, 可选): 如果成功，返回生成的文本
                - error (str, 可选): 如果失败，返回错误信息
        """
        if not self.is_available or not self.client:
            error_msg = "OpenAI服务不可用，请检查API配置"
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

            # 创建聊天完成请求
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是一个有用的助手。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # 提取生成的文本
            generated_text = response.choices[0].message.content.strip()
            return {"success": True, "result": generated_text}
        except Exception as e:
            error_msg = f"OpenAI文本生成失败: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    async def get_available_models(self) -> list:
        """
        获取OpenAI可用的模型列表

        Returns:
            list: 模型列表
        """
        if not self.is_available or not self.client:
            logger.error("OpenAI服务不可用，无法获取模型列表")
            return []

        try:
            # 获取模型列表
            models_response = self.client.models.list()

            # 提取模型ID
            models = []
            for model in models_response.data:
                # 只添加支持聊天的模型
                if "gpt" in model.id.lower():
                    models.append(model.id)

            # 如果没有找到任何模型，添加默认模型
            if not models:
                models = ["gpt-3.5-turbo", "gpt-4"]

            logger.info(f"成功获取OpenAI模型列表: {models}")
            return models
        except Exception as e:
            logger.error(f"获取OpenAI模型列表失败: {e}")
            # 返回默认模型列表
            return ["gpt-3.5-turbo", "gpt-4"]
