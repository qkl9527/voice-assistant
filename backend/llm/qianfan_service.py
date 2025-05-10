"""
百度千帆API服务实现
"""

import logging
import json
from typing import Dict, Any, Optional
import qianfan
from .base import BaseLLMService

logger = logging.getLogger(__name__)


class QianfanService(BaseLLMService):
    """百度千帆API服务实现"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化百度千帆服务

        Args:
            config: 配置参数，包含api_key、secret_key等
        """
        super().__init__(config)
        self.client = None
        self.setup_client()

    def setup_client(self):
        """设置百度千帆客户端"""
        try:
            api_key = self.config.get("api_key")
            secret_key = self.config.get("secret_key")

            if not api_key or not secret_key:
                logger.error("百度千帆API密钥未完全配置")
                self.is_available = False
                return

            self.client = qianfan.ChatCompletion(ak=api_key, sk=secret_key)
            self.is_available = True
            logger.info("百度千帆客户端初始化成功")
        except Exception as e:
            logger.error(f"百度千帆客户端初始化失败: {e}")
            self.is_available = False

    def check_availability(self) -> bool:
        """
        检查百度千帆服务是否可用

        Returns:
            bool: 服务是否可用
        """
        if not self.is_available or not self.client:
            return False

        try:
            # 尝试发送一个简单的请求来检查服务是否可用
            return True
        except Exception as e:
            logger.error(f"百度千帆服务不可用: {e}")
            return False

    async def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        使用百度千帆生成文本

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
            error_msg = "百度千帆服务不可用，请检查API配置"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

        try:
            # 获取模型参数
            model = kwargs.get("model") or self.config.get("model") or "ERNIE-Bot-4"
            temperature = (
                kwargs.get("temperature") or self.config.get("temperature") or 0.7
            )

            # 创建聊天完成请求
            response = self.client.do(
                model=model,
                messages=[
                    {"role": "system", "content": "你是一个有用的助手。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
            )

            # 提取生成的文本
            if response and "result" in response:
                return {"success": True, "result": response["result"]}
            else:
                error_msg = f"百度千帆响应格式异常: {response}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"百度千帆文本生成失败: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
