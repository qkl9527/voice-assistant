import os
import sqlite3
import logging
import time
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class DBManager:
    """SQLite数据库管理类，负责初始化数据库、创建表和提供CRUD操作"""

    def __init__(self, db_path=None):
        """初始化数据库管理器

        Args:
            db_path: 数据库文件路径，如果为None，则使用默认路径
        """
        if db_path is None:
            # 默认在用户目录下创建数据库文件
            user_home = os.path.expanduser("~")
            app_data_dir = os.path.join(user_home, ".voice-assistant")
        else:
            app_data_dir = db_path

        # 确保目录存在
        if not os.path.exists(app_data_dir):
            os.makedirs(app_data_dir)

        self.db_path = os.path.join(app_data_dir, "asr_history.db")

        logger.info(f"数据库路径: {self.db_path}")

        # 初始化数据库
        self.init_db()

    def get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)

    def init_db(self):
        """初始化数据库，创建必要的表"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # 检查是否需要迁移数据
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='llm_configs'"
            )
            old_table_exists = cursor.fetchone() is not None

            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='llm_platform'"
            )
            new_table_exists = cursor.fetchone() is not None

            # 如果旧表存在但新表不存在，需要进行迁移
            need_migration = old_table_exists and not new_table_exists

            # 创建主记录表
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS recognition_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                mode TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                audio_path TEXT,
                is_chunked BOOLEAN DEFAULT 0,
                is_delete BOOLEAN DEFAULT 0
            )
            """
            )

            # 创建分片记录表
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS recognition_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                text TEXT NOT NULL,
                audio_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            )

            # 创建LLM分类表
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS llm_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            )

            # 创建LLM平台表
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS llm_platform (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                base_url TEXT,
                model_url TEXT,
                models_json TEXT,
                category_id TEXT,
                sort INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            )

            # 创建LLM配置表
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS llm_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform_id INTEGER NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                config_json TEXT NOT NULL,
                is_default BOOLEAN DEFAULT 0,
                is_configured BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            )

            # 创建LLM处理记录表
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS llm_processed_texts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id INTEGER,
                original_text TEXT NOT NULL,
                processed_text TEXT NOT NULL,
                operation TEXT NOT NULL,
                provider TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            )

            conn.commit()
            logger.info("数据库初始化成功")

            # 如果需要迁移数据，执行迁移
            if need_migration:
                self.migrate_llm_data()

            # 初始化默认的LLM分类
            self.init_default_llm_categories()

            # 初始化默认的LLM平台
            self.init_default_llm_platform()
        except Exception as e:
            logger.error(f"初始化数据库失败: {e}")
        finally:
            if conn:
                conn.close()

    def init_default_llm_categories(self):
        """初始化默认的LLM分类"""
        try:
            # 检查是否已有分类
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM llm_categories")
            count = cursor.fetchone()[0]

            if count > 0:
                logger.info(f"已存在 {count} 个LLM分类，跳过初始化默认分类")
                conn.close()
                return

            # 默认分类列表
            default_categories = [
                {"category_id": "all", "name": "全部", "description": "所有大语言模型"},
                {
                    "category_id": "international",
                    "name": "国际模型",
                    "description": "国际大语言模型服务",
                },
                {
                    "category_id": "chinese",
                    "name": "国内模型",
                    "description": "国内大语言模型服务",
                },
                {
                    "category_id": "cloud",
                    "name": "云服务",
                    "description": "云服务提供商的大语言模型",
                },
                {
                    "category_id": "local",
                    "name": "本地部署",
                    "description": "本地部署的大语言模型",
                },
                {
                    "category_id": "aggregator",
                    "name": "聚合服务",
                    "description": "聚合多个大语言模型的服务",
                },
            ]

            # 保存默认分类
            for category in default_categories:
                cursor.execute(
                    """
                    INSERT INTO llm_categories (category_id, name, description)
                    VALUES (?, ?, ?)
                    """,
                    (
                        category["category_id"],
                        category["name"],
                        category["description"],
                    ),
                )

            conn.commit()
            conn.close()
            logger.info(f"初始化了 {len(default_categories)} 个默认LLM分类")
        except Exception as e:
            logger.error(f"初始化默认LLM分类失败: {e}")
            return False

    def migrate_llm_data(self):
        """将旧的LLM配置数据迁移到新的表结构"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # 获取旧表中的所有数据
            cursor.execute(
                """
                SELECT id, provider, config_json, category_id, is_default, is_configured, created_at, updated_at
                FROM llm_configs
            """
            )

            old_configs = cursor.fetchall()

            if not old_configs:
                logger.info("没有找到需要迁移的LLM配置数据")
                return

            # 开始事务
            conn.execute("BEGIN TRANSACTION")

            # 迁移每个配置
            for config in old_configs:
                (
                    old_id,
                    provider,
                    config_json,
                    category_id,
                    is_default,
                    is_configured,
                    created_at,
                    updated_at,
                ) = config

                # 解析配置JSON
                config_data = json.loads(config_json)

                # 提取模型名称
                model = config_data.get("model", "")

                # 从配置中移除模型字段
                if "model" in config_data:
                    del config_data["model"]

                # 提取平台名称
                name = config_data.get("name", provider)

                # 提取base_url
                base_url = config_data.get("base_url", "")

                # 从配置中移除name和base_url字段
                if "name" in config_data:
                    del config_data["name"]
                if "base_url" in config_data:
                    del config_data["base_url"]

                # 重新序列化配置
                new_config_json = json.dumps(config_data, ensure_ascii=False)

                # 插入平台数据
                cursor.execute(
                    """
                    INSERT INTO llm_platform (provider, name, base_url, category_id, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (provider, name, base_url, category_id, created_at, updated_at),
                )

                # 获取新插入的平台ID
                platform_id = cursor.lastrowid

                # 插入配置数据
                cursor.execute(
                    """
                    INSERT INTO llm_configs (platform_id, model, config_json, is_default, is_configured, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        platform_id,
                        model,
                        new_config_json,
                        is_default,
                        is_configured,
                        created_at,
                        updated_at,
                    ),
                )

            # 提交事务
            conn.commit()

            logger.info(f"成功迁移 {len(old_configs)} 条LLM配置数据")

            # 重命名旧表，以备不时之需
            cursor.execute("ALTER TABLE llm_configs RENAME TO llm_configs_old")
            conn.commit()

            logger.info("旧的LLM配置表已重命名为llm_configs_old")

            return True
        except Exception as e:
            logger.error(f"LLM配置数据迁移失败: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def init_default_llm_platform(self):
        """初始化默认的LLM平台"""
        logger.info(f"初始化默认LLM平台")
        try:
            # 检查是否已有平台
            platforms = self.get_llm_platforms()

            if platforms:
                logger.info(f"已存在 {len(platforms)} 个LLM平台，跳过初始化默认平台")
                return

            # 默认平台列表
            default_platforms = [
                # OpenAI
                {
                    "provider": "openai",
                    "name": "OpenAI",
                    "base_url": "https://api.openai.com/v1",
                    "model_url": "https://api.openai.com/v1/models",
                    "category_id": "international",
                    "sort": 10,
                },
                # Anthropic
                {
                    "provider": "anthropic",
                    "name": "Anthropic",
                    "base_url": "https://api.anthropic.com",
                    "model_url": "https://api.anthropic.com/v1/models",
                    "category_id": "international",
                    "sort": 20,
                },
                # 智谱AI
                {
                    "provider": "zhipu",
                    "name": "智谱AI",
                    "base_url": "https://open.bigmodel.cn/api/paas/v4",
                    "model_url": "",
                    "category_id": "chinese",
                    "sort": 110,
                },
                # 百度千帆
                {
                    "provider": "qianfan",
                    "name": "百度千帆",
                    "base_url": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop",
                    "model_url": "",
                    "category_id": "chinese",
                    "sort": 120,
                },
                # 阿里云灵积
                {
                    "provider": "dashscope",
                    "name": "阿里云灵积",
                    "base_url": "https://dashscope.aliyuncs.com/api/v1",
                    "model_url": "",
                    "category_id": "chinese",
                    "sort": 130,
                },
                # 阿里云百炼
                {
                    "provider": "qwen",
                    "name": "阿里云百炼",
                    "base_url": "https://dashscope.aliyuncs.com/api/v1",
                    "model_url": "",
                    "category_id": "chinese",
                    "sort": 140,
                },
                # 字节跳动(豆包)
                {
                    "provider": "bytedance",
                    "name": "豆包",
                    "base_url": "https://api.doubao.com/v1",
                    "model_url": "",
                    "category_id": "chinese",
                    "sort": 150,
                },
                # 华为云
                {
                    "provider": "huawei",
                    "name": "华为云盘古",
                    "base_url": "https://huawei-llm.cn-north-4.myhuaweicloud.com",
                    "model_url": "",
                    "category_id": "chinese",
                    "sort": 160,
                },
                # Google Gemini
                {
                    "provider": "gemini",
                    "name": "Google Gemini",
                    "base_url": "https://generativelanguage.googleapis.com/v1",
                    "model_url": "",
                    "category_id": "international",
                    "sort": 30,
                },
                # Groq
                {
                    "provider": "groq",
                    "name": "Groq",
                    "base_url": "https://api.groq.com/v1",
                    "model_url": "https://api.groq.com/v1/models",
                    "category_id": "international",
                    "sort": 40,
                },
                # 硅基流动
                {
                    "provider": "moonshot",
                    "name": "硅基流动",
                    "base_url": "https://api.moonshot.cn/v1",
                    "model_url": "https://api.moonshot.cn/v1/models",
                    "category_id": "international",
                    "sort": 50,
                },
                # DeepSeek
                {
                    "provider": "deepseek",
                    "name": "DeepSeek",
                    "base_url": "https://api.deepseek.com/v1",
                    "model_url": "https://api.deepseek.com/v1/models",
                    "category_id": "international",
                    "sort": 60,
                },
                # Ollama本地
                {
                    "provider": "ollama",
                    "name": "Ollama",
                    "base_url": "http://localhost:11434/api",
                    "model_url": "http://localhost:11434/api/tags",
                    "category_id": "local",
                    "sort": 210,
                },
                # OneAPI
                {
                    "provider": "oneapi",
                    "name": "OneAPI",
                    "base_url": "https://api.oneapi.com/v1",
                    "model_url": "",
                    "category_id": "aggregator",
                    "sort": 310,
                },
                # OpenRouter
                {
                    "provider": "openrouter",
                    "name": "OpenRouter",
                    "base_url": "https://openrouter.ai/api/v1",
                    "model_url": "https://openrouter.ai/api/v1/models",
                    "category_id": "aggregator",
                    "sort": 320,
                },
                # LiteLLM
                {
                    "provider": "litellm",
                    "name": "LiteLLM",
                    "base_url": "http://localhost:8000",
                    "model_url": "http://localhost:8000/models",
                    "category_id": "aggregator",
                    "sort": 330,
                },
                # GitHub Copilot
                {
                    "provider": "copilot",
                    "name": "GitHub Copilot",
                    "base_url": "https://api.githubcopilot.com",
                    "model_url": "",
                    "category_id": "international",
                    "sort": 70,
                },
                # AWS Bedrock
                {
                    "provider": "aws",
                    "name": "AWS Bedrock",
                    "base_url": "https://bedrock-runtime.us-east-1.amazonaws.com",
                    "model_url": "",
                    "category_id": "cloud",
                    "sort": 410,
                },
                # Azure OpenAI
                {
                    "provider": "azure",
                    "name": "Azure OpenAI",
                    "base_url": "",
                    "model_url": "",
                    "category_id": "cloud",
                    "sort": 420,
                },
            ]

            # 保存默认平台
            for platform in default_platforms:
                self.save_llm_platform(
                    provider=platform["provider"],
                    name=platform["name"],
                    base_url=platform["base_url"],
                    model_url=platform["model_url"],
                    category_id=platform.get("category_id"),
                    sort=platform.get("sort", 0),
                )

            logger.info(f"初始化了 {len(default_platforms)} 个默认LLM平台")
        except Exception as e:
            logger.error(f"初始化默认LLM平台失败: {e}")
            return False

    def add_record(self, text, mode, audio_path=None, is_chunked=False):
        """添加一条识别记录

        Args:
            text: 识别的文本
            mode: 录音模式 ('onetime' 或 'realtime')
            audio_path: 音频文件路径
            is_chunked: 是否为分片录音

        Returns:
            新记录的ID
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
            INSERT INTO recognition_records (text, mode, audio_path, is_chunked, is_delete, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    text,
                    mode,
                    audio_path,
                    1 if is_chunked else 0,
                    0,
                    datetime.now().isoformat(),
                ),
            )

            record_id = cursor.lastrowid
            conn.commit()
            print(f"添加记录成功，ID: {record_id}")
            logger.info(f"添加记录成功，ID: {record_id}")
            return record_id
        except Exception as e:
            logger.error(f"添加记录失败: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def add_chunk(self, record_id, chunk_index, text, audio_path=None):
        """添加一条分片记录

        Args:
            record_id: 主记录ID
            chunk_index: 分片索引
            text: 分片识别的文本
            audio_path: 分片音频文件路径

        Returns:
            新分片记录的ID
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
            INSERT INTO recognition_chunks (record_id, chunk_index, text, audio_path, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
                (record_id, chunk_index, text, audio_path, datetime.now().isoformat()),
            )

            chunk_id = cursor.lastrowid
            conn.commit()
            logger.info(f"添加分片记录成功，ID: {chunk_id}")
            return chunk_id
        except Exception as e:
            logger.error(f"添加分片记录失败: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_all_records(self, limit=100):
        """获取所有识别记录

        Args:
            limit: 最大返回记录数

        Returns:
            记录列表
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
            SELECT id, text, mode, created_at, audio_path, is_chunked
            FROM recognition_records
            WHERE is_delete=0
            ORDER BY created_at DESC
            LIMIT ?
            """,
                (limit,),
            )

            records = []
            for row in cursor.fetchall():
                record = {
                    "id": row[0],
                    "text": row[1],
                    "mode": row[2],
                    "timestamp": row[3],
                    "audio_path": row[4],
                    "is_chunked": bool(row[5]),
                }

                # 如果是分片记录，获取所有分片
                if record["is_chunked"]:
                    record["chunks"] = self.get_chunks_by_record_id(record["id"])

                records.append(record)

            logger.info(f"获取记录成功，共 {len(records)} 条")
            return records
        except Exception as e:
            logger.error(f"获取记录失败: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_last_record_id(self):
        """获取最后一条记录id

        Returns:
            最后一条记录id
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
            SELECT id
            FROM recognition_records
            ORDER BY id DESC
            LIMIT 1
            """
            )

            record = cursor.fetchone()
            if not record:
                return 1

            logger.info(f"获取记录成功id:", record[0])
            return int(record[0]) + 1
        except Exception as e:
            logger.error(f"获取记录失败: {e}")
            return 1
        finally:
            if conn:
                conn.close()

    # LLM配置相关方法

    def save_llm_config(
        self, provider, config_json, category_id=None, is_default=False
    ):
        """保存LLM配置

        Args:
            provider: 服务提供商名称
            config_json: 配置JSON字符串
            category_id: 分类ID
            is_default: 是否为默认配置

        Returns:
            新配置的ID
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # 解析配置JSON
            config_data = json.loads(config_json)

            # 提取模型名称
            model = config_data.get("model", "")

            # 从配置中移除模型字段
            if "model" in config_data:
                del config_data["model"]

            # 重新序列化配置
            new_config_json = json.dumps(config_data, ensure_ascii=False)

            # 如果设置为默认，先将所有配置设为非默认
            if is_default:
                cursor.execute(
                    """
                UPDATE llm_configs
                SET is_default = 0
                """
                )

            # 获取平台ID
            cursor.execute(
                """
            SELECT id, model_url FROM llm_platform
            WHERE provider = ?
            """,
                (provider,),
            )

            existing_platform = cursor.fetchone()
            now = datetime.now().isoformat()

            if not existing_platform:
                logger.error(f"未找到平台记录: {provider}")
                return None

            platform_id = existing_platform[0]
            model_url = existing_platform[1]

            # 检查是否已存在该平台的配置记录
            cursor.execute(
                """
            SELECT id FROM llm_configs
            WHERE platform_id = ? AND model = ?
            """,
                (platform_id, model),
            )

            existing_model_config = cursor.fetchone()

            if existing_model_config:
                # 更新现有模型配置
                cursor.execute(
                    """
                UPDATE llm_configs
                SET config_json = ?, is_default = ?, is_configured = 1, updated_at = ?
                WHERE id = ?
                """,
                    (
                        new_config_json,
                        1 if is_default else 0,
                        now,
                        existing_model_config[0],
                    ),
                )
                config_id = existing_model_config[0]
                logger.info(f"更新现有模型配置: {provider}/{model}, ID: {config_id}")
            else:
                # 检查是否已存在该平台的任何配置记录
                cursor.execute(
                    """
                SELECT id FROM llm_configs
                WHERE platform_id = ?
                """,
                    (platform_id,),
                )

                existing_platform_config = cursor.fetchone()

                if existing_platform_config:
                    # 插入新模型配置
                    cursor.execute(
                        """
                    INSERT INTO llm_configs (provider, platform_id, model, config_json, is_default, is_configured, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            provider,
                            platform_id,
                            model,
                            new_config_json,
                            1 if is_default else 0,
                            1,  # 设置为已配置
                            now,
                            now,
                        ),
                    )
                    config_id = cursor.lastrowid
                    logger.info(f"新增模型配置: {provider}/{model}, ID: {config_id}")

                    # 如果平台没有model_url值，将新模型增量更新到model_json
                    if not model_url or model_url.strip() == "":
                        # 获取平台当前的模型列表
                        platform = self.get_llm_platform(provider)
                        if platform:
                            current_models = platform.get("models", [])
                            if model not in current_models:
                                current_models.append(model)
                                # 更新平台的模型列表
                                models_json = json.dumps(
                                    current_models, ensure_ascii=False
                                )
                                cursor.execute(
                                    """
                                    UPDATE llm_platform
                                    SET models_json = ?, updated_at = ?
                                    WHERE id = ?
                                    """,
                                    (models_json, now, platform_id),
                                )
                                logger.info(
                                    f"增量更新平台模型列表: {provider}, 添加模型: {model}"
                                )
                else:
                    # 插入新配置
                    cursor.execute(
                        """
                    INSERT INTO llm_configs (provider, platform_id, model, config_json, is_default, is_configured, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            provider,
                            platform_id,
                            model,
                            new_config_json,
                            1 if is_default else 0,
                            1,  # 设置为已配置
                            now,
                            now,
                        ),
                    )
                    config_id = cursor.lastrowid
                    logger.info(
                        f"新增平台首个配置: {provider}/{model}, ID: {config_id}"
                    )

            conn.commit()
            logger.info(f"保存LLM配置成功，ID: {config_id}")
            return config_id
        except Exception as e:
            logger.error(f"保存LLM配置失败: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_llm_configs(self):
        """获取所有LLM配置

        Returns:
            配置列表
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
            SELECT c.id, p.provider, c.model, c.config_json, p.category_id, c.is_default, c.is_configured,
                   p.name, p.base_url, p.created_at, p.updated_at
            FROM llm_configs c
            JOIN llm_platform p ON c.platform_id = p.id
            ORDER BY c.is_default DESC, p.provider ASC
            """
            )

            configs = []
            for row in cursor.fetchall():
                # 解析配置JSON
                config_data = json.loads(row[3])

                # 添加模型和平台信息到配置中
                config_data["model"] = row[2]
                config_data["name"] = row[7]
                config_data["base_url"] = row[8]

                config = {
                    "id": row[0],
                    "provider": row[1],
                    "config": config_data,
                    "category_id": row[4],
                    "is_default": bool(row[5]),
                    "is_configured": bool(row[6]),
                    "created_at": row[9],
                    "updated_at": row[10],
                }
                configs.append(config)

            logger.info(f"获取LLM配置成功，共 {len(configs)} 条")
            return configs
        except Exception as e:
            logger.error(f"获取LLM配置失败: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_llm_config(self, provider):
        """获取指定提供商的LLM配置

        Args:
            provider: 服务提供商名称

        Returns:
            指定提供商的配置，如果没有则返回None
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
            SELECT c.id, p.provider, c.model, c.config_json, p.category_id, c.is_default, c.is_configured,
                   p.name, p.base_url, p.created_at, p.updated_at
            FROM llm_configs c
            JOIN llm_platform p ON c.platform_id = p.id
            WHERE p.provider = ?
            LIMIT 1
            """,
                (provider,),
            )

            row = cursor.fetchone()
            if not row:
                return None

            # 解析配置JSON
            config_data = json.loads(row[3])

            # 添加模型和平台信息到配置中
            config_data["model"] = row[2]
            config_data["name"] = row[7]
            config_data["base_url"] = row[8]

            config = {
                "id": row[0],
                "provider": row[1],
                "config": config_data,
                "category_id": row[4],
                "is_default": bool(row[5]),
                "is_configured": bool(row[6]),
                "created_at": row[9],
                "updated_at": row[10],
            }

            logger.info(f"获取LLM配置成功: {config['provider']}")
            return config
        except Exception as e:
            logger.error(f"获取LLM配置失败: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_default_llm_config(self):
        """获取默认LLM配置

        Returns:
            默认配置，如果没有则返回None
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
            SELECT c.id, p.provider, c.model, c.config_json, p.category_id, c.is_configured,
                   p.name, p.base_url, p.created_at, p.updated_at
            FROM llm_configs c
            JOIN llm_platform p ON c.platform_id = p.id
            WHERE c.is_default = 1
            LIMIT 1
            """
            )

            row = cursor.fetchone()
            if not row:
                return None

            # 解析配置JSON
            config_data = json.loads(row[3])

            # 添加模型和平台信息到配置中
            config_data["model"] = row[2]
            config_data["name"] = row[6]
            config_data["base_url"] = row[7]

            config = {
                "id": row[0],
                "provider": row[1],
                "config": config_data,
                "category_id": row[4],
                "is_configured": bool(row[5]),
                "is_default": True,
                "created_at": row[8],
                "updated_at": row[9],
            }

            logger.info(f"获取默认LLM配置成功: {config['provider']}")
            return config
        except Exception as e:
            logger.error(f"获取默认LLM配置失败: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_llm_platforms(self):
        """获取所有LLM平台

        Returns:
            平台列表
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
            SELECT id, provider, name, base_url, model_url, models_json, category_id, sort, created_at, updated_at
            FROM llm_platform
            ORDER BY sort ASC, provider ASC
            """
            )

            platforms = []
            for row in cursor.fetchall():
                # 解析models_json
                models = []
                if row[5]:
                    try:
                        models = json.loads(row[5])
                    except:
                        logger.error(f"解析models_json失败: {row[5]}")

                platform = {
                    "id": row[0],
                    "provider": row[1],
                    "name": row[2],
                    "base_url": row[3],
                    "model_url": row[4],
                    "models": models,
                    "category_id": row[6],
                    "sort": row[7],
                    "created_at": row[8],
                    "updated_at": row[9],
                }
                platforms.append(platform)

            logger.info(f"获取LLM平台成功，共 {len(platforms)} 条")
            return platforms
        except Exception as e:
            logger.error(f"获取LLM平台失败: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_llm_platform(self, provider):
        """获取指定提供商的LLM平台信息

        Args:
            provider: 服务提供商名称

        Returns:
            指定提供商的平台信息，如果没有则返回None
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
            SELECT id, provider, name, base_url, model_url, models_json, category_id, sort, created_at, updated_at
            FROM llm_platform
            WHERE provider = ?
            LIMIT 1
            """,
                (provider,),
            )

            row = cursor.fetchone()
            if not row:
                return None

            # 解析models_json
            models = []
            if row[5]:
                try:
                    models = json.loads(row[5])
                except:
                    logger.error(f"解析models_json失败: {row[5]}")

            platform = {
                "id": row[0],
                "provider": row[1],
                "name": row[2],
                "base_url": row[3],
                "model_url": row[4],
                "models": models,
                "category_id": row[6],
                "sort": row[7],
                "created_at": row[8],
                "updated_at": row[9],
            }

            logger.info(f"获取LLM平台成功: {platform['provider']}")
            return platform
        except Exception as e:
            logger.error(f"获取LLM平台失败: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def save_llm_platform(
        self,
        provider,
        name,
        base_url="",
        model_url="",
        models_json=None,
        category_id=None,
        sort=0,
    ):
        """保存LLM平台信息

        Args:
            provider: 服务提供商名称
            name: 平台名称
            base_url: 基础URL
            model_url: 模型获取URL
            models_json: 模型列表JSON字符串
            category_id: 分类ID
            sort: 排序字段

        Returns:
            新平台的ID
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            now = datetime.now().isoformat()

            # 检查是否已存在该提供商的平台记录
            cursor.execute(
                """
            SELECT id, model_url, models_json FROM llm_platform
            WHERE provider = ?
            """,
                (provider,),
            )

            existing = cursor.fetchone()

            if existing:
                platform_id = existing[0]
                existing_model_url = existing[1]
                existing_models_json = existing[2]

                # 检查是否需要增量更新models_json
                final_models_json = models_json

                # 如果没有model_url值，并且提供了新的models_json，则进行增量更新
                if (
                    (not model_url or model_url.strip() == "")
                    and models_json
                    and existing_models_json
                ):
                    try:
                        # 解析现有模型列表
                        current_models = json.loads(existing_models_json)
                        # 解析新模型列表
                        new_models = json.loads(models_json)

                        # 增量更新：合并现有模型和新模型，去重
                        existing_model_ids = set(model for model in current_models)
                        for model in new_models:
                            if model not in existing_model_ids:
                                current_models.append(model)
                                existing_model_ids.add(model)

                        # 重新序列化
                        final_models_json = json.dumps(
                            current_models, ensure_ascii=False
                        )
                        logger.info(
                            f"增量更新平台模型列表: {provider}, 当前共有 {len(current_models)} 个模型"
                        )
                    except Exception as e:
                        logger.error(f"解析或更新models_json失败: {e}")
                        # 如果解析失败，使用原始值
                        final_models_json = models_json

                # 更新现有平台记录
                cursor.execute(
                    """
                UPDATE llm_platform
                SET name = ?, base_url = ?, model_url = ?, models_json = ?, category_id = ?, sort = ?, updated_at = ?
                WHERE provider = ?
                """,
                    (
                        name,
                        base_url,
                        model_url,
                        final_models_json,
                        category_id,
                        sort,
                        now,
                        provider,
                    ),
                )
            else:
                # 插入新平台记录
                cursor.execute(
                    """
                INSERT INTO llm_platform (provider, name, base_url, model_url, models_json, category_id, sort, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        provider,
                        name,
                        base_url,
                        model_url,
                        models_json,
                        category_id,
                        sort,
                        now,
                        now,
                    ),
                )
                platform_id = cursor.lastrowid

            conn.commit()
            logger.info(f"保存LLM平台成功，ID: {platform_id}")
            return platform_id
        except Exception as e:
            logger.error(f"保存LLM平台失败: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def update_platform_models(self, provider, models, is_incremental=False):
        """更新平台的模型列表

        Args:
            provider: 服务提供商名称
            models: 模型列表
            is_incremental: 是否增量更新，如果为True，则将新模型添加到现有列表中；如果为False，则替换现有列表

        Returns:
            是否成功更新
        """
        try:
            # 获取当前平台信息
            platform = self.get_llm_platform(provider)
            if not platform:
                logger.error(f"未找到平台: {provider}")
                return False

            # 检查平台是否有model_url值
            model_url = platform.get("model_url", "")
            force_incremental = not model_url or model_url.strip() == ""

            # 如果平台没有model_url值，强制使用增量更新
            if force_incremental:
                logger.info(f"平台 {provider} 没有model_url值，强制使用增量更新模式")
                is_incremental = True

            # 获取当前模型列表
            current_models = platform.get("models", [])

            # 根据是否增量更新决定最终的模型列表
            if is_incremental and current_models:
                # 增量更新：合并现有模型和新模型，去重
                existing_model_ids = set(model for model in current_models)
                new_models_added = 0
                for model in models:
                    if model not in existing_model_ids:
                        current_models.append(model)
                        existing_model_ids.add(model)
                        new_models_added += 1
                final_models = current_models
                logger.info(
                    f"增量更新模型列表: {provider}, 新增 {new_models_added} 个模型"
                )
            else:
                # 全量更新：直接使用新模型列表
                final_models = models
                logger.info(f"全量更新模型列表: {provider}, 共 {len(models)} 个模型")

            # 将模型列表转换为JSON字符串
            models_json = json.dumps(final_models, ensure_ascii=False)

            # 更新数据库
            conn = self.get_connection()
            cursor = conn.cursor()
            now = datetime.now().isoformat()

            cursor.execute(
                """
                UPDATE llm_platform
                SET models_json = ?, updated_at = ?
                WHERE provider = ?
                """,
                (models_json, now, provider),
            )

            conn.commit()
            conn.close()

            logger.info(
                f"更新平台模型列表成功: {provider}, 共 {len(final_models)} 个模型"
            )
            return True
        except Exception as e:
            logger.error(f"更新平台模型列表失败: {e}")
            return False

    def delete_llm_platform(self, provider):
        """删除LLM平台信息

        Args:
            provider: 服务提供商名称

        Returns:
            是否成功删除
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # 先获取平台ID
            cursor.execute(
                """
            SELECT id FROM llm_platform
            WHERE provider = ?
            """,
                (provider,),
            )

            row = cursor.fetchone()
            if not row:
                logger.info(f"未找到要删除的LLM平台: {provider}")
                return False

            platform_id = row[0]

            # 删除相关的配置
            cursor.execute(
                """
            DELETE FROM llm_configs
            WHERE platform_id = ?
            """,
                (platform_id,),
            )

            # 删除平台
            cursor.execute(
                """
            DELETE FROM llm_platform
            WHERE id = ?
            """,
                (platform_id,),
            )

            conn.commit()
            logger.info(f"删除LLM平台成功: {provider}")
            return True
        except Exception as e:
            logger.error(f"删除LLM平台失败: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def delete_llm_config(self, provider):
        """删除LLM配置

        Args:
            provider: 服务提供商名称

        Returns:
            是否成功删除
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # 先获取平台ID
            cursor.execute(
                """
            SELECT id FROM llm_platform
            WHERE provider = ?
            """,
                (provider,),
            )

            row = cursor.fetchone()
            if not row:
                logger.info(f"未找到要删除的LLM配置: {provider}")
                return False

            platform_id = row[0]

            # 删除配置
            cursor.execute(
                """
            DELETE FROM llm_configs
            WHERE platform_id = ?
            """,
                (platform_id,),
            )

            # 删除平台
            cursor.execute(
                """
            DELETE FROM llm_platform
            WHERE id = ?
            """,
                (platform_id,),
            )

            conn.commit()
            logger.info(f"删除LLM配置成功: {provider}")
            return True
        except Exception as e:
            logger.error(f"删除LLM配置失败: {e}")
            return False
        finally:
            if conn:
                conn.close()

    # LLM处理记录相关方法

    def add_llm_processed_text(
        self, original_text, processed_text, operation, provider, record_id=None
    ):
        """添加LLM处理记录

        Args:
            original_text: 原始文本
            processed_text: 处理后的文本
            operation: 操作类型
            provider: 服务提供商
            record_id: 关联的识别记录ID

        Returns:
            新记录的ID
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
            INSERT INTO llm_processed_texts (record_id, original_text, processed_text, operation, provider, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    record_id,
                    original_text,
                    processed_text,
                    operation,
                    provider,
                    datetime.now().isoformat(),
                ),
            )

            process_id = cursor.lastrowid
            conn.commit()
            logger.info(f"添加LLM处理记录成功，ID: {process_id}")
            return process_id
        except Exception as e:
            logger.error(f"添加LLM处理记录失败: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_llm_categories(self):
        """获取所有LLM分类

        Returns:
            分类列表
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
            SELECT id, category_id, name, description, created_at
            FROM llm_categories
            ORDER BY id ASC
            """
            )

            categories = []
            for row in cursor.fetchall():
                category = {
                    "id": row[0],
                    "category_id": row[1],
                    "name": row[2],
                    "description": row[3],
                    "created_at": row[4],
                }
                categories.append(category)

            logger.info(f"获取LLM分类成功，共 {len(categories)} 条")
            return categories
        except Exception as e:
            logger.error(f"获取LLM分类失败: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_llm_processed_texts(self, limit=100):
        """获取LLM处理记录

        Args:
            limit: 最大返回记录数

        Returns:
            处理记录列表
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
            SELECT id, record_id, original_text, processed_text, operation, provider, created_at
            FROM llm_processed_texts
            ORDER BY created_at DESC
            LIMIT ?
            """,
                (limit,),
            )

            records = []
            for row in cursor.fetchall():
                record = {
                    "id": row[0],
                    "record_id": row[1],
                    "original_text": row[2],
                    "processed_text": row[3],
                    "operation": row[4],
                    "provider": row[5],
                    "timestamp": row[6],
                }
                records.append(record)

            logger.info(f"获取LLM处理记录成功，共 {len(records)} 条")
            return records
        except Exception as e:
            logger.error(f"获取LLM处理记录失败: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_chunks_by_record_id(self, record_id):
        """获取指定记录的所有分片

        Args:
            record_id: 主记录ID

        Returns:
            分片记录列表
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
            SELECT id, chunk_index, text, audio_path, created_at
            FROM recognition_chunks
            WHERE record_id = ?
            ORDER BY chunk_index
            """,
                (record_id,),
            )

            chunks = []
            for row in cursor.fetchall():
                chunk = {
                    "id": row[0],
                    "chunk_index": row[1],
                    "text": row[2],
                    "audio_path": row[3],
                    "timestamp": row[4],
                }
                chunks.append(chunk)

            return chunks
        except Exception as e:
            logger.error(f"获取分片记录失败: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def delete_record(self, record_id):
        """软删除一条识别记录

        Args:
            record_id: 记录ID

        Returns:
            是否删除成功
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # 获取记录信息，包括音频文件路径
            cursor.execute(
                """
           UPDATE recognition_records
           SET is_delete = 1
           WHERE id = ?
            """,
                (record_id,),
            )

            conn.commit()
            logger.info(f"删除记录成功，ID: {record_id}")
            return True
        except Exception as e:
            logger.error(f"删除记录失败: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def clear_all_records(self):
        """软清空所有记录和相关的音频文件

        Returns:
            是否清空成功
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # 获取记录信息，包括音频文件路径
            cursor.execute(
                """
           UPDATE recognition_records
           SET is_delete = 1
           WHERE id >= 0
            """,
            )

            conn.commit()
            logger.info(f"记录已软清空")
            return True
        except Exception as e:
            logger.error(f"记录已软清空 失败: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def delete_record_concept(self, record_id):
        """删除一条识别记录及其所有分片

        Args:
            record_id: 记录ID

        Returns:
            是否删除成功
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # 获取记录信息，包括音频文件路径
            cursor.execute(
                """
            SELECT audio_path, is_chunked
            FROM recognition_records
            WHERE id = ?
            """,
                (record_id,),
            )

            record = cursor.fetchone()
            if not record:
                logger.warning(f"记录不存在: {record_id}")
                return False

            audio_path, is_chunked = record

            # 如果是分片记录，获取并删除所有分片的音频文件
            if is_chunked:
                cursor.execute(
                    """
                SELECT audio_path
                FROM recognition_chunks
                WHERE record_id = ?
                """,
                    (record_id,),
                )

                for row in cursor.fetchall():
                    chunk_audio_path = row[0]
                    if chunk_audio_path and os.path.exists(chunk_audio_path):
                        try:
                            os.remove(chunk_audio_path)
                            logger.info(f"删除分片音频文件: {chunk_audio_path}")
                        except Exception as e:
                            logger.error(f"删除分片音频文件失败: {e}")

            # 删除主记录的音频文件
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                    logger.info(f"删除音频文件: {audio_path}")
                except Exception as e:
                    logger.error(f"删除音频文件失败: {e}")

            # 删除记录（级联删除会自动删除相关的分片记录）
            cursor.execute(
                """
            DELETE FROM recognition_records
            WHERE id = ?
            """,
                (record_id,),
            )

            conn.commit()
            logger.info(f"删除记录成功，ID: {record_id}")
            return True
        except Exception as e:
            logger.error(f"删除记录失败: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def clear_all_records_concept(self):
        """清空所有记录和相关的音频文件

        Returns:
            是否清空成功
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # 获取所有音频文件路径
            cursor.execute(
                """
            SELECT audio_path FROM recognition_records
            WHERE audio_path IS NOT NULL
            """
            )

            for row in cursor.fetchall():
                audio_path = row[0]
                if audio_path and os.path.exists(audio_path):
                    try:
                        os.remove(audio_path)
                        logger.info(f"删除音频文件: {audio_path}")
                    except Exception as e:
                        logger.error(f"删除音频文件失败: {e}")

            # 获取所有分片音频文件路径
            cursor.execute(
                """
            SELECT audio_path FROM recognition_chunks
            WHERE audio_path IS NOT NULL
            """
            )

            for row in cursor.fetchall():
                audio_path = row[0]
                if audio_path and os.path.exists(audio_path):
                    try:
                        os.remove(audio_path)
                        logger.info(f"删除分片音频文件: {audio_path}")
                    except Exception as e:
                        logger.error(f"删除分片音频文件失败: {e}")

            # 清空表
            cursor.execute("DELETE FROM recognition_records")
            conn.commit()

            logger.info("清空所有记录成功")
            return True
        except Exception as e:
            logger.error(f"清空记录失败: {e}")
            return False
        finally:
            if conn:
                conn.close()
