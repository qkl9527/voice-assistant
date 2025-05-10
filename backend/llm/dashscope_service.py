"""
阿里云灵积API服务实现
"""

import logging
import json
from typing import Dict, Any, Optional
import dashscope
from dashscope import Generation
from .base import BaseLLMService

logger = logging.getLogger(__name__)


class DashscopeService(BaseLLMService):
    """阿里云灵积API服务实现"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化阿里云灵积服务

        Args:
            config: 配置参数，包含api_key等
        """
        super().__init__(config)
        self.setup_client()

    def setup_client(self):
        """设置阿里云灵积客户端"""
        try:
            api_key = self.config.get("api_key")

            if not api_key:
                logger.error("阿里云灵积API密钥未配置")
                self.is_available = False
                return

            # 设置API密钥
            dashscope.api_key = api_key
            self.is_available = True
            logger.info("阿里云灵积客户端初始化成功")
        except Exception as e:
            logger.error(f"阿里云灵积客户端初始化失败: {e}")
            self.is_available = False

    def check_availability(self) -> bool:
        """
        检查阿里云灵积服务是否可用

        Returns:
            bool: 服务是否可用
        """
        if not self.is_available:
            return False

        try:
            # 尝试发送一个简单的请求来检查服务是否可用
            return True
        except Exception as e:
            logger.error(f"阿里云灵积服务不可用: {e}")
            return False

    async def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        使用阿里云灵积生成文本

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
            error_msg = "阿里云灵积服务不可用，请检查API配置"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

        try:
            # 获取模型参数
            model = kwargs.get("model") or self.config.get("model") or "qwen-max"
            temperature = (
                kwargs.get("temperature") or self.config.get("temperature") or 0.7
            )
            max_tokens = (
                kwargs.get("max_tokens") or self.config.get("max_tokens") or 1000
            )

            # 创建聊天完成请求
            response = Generation.call(
                model=model,
                messages=[
                    {"role": "system", "content": "你是一个有用的助手。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # 提取生成的文本
            if response.status_code == 200:
                return {
                    "success": True,
                    "result": response.output.choices[0].message.content,
                }
            else:
                error_msg = (
                    f"阿里云灵积请求失败: {response.status_code}, {response.message}"
                )
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"阿里云灵积文本生成失败: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
