"""
硅基流动(Moonshot) API服务实现
"""

import logging
import json
from typing import Dict, Any, Optional
import requests
from .base import BaseLLMService

logger = logging.getLogger(__name__)


class MoonshotService(BaseLLMService):
    """硅基流动(Moonshot) API服务实现"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化硅基流动服务

        Args:
            config: 配置参数，包含api_key等
        """
        super().__init__(config)
        self.client = None
        self.setup_client()

    def setup_client(self):
        """设置硅基流动客户端"""
        try:
            api_key = self.config.get("api_key")
            base_url = self.config.get("base_url", "https://api.moonshot.cn/v1")

            if not api_key:
                logger.error("硅基流动API密钥未配置")
                self.is_available = False
                return

            self.api_key = api_key
            self.base_url = base_url
            self.is_available = True
            logger.info("硅基流动客户端初始化成功")
        except Exception as e:
            logger.error(f"硅基流动客户端初始化失败: {e}")
            self.is_available = False

    def check_availability(self) -> bool:
        """
        检查硅基流动服务是否可用

        Returns:
            bool: 服务是否可用
        """
        if not self.is_available:
            return False

        try:
            # 简单的API密钥检查
            return len(self.api_key) > 10
        except Exception as e:
            logger.error(f"硅基流动服务不可用: {e}")
            return False

    async def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        使用硅基流动生成文本

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
            error_msg = "硅基流动服务不可用，请检查API配置"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

        try:
            # 获取模型参数
            model = kwargs.get("model") or self.config.get("model") or "moonshot-v1-8k"
            temperature = (
                kwargs.get("temperature") or self.config.get("temperature") or 0.7
            )
            max_tokens = (
                kwargs.get("max_tokens") or self.config.get("max_tokens") or 1000
            )

            # 构建请求URL
            url = f"{self.base_url}/chat/completions"

            # 构建请求头
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

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
                    error_msg = f"硅基流动响应格式异常: {result}"
                    logger.error(error_msg)
                    return {"success": False, "error": error_msg}
            else:
                error_msg = f"硅基流动请求失败: {response.status_code}, {response.text}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"硅基流动文本生成失败: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    async def get_available_models(self) -> list:
        """
        获取硅基流动可用的模型列表

        Returns:
            list: 模型列表
        """
        if not self.is_available:
            logger.error("硅基流动服务不可用，无法获取模型列表")
            return []

        try:
            # 构建请求URL - 获取模型列表
            url = f"{self.base_url}/models"

            # 构建请求头
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            # 发送请求
            response = requests.get(url, headers=headers)

            # 处理响应
            if response.status_code == 200:
                result = response.json()
                models = []

                # 提取模型ID
                if "data" in result:
                    for model in result["data"]:
                        if "id" in model:
                            models.append(model["id"])

                # 如果没有找到任何模型，返回默认模型列表
                if not models:
                    models = ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"]

                logger.info(f"成功获取硅基流动模型列表: {models}")
                return models
            else:
                logger.error(
                    f"硅基流动获取模型列表失败: {response.status_code}, {response.text}"
                )
                # 返回默认模型列表
                return ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"]
        except Exception as e:
            logger.error(f"获取硅基流动模型列表失败: {e}")
            # 返回默认模型列表
            return ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"]
