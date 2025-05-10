"""
LLM服务管理模块 - 管理各种LLM服务提供商
"""

import logging
import json
from typing import Dict, Any, List, Optional
import asyncio
from .base import BaseLLMService
from .openai_service import OpenAIService
from .anthropic_service import AnthropicService
from .zhipu_service import ZhipuService
from .qianfan_service import QianfanService
from .dashscope_service import DashscopeService
from .qwen_service import QwenService
from .bytedance_service import BytedanceService
from .huawei_service import HuaweiService
from .gemini_service import GeminiService
from .groq_service import GroqService
from .ollama_service import OllamaService
from .oneapi_service import OneAPIService
from .openrouter_service import OpenRouterService
from .litellm_service import LiteLLMService
from .copilot_service import CopilotService
from .aws_service import AWSService
from .azure_service import AzureService
from .moonshot_service import MoonshotService
from .deepseek_service import DeepSeekService
from .silicflow_service import SilicFlowService

logger = logging.getLogger(__name__)


class LLMServiceManager:
    """LLM服务管理器，负责管理各种LLM服务提供商"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化LLM服务管理器

        Args:
            config_path: 配置文件路径，如果为None，则使用默认配置
        """
        self.services = {}
        self.config = {}
        self.active_service = None

        # 加载配置
        if config_path:
            self.load_config(config_path)

    def load_config(self, config_path: str) -> bool:
        """
        从文件加载配置

        Args:
            config_path: 配置文件路径

        Returns:
            bool: 是否成功加载配置
        """
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)

            # 初始化服务
            self.init_services()
            return True
        except Exception as e:
            logger.error(f"加载LLM配置失败: {e}")
            return False

    def save_config(self, config_path: str) -> bool:
        """
        保存配置到文件

        Args:
            config_path: 配置文件路径

        Returns:
            bool: 是否成功保存配置
        """
        try:
            # 移除敏感信息，如API密钥
            safe_config = {}
            for provider, provider_config in self.config.items():
                safe_config[provider] = {
                    k: v
                    for k, v in provider_config.items()
                    if k != "api_key" and k != "secret_key"
                }

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(safe_config, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            logger.error(f"保存LLM配置失败: {e}")
            return False

    def update_config(self, provider: str, config: Dict[str, Any]) -> bool:
        """
        更新服务提供商配置

        Args:
            provider: 服务提供商名称
            config: 配置参数

        Returns:
            bool: 是否成功更新配置
        """
        try:
            self.config[provider] = config

            # 重新初始化服务
            self.init_service(provider)
            return True
        except Exception as e:
            logger.error(f"更新LLM配置失败: {e}")
            return False

    def init_services(self):
        """初始化所有配置的服务"""
        for provider, config in self.config.items():
            self.init_service(provider)

    def init_service(self, provider: str):
        """
        初始化指定服务提供商

        Args:
            provider: 服务提供商名称
        """
        if provider not in self.config:
            logger.error(f"未找到服务提供商配置: {provider}")
            return

        config = self.config[provider]

        try:
            # 主流大模型服务
            if provider == "openai":
                self.services[provider] = OpenAIService(config)
            elif provider == "anthropic":
                self.services[provider] = AnthropicService(config)
            elif provider == "zhipu":
                self.services[provider] = ZhipuService(config)
            elif provider == "qianfan":
                self.services[provider] = QianfanService(config)
            elif provider == "dashscope":
                self.services[provider] = DashscopeService(config)
            # 新增大模型服务
            elif provider == "qwen":
                self.services[provider] = QwenService(config)
            elif provider == "bytedance":
                self.services[provider] = BytedanceService(config)
            elif provider == "huawei":
                self.services[provider] = HuaweiService(config)
            elif provider == "gemini":
                self.services[provider] = GeminiService(config)
            elif provider == "groq":
                self.services[provider] = GroqService(config)
            elif provider == "ollama":
                self.services[provider] = OllamaService(config)
            elif provider == "oneapi":
                self.services[provider] = OneAPIService(config)
            elif provider == "openrouter":
                self.services[provider] = OpenRouterService(config)
            elif provider == "litellm":
                self.services[provider] = LiteLLMService(config)
            elif provider == "copilot":
                self.services[provider] = CopilotService(config)
            elif provider == "aws":
                self.services[provider] = AWSService(config)
            elif provider == "azure":
                self.services[provider] = AzureService(config)
            elif provider == "moonshot":
                self.services[provider] = MoonshotService(config)
            elif provider == "deepseek":
                self.services[provider] = DeepSeekService(config)
            elif provider == "silicflow":
                self.services[provider] = SilicFlowService(config)
            else:
                logger.warning(f"未知的服务提供商: {provider}")

            # 如果配置了默认服务，设置为活动服务
            if config.get("is_default", False):
                self.active_service = provider

            logger.info(f"初始化服务提供商成功: {provider}")
        except Exception as e:
            logger.error(f"初始化服务提供商失败: {provider}, 错误: {e}")

    def get_service(self, provider: Optional[str] = None) -> Optional[BaseLLMService]:
        """
        获取指定服务提供商的服务实例

        Args:
            provider: 服务提供商名称，如果为None，则返回活动服务

        Returns:
            BaseLLMService: 服务实例，如果未找到则返回None
        """
        if not provider:
            provider = self.active_service

        if not provider or provider not in self.services:
            logger.error(f"未找到服务提供商: {provider}")
            return None

        return self.services[provider]

    def set_active_service(self, provider: str) -> bool:
        """
        设置活动服务

        Args:
            provider: 服务提供商名称

        Returns:
            bool: 是否成功设置活动服务
        """
        if provider not in self.services:
            logger.error(f"未找到服务提供商: {provider}")
            return False

        self.active_service = provider

        # 更新配置
        for p in self.config:
            self.config[p]["is_default"] = p == provider

        logger.info(f"设置活动服务: {provider}")
        return True

    def get_available_services(self) -> List[str]:
        """
        获取所有可用的服务提供商

        Returns:
            List[str]: 可用的服务提供商列表
        """
        available = []
        for provider, service in self.services.items():
            if service.check_availability():
                available.append(provider)

        return available

    async def process_text(
        self, text: str, operation: str, provider: str = None, **kwargs
    ) -> Dict[str, Any]:
        """
        处理文本

        Args:
            text: 原始文本
            operation: 操作类型，如'fix_typos', 'polish_text', 'summarize', 'translate'
            **kwargs: 其他参数

        Returns:
            Dict[str, Any]: 处理结果
        """
        service = self.get_service(provider)
        if not service:
            return {"success": False, "error": "未找到可用的LLM服务"}

        try:
            if operation == "fix_typos":
                result = await service.fix_typos(text)
            elif operation == "polish_text":
                result = await service.polish_text(text)
            elif operation == "summarize":
                result = await service.summarize(text)
            elif operation == "translate":
                target_language = kwargs.get("target_language", "英文")
                result = await service.translate(text, target_language)
            else:
                return {"success": False, "error": f"不支持的操作: {operation}"}

            return {"success": True, "result": result, "original": text}
        except Exception as e:
            logger.error(f"处理文本失败: {e}")
            return {"success": False, "error": str(e)}
