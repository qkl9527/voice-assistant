import os
import sys
import platform
import tempfile
import logging
import argparse
import json
from flask import Flask, request, jsonify, make_response, send_file
from flask_cors import CORS
import threading
import time
import atexit
import base64
import io
import wave
import numpy as np
from utils.postprocess_utils import format_str_v2
from db.db_manager import DBManager
from utils.audio_storage import AudioStorage
from llm.llm_service import LLMServiceManager
import traceback

# 配置huggingface加速
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 创建 Flask 应用
app = Flask(__name__)

# 配置 CORS，允许所有来源访问
# CORS(app,
#      resources={r"/*": {"origins": "*"}},
#      supports_credentials=True,
#      allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin"],
#      methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
#      max_age=86400)  # 缓存预检请求结果24小时

# 全局变量
asr_model = None
model_loading = False
model_load_error = None
is_recording = False
temp_dir = tempfile.gettempdir()

# 初始化数据库管理器和音频存储管理器（稍后会根据命令行参数重新初始化）
db_manager = None
audio_storage = None

# 初始化LLM服务管理器
llm_manager = None

# 模型参数
model_params = {
    "model": "paraformer-zh-streaming",
    "vad_model": "fsmn-vad",
    "punc_model": "ct-punc",
    "spk_model": "cam++",
    "disable_update": True,
    "device": "cuda",  # 使用 CUDA 或 CPU
    "ngpu": 0,  # GPU 设备 ID，0 表示使用第一个 GPU
    "hotwords": "",  # 热词，提高特定词汇的识别准确率
}

# 根据操作系统加载不同的文本插入模块
system = platform.system()
if system == "Windows":
    from text_inserter.windows import WindowsTextInserter as TextInserter
elif system == "Darwin":  # macOS
    from text_inserter.macos import MacOSTextInserter as TextInserter
elif system == "Linux":
    from text_inserter.linux import LinuxTextInserter as TextInserter
else:
    logger.error(f"不支持的操作系统: {system}")
    sys.exit(1)

# 初始化文本插入器
text_inserter = TextInserter()

# 预加载 FunASR 模块，避免在线程中首次导入
try:
    import torch
    import torchaudio

    logger.info("torch 版本: %s", torch.__version__)
    logger.info("torchaudio 版本: %s", torchaudio.__version__)
    import funasr

    logger.info("FunASR 模块已导入")
except ImportError as e:
    logger.error(f"导入 FunASR 模块失败: {e}")
    model_load_error = str(e)


# 延迟加载 FunASR 模型，因为它可能比较大
def load_asr_model():
    global asr_model, model_loading, model_load_error, model_params

    if model_loading:
        logger.info("模型已经在加载中...")
        return

    model_loading = True
    model_load_error = None

    try:
        import funasr

        logger.info("正在加载 FunASR 模型...")
        logger.info(f"模型参数: {model_params}")

        # 准备模型参数
        model_kwargs = {}

        # 添加模型名称
        model_kwargs["model"] = model_params["model"]

        # 添加VAD模型（如果有）
        if model_params["vad_model"]:
            model_kwargs["vad_model"] = model_params["vad_model"]

        # 添加标点模型（如果有）
        if model_params["punc_model"]:
            model_kwargs["punc_model"] = model_params["punc_model"]

        # 添加说话人分割模型（如果有）
        if model_params["spk_model"]:
            model_kwargs["spk_model"] = model_params["spk_model"]

        # 设置是否禁用自动更新
        model_kwargs["disable_update"] = model_params["disable_update"]

        # 设置设备类型（CUDA 或 CPU）
        model_kwargs["device"] = model_params["device"]

        # 设置 GPU 设备 ID
        model_kwargs["ngpu"] = model_params["ngpu"]

        # 设置热词
        if model_params["hotwords"]:
            model_kwargs["hotwords"] = model_params["hotwords"]

        logger.info(f"最终模型参数: {model_kwargs}")

        # 创建模型
        asr_model = funasr.AutoModel(**model_kwargs)

        logger.info("FunASR 模型加载完成")
        model_loading = False
        return True
    except Exception as e:
        logger.error(f"加载 FunASR 模型失败: {e}")
        model_load_error = str(e)
        model_loading = False
        return False


# 清理函数
def cleanup():
    global asr_model
    logger.info("执行清理操作...")
    # 在这里可以添加任何需要的清理代码
    asr_model = None


# 注册清理函数
atexit.register(cleanup)


# 添加 CORS 头的辅助函数
def add_cors_headers(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add(
        "Access-Control-Allow-Headers",
        "Content-Type, Authorization, X-Requested-With, Accept, Origin",
    )
    response.headers.add(
        "Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS"
    )
    response.headers.add("Access-Control-Max-Age", "86400")  # 24小时
    return response


# 全局请求前处理器，为所有响应添加 CORS 头
@app.after_request
def after_request(response):
    return add_cors_headers(response)


# 在应用启动时开始加载模型 - 使用请求处理器替代 before_first_request
@app.route("/api/status", methods=["GET"])
def status():
    """检查服务状态和模型加载情况"""
    global asr_model, model_loading, model_load_error

    # 如果模型未加载且未在加载中，启动加载
    # if asr_model is None and not model_loading and model_load_error is None:
    #     threading.Thread(target=load_asr_model).start()

    # 获取已配置的模型数量
    configured_models_count = 0
    try:
        configs = db_manager.get_llm_configs()
        configured_models_count = len([c for c in configs if c["is_configured"]])
    except Exception as e:
        logger.error(f"获取已配置的LLM模型数量失败: {e}")

    response = jsonify(
        {
            "status": "running",
            "model_loaded": asr_model is not None,
            "model_loading": model_loading,
            "model_error": model_load_error,
            "system": system,
            "configured_llm_count": configured_models_count,
        }
    )

    return response


# 将 base64 编码的音频数据转换为临时 WAV 文件
def base64_to_wav(base64_audio):
    """使用音频存储模块将base64编码的音频数据转换为临时WAV文件"""
    return audio_storage.base64_to_wav(base64_audio)


# 实时语音识别
@app.route("/api/recognize_stream", methods=["POST"])
def recognize_stream():
    """实时语音识别"""
    global asr_model, model_loading, model_load_error

    if asr_model is None:
        if model_loading:
            return jsonify({"error": "模型正在加载中，请稍后再试"}), 503
        elif model_load_error:
            return jsonify({"error": f"模型加载失败: {model_load_error}"}), 500
        else:
            # 尝试加载模型
            if not model_loading and asr_model is None:
                threading.Thread(target=load_asr_model).start()
                return (
                    jsonify({"error": "模型尚未加载，已启动加载过程，请稍后再试"}),
                    503,
                )

    # 获取请求数据
    data = request.json

    auto_insert = data.get("auto_insert", False)
    chunk_index = data.get("chunk_index", None)  # 获取分片索引
    record_id = data.get("record_id", None)  # 获取记录ID
    is_last_chunk = data.get("is_last_chunk", False)  # 是否为最后一个分片

    # 如果是最后一个分片标记请求（没有音频数据）
    if is_last_chunk and ("audio" not in data or data["audio"] is None):
        logger.info(
            f"收到最后一个分片标记，记录ID: {record_id}, 分片索引: {chunk_index}"
        )

        if record_id:
            try:
                # 获取所有分片
                chunks = db_manager.get_chunks_by_record_id(record_id)
                if chunks:
                    full_text = "".join([chunk["text"] for chunk in chunks])

                    # 更新主记录
                    conn = db_manager.get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE recognition_records SET text = ?, audio_path = ? WHERE id = ?",
                        (
                            full_text,
                            chunks[0]["audio_path"] if chunks else None,
                            record_id,
                        ),
                    )
                    conn.commit()
                    conn.close()

                    logger.info(f"已更新记录 {record_id} 的完整文本")
                    return jsonify({"success": True, "record_id": record_id})
                else:
                    logger.warning(f"记录 {record_id} 没有找到分片")
                    return jsonify({"error": "没有找到分片记录"}), 400
            except Exception as e:
                logger.error(f"处理最后一个分片标记失败: {e}")
                return jsonify({"error": f"处理最后一个分片标记失败: {str(e)}"}), 500
        else:
            return jsonify({"error": "没有提供记录ID"}), 400

    # 正常的音频处理请求
    if not data or "audio" not in data:
        return jsonify({"error": "没有提供音频数据"}), 400

    # 将 base64 音频数据转换为 WAV 文件并保存
    audio_path = audio_storage.save_audio_file(
        data["audio"], mode="realtime", chunk_index=chunk_index
    )

    if not audio_path:
        return jsonify({"error": "音频数据处理失败"}), 400

    try:
        # 使用 FunASR 进行识别
        logger.info(f"处理音频: {audio_path}")

        result = asr_model.generate(
            input=audio_path,
            language="auto",
            use_itn=True,
            hotword=model_params["hotwords"],
        )

        if model_params["model"] == "iic/SenseVoiceSmall":
            recognized_text = format_str_v2(result[0]["text"])
        else:
            recognized_text = result[0]["text"]

        if recognized_text == "":
            return jsonify(
                {
                    "success": True,
                    "text": "",
                    "record_id": record_id,
                    "chunk_index": chunk_index,
                }
            )

        # 如果需要自动插入文本
        if auto_insert:
            text_inserter.insert_text(recognized_text)

        # 保存到数据库
        if chunk_index is not None:
            # 如果是第一个分片，创建主记录
            if chunk_index == 0:
                record_id = db_manager.add_record(
                    text="", mode="realtime", is_chunked=True
                )
                logger.info(f"创建新的实时录音记录，ID: {record_id}")

            # 添加分片记录
            if record_id:
                db_manager.add_chunk(
                    record_id=record_id,
                    chunk_index=chunk_index,
                    text=recognized_text,
                    audio_path=audio_path,
                )
                logger.info(
                    f"添加分片记录，记录ID: {record_id}, 分片索引: {chunk_index}"
                )

            # 如果是最后一个分片，更新主记录的文本
            if is_last_chunk and record_id:
                # 获取所有分片
                chunks = db_manager.get_chunks_by_record_id(record_id)
                full_text = "".join([chunk["text"] for chunk in chunks])

                # 更新主记录
                conn = db_manager.get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE recognition_records SET text = ? WHERE id = ?",
                    (full_text, record_id),
                )
                conn.commit()
                conn.close()
                logger.info(f"更新记录 {record_id} 的完整文本")

        return jsonify(
            {
                "success": True,
                "text": recognized_text,
                "record_id": record_id,
                "chunk_index": chunk_index,
            }
        )
    except Exception as e:
        logger.error(f"识别失败: {e}")
        estr = str(e)
        if "ffmpeg" in estr or "Invalid data found when processing" in estr:
            return jsonify({"error": "空音频数据"}), 200
        eeee = sys.exc_info()
        return jsonify({"error": f"识别失败: {str(eeee)}"}), 500


@app.route("/api/get_last_record_id", methods=["POST", "GET"])
def get_last_record_id():
    """获取最后一个记录的ID"""
    try:
        last_record_id = db_manager.get_last_record_id()
        return jsonify({"success": True, "last_record_id": last_record_id})
    except Exception as e:
        logger.error(f"获取最后一个记录ID失败: {e}")
        return jsonify({"error": f"获取最后一个记录ID失败: {str(e)}"}), 500


@app.route("/api/recognize", methods=["POST"])
def recognize():
    """从音频文件识别文本（一次性录音模式）"""
    global asr_model

    if asr_model is None:
        if model_loading:
            return jsonify({"error": "模型正在加载中，请稍后再试"}), 503
        elif model_load_error:
            return jsonify({"error": f"模型加载失败: {model_load_error}"}), 500
        else:
            # 尝试加载模型
            threading.Thread(target=load_asr_model).start()
            return jsonify({"error": "模型尚未加载，已启动加载过程，请稍后再试"}), 503

    if "audio" not in request.files:
        return jsonify({"error": "没有提供音频文件"}), 400

    audio_file = request.files["audio"]
    auto_insert = request.form.get("auto_insert", "false").lower() == "true"

    # 保存上传的音频文件
    audio_path = audio_storage.save_audio_file(audio_file, mode="onetime")

    if not audio_path:
        return jsonify({"error": "音频文件保存失败"}), 400

    try:
        # 使用 FunASR 进行识别
        result = asr_model.generate(input=audio_path, language="zh", use_itn=True)
        recognized_text = result[0]["text"]

        # 如果需要自动插入文本
        if auto_insert:
            text_inserter.insert_text(recognized_text)

        # 保存到数据库
        record_id = db_manager.add_record(
            text=recognized_text,
            mode="onetime",
            audio_path=audio_path,
            is_chunked=False,
        )

        return jsonify(
            {"success": True, "text": recognized_text, "record_id": record_id}
        )
    except Exception as e:
        logger.error(f"识别失败: {e}")
        # 删除音频文件
        audio_storage.delete_audio_file(audio_path)
        return jsonify({"error": f"识别失败: {str(e)}"}), 500


@app.route("/api/insert_text", methods=["POST"])
def insert_text():
    """将文本插入到当前焦点位置"""
    data = request.json
    if not data or "text" not in data:
        return jsonify({"error": "没有提供文本"}), 400

    text = data["text"]
    try:
        text_inserter.insert_text(text)
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"插入文本失败: {e}")
        return jsonify({"error": f"插入文本失败: {str(e)}"}), 500


@app.route("/api/reload_model", methods=["GET"])
def reload_model():
    """重新加载模型"""
    global asr_model, model_loading

    if model_loading:
        return jsonify({"error": "模型正在加载中，请稍后再试"}), 503

    # 清除当前模型
    asr_model = None

    # 启动模型加载
    success = load_asr_model()

    if success:
        return jsonify({"success": True, "message": "模型重新加载成功"})
    else:
        return (
            jsonify(
                {"success": False, "error": f"模型重新加载失败: {model_load_error}"}
            ),
            500,
        )


# 获取历史记录
@app.route("/api/history", methods=["GET"])
def get_history():
    """获取历史记录"""
    try:
        limit = request.args.get("limit", default=100, type=int)
        records = db_manager.get_all_records(limit=limit)
        return jsonify({"success": True, "records": records})
    except Exception as e:
        logger.error(f"获取历史记录失败: {e}")
        return jsonify({"error": f"获取历史记录失败: {str(e)}"}), 500


# 删除历史记录
@app.route("/api/history/<int:record_id>", methods=["DELETE"])
def delete_history(record_id):
    """删除历史记录"""
    try:
        success = db_manager.delete_record(record_id)
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"error": "删除记录失败"}), 400
    except Exception as e:
        logger.error(f"删除历史记录失败: {e}")
        return jsonify({"error": f"删除历史记录失败: {str(e)}"}), 500


# 清空历史记录
@app.route("/api/history", methods=["DELETE"])
def clear_history():
    """清空历史记录"""
    try:
        success = db_manager.clear_all_records()
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"error": "清空记录失败"}), 400
    except Exception as e:
        logger.error(f"清空历史记录失败: {e}")
        return jsonify({"error": f"清空历史记录失败: {str(e)}"}), 500


# 获取音频文件
@app.route("/api/audio/<path:filename>", methods=["GET"])
def get_audio_file(filename):
    """获取音频文件"""
    try:
        file_path = audio_storage.get_audio_file_path(filename)
        if os.path.exists(file_path):
            return send_file(file_path, mimetype="audio/wav")
        else:
            return jsonify({"error": "音频文件不存在"}), 404
    except Exception as e:
        logger.error(f"获取音频文件失败: {e}")
        return jsonify({"error": f"获取音频文件失败: {str(e)}"}), 500


# LLM相关API端点


# 加载LLM配置
def load_llm_configs():
    """从数据库加载LLM配置"""
    global llm_manager

    try:
        # 获取所有LLM配置
        configs = db_manager.get_llm_configs()

        if not configs:
            logger.info("未找到LLM配置，使用默认配置")
            return

        # 更新LLM服务管理器配置
        for config in configs:
            provider = config["provider"]
            config_data = config["config"]
            is_default = config["is_default"]

            # 更新配置
            llm_manager.update_config(provider, config_data)

            # 如果是默认配置，设置为活动服务
            if is_default:
                llm_manager.set_active_service(provider)

        logger.info(f"已加载 {len(configs)} 个LLM配置")
    except Exception as e:
        logger.error(f"加载LLM配置失败: {e}")


@app.route("/api/llm/configs", methods=["GET"])
def get_llm_configs():
    """获取所有LLM配置"""
    try:
        configs = db_manager.get_llm_configs()

        # 移除敏感信息
        safe_configs = []
        for config in configs:
            safe_config = {
                "id": config["id"],
                "provider": config["provider"],
                "category_id": config["category_id"],
                "is_default": config["is_default"],
                "is_configured": config["is_configured"],
                "created_at": config["created_at"],
                "updated_at": config["updated_at"],
            }

            # 复制配置，但移除API密钥
            provider_config = config["config"].copy()
            if "api_key" in provider_config:
                provider_config["api_key"] = "******"
            if "secret_key" in provider_config:
                provider_config["secret_key"] = "******"

            safe_config["config"] = provider_config
            safe_configs.append(safe_config)

        return jsonify({"success": True, "configs": safe_configs})
    except Exception as e:
        logger.error(f"获取LLM配置失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/llm/configs", methods=["POST"])
def save_llm_config():
    """保存LLM配置"""
    try:
        data = request.json

        if not data or "provider" not in data or "config" not in data:
            return jsonify({"success": False, "error": "缺少必要参数"}), 400

        provider = data["provider"]
        config = data["config"]
        is_default = data.get("is_default", False)
        category_id = data.get("category_id")

        # 检查配置是否有效（例如，是否有API密钥）
        has_api_key = False

        # 获取当前配置，用于保留原有的API密钥
        current_config = db_manager.get_llm_config(provider)

        # 检查API密钥是否为屏蔽值（******）或空字符串，如果是则使用原有的值
        if "api_key" in config:
            if (
                (config["api_key"] == "******" or config["api_key"] == "")
                and current_config
                and "api_key" in current_config["config"]
            ):
                config["api_key"] = current_config["config"]["api_key"]
                logger.info(f"使用原有的API密钥值")
            if config["api_key"] and config["api_key"] != "******":
                has_api_key = True

        if "secret_key" in config:
            if (
                (config["secret_key"] == "******" or config["secret_key"] == "")
                and current_config
                and "secret_key" in current_config["config"]
            ):
                config["secret_key"] = current_config["config"]["secret_key"]
                logger.info(f"使用原有的Secret密钥值")
            if config["secret_key"] and config["secret_key"] != "******":
                has_api_key = True

        if "access_key" in config:
            if (
                (config["access_key"] == "******" or config["access_key"] == "")
                and current_config
                and "access_key" in current_config["config"]
            ):
                config["access_key"] = current_config["config"]["access_key"]
                logger.info(f"使用原有的Access Key值")

        # Ollama是本地服务，不需要API密钥
        if provider == "ollama":
            has_api_key = True

        # 获取平台信息，检查是否有model_url
        platform = db_manager.get_llm_platform(provider)
        if platform and (
            not platform.get("model_url") or platform.get("model_url").strip() == ""
        ):
            # 如果平台没有model_url值，确保模型被添加到model_json
            model = config.get("model", "")
            if model and model not in platform.get("models", []):
                logger.info(
                    f"平台 {provider} 没有model_url值，将模型 {model} 增量更新到models_json"
                )
                # 在保存配置时会自动处理增量更新

        # 保存到数据库
        config_id = db_manager.save_llm_config(
            provider=provider,
            config_json=json.dumps(config, ensure_ascii=False),
            category_id=category_id,
            is_default=is_default,
        )

        # 更新is_configured字段
        if config_id:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE llm_configs
                SET is_configured = ?
                WHERE id = ?
                """,
                (1 if has_api_key else 0, config_id),
            )
            conn.commit()
            conn.close()

        if not config_id:
            return jsonify({"success": False, "error": "保存配置失败"}), 500

        # 更新LLM服务管理器配置
        llm_manager.update_config(provider, config)

        # 如果是默认配置，设置为活动服务
        if is_default:
            llm_manager.set_active_service(provider)

        return jsonify({"success": True, "config_id": config_id})
    except Exception as e:
        logger.error(f"保存LLM配置失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/llm/configs/<provider>", methods=["DELETE"])
def delete_llm_config(provider):
    """删除LLM配置"""
    try:
        # 从数据库删除
        success = db_manager.delete_llm_config(provider)

        if not success:
            return jsonify({"success": False, "error": "删除配置失败"}), 500

        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"删除LLM配置失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/llm/process", methods=["POST"])
def process_text():
    """使用LLM处理文本"""
    try:
        data = request.json

        if not data or "text" not in data or "operation" not in data:
            return jsonify({"success": False, "error": "缺少必要参数"}), 400

        text = data["text"]
        operation = data["operation"]
        record_id = data.get("record_id")
        provider = data.get("provider")  # 可选，如果不提供则使用默认服务

        # 其他参数
        kwargs = {}
        if operation == "translate":
            kwargs["target_language"] = data.get("target_language", "英文")

        # 正确地同步调用异步函数
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                llm_manager.process_text(text, operation, **kwargs)
            )
        finally:
            loop.close()

        if not result["success"]:
            return jsonify(result), 500

        # 保存处理记录
        process_id = db_manager.add_llm_processed_text(
            original_text=text,
            processed_text=result["result"],
            operation=operation,
            provider=provider or llm_manager.active_service,
            record_id=record_id,
        )

        result["process_id"] = process_id
        return jsonify(result)
    except Exception as e:
        logger.error(f"处理文本失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/llm/processed_texts", methods=["GET"])
def get_processed_texts():
    """获取LLM处理记录"""
    try:
        limit = request.args.get("limit", default=100, type=int)
        records = db_manager.get_llm_processed_texts(limit=limit)
        return jsonify({"success": True, "records": records})
    except Exception as e:
        logger.error(f"获取LLM处理记录失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/llm/categories", methods=["GET"])
def get_llm_categories():
    """获取LLM分类列表"""
    try:
        categories = db_manager.get_llm_categories()
        return jsonify({"success": True, "categories": categories})
    except Exception as e:
        logger.error(f"获取LLM分类失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/llm/platforms", methods=["GET", "POST", "PUT", "DELETE"])
def manage_llm_platforms():
    """管理LLM平台信息"""
    if request.method == "GET":
        # 获取平台列表
        try:
            platforms = db_manager.get_llm_platforms()
            return jsonify({"success": True, "platforms": platforms})
        except Exception as e:
            logger.error(f"获取LLM平台列表失败: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    elif request.method == "POST" or request.method == "PUT":
        # 添加或更新平台
        try:
            data = request.json
            if not data or "provider" not in data or "name" not in data:
                return jsonify({"success": False, "error": "缺少必要参数"}), 400

            provider = data["provider"]
            name = data["name"]
            base_url = data.get("base_url", "")
            model_url = data.get("model_url", "")
            category_id = data.get("category_id")
            sort = data.get("sort", 0)

            platform_id = db_manager.save_llm_platform(
                provider=provider,
                name=name,
                base_url=base_url,
                model_url=model_url,
                category_id=category_id,
                sort=sort,
            )

            if platform_id:
                return jsonify({"success": True, "platform_id": platform_id})
            else:
                return jsonify({"success": False, "error": "保存平台信息失败"}), 500
        except Exception as e:
            logger.error(f"保存LLM平台信息失败: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    elif request.method == "DELETE":
        # 删除平台
        try:
            data = request.json
            if not data or "provider" not in data:
                return jsonify({"success": False, "error": "缺少必要参数"}), 400

            provider = data["provider"]

            success = db_manager.delete_llm_platform(provider)

            if success:
                return jsonify({"success": True})
            else:
                return jsonify({"success": False, "error": "删除平台信息失败"}), 500
        except Exception as e:
            logger.error(f"删除LLM平台信息失败: {e}")
            return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/llm/providers", methods=["GET"])
def get_llm_providers():
    """获取支持的LLM服务提供商列表"""
    # 是否只返回已配置的提供商
    only_configured = request.args.get("only_configured", "false").lower() == "true"

    try:
        # 从数据库获取所有平台信息
        all_platforms = db_manager.get_llm_platforms()

        # 从数据库获取所有LLM配置
        all_configs = db_manager.get_llm_configs()

        # 创建提供商ID到配置信息的映射
        config_map = {}
        for config in all_configs:
            provider = config["provider"]
            config_map[provider] = config

        # 转换为前端需要的格式，以平台为基础
        providers = []
        for platform in all_platforms:
            provider = platform["provider"]

            # 获取该平台的配置信息（如果存在）
            config = config_map.get(provider, None)

            # 确定是否已配置
            is_configured = False
            models = []
            if config:
                is_configured = config["is_configured"]
                models = config.get("config", {}).get("models", [])

            # 如果平台的models_json字段有值，优先使用它
            if platform["models"] and not models:
                models = platform["models"]

            provider_config = {
                "id": provider,
                "name": platform["name"],
                "models": models,
                "base_url_default": platform["base_url"],
                "model_url": platform["model_url"],
                "category": platform["category_id"] or "",
                "sort": platform["sort"] or 0,
                "is_configured": is_configured,
            }
            providers.append(provider_config)

        # 如果请求只返回已配置的提供商，进行过滤
        if only_configured:
            providers = [p for p in providers if p["is_configured"]]

        # 按照sort字段排序
        providers.sort(key=lambda p: (p.get("sort", 0), p["id"]))

        return jsonify({"success": True, "providers": providers})
    except Exception as e:
        logger.error(f"获取LLM提供商列表失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/llm/fetch_models", methods=["POST"])
def fetch_models():
    """从官方API获取模型列表"""
    try:
        data = request.json
        if not data or "provider" not in data:
            return jsonify({"success": False, "error": "缺少必要参数"}), 400

        provider = data["provider"]
        config = data.get("config", {})

        # 获取服务实例
        service = llm_manager.get_service(provider)
        if not service:
            # 如果服务不存在，尝试初始化
            llm_manager.update_config(provider, config)
            service = llm_manager.get_service(provider)

        if not service:
            return (
                jsonify({"success": False, "error": f"无法初始化{provider}服务"}),
                500,
            )

        # 检查服务是否可用
        if not service.check_availability():
            return (
                jsonify(
                    {"success": False, "error": f"{provider}服务不可用，请检查API配置"}
                ),
                400,
            )

        # 获取模型列表
        try:

            # 同步调用异步函数
            import asyncio

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                models = loop.run_until_complete(service.get_available_models())
            finally:
                loop.close()
            is_incremental = data.get("is_incremental", False)

            # 更新数据库中的模型列表
            if models:
                # 更新平台的模型列表
                db_manager.update_platform_models(provider, models, is_incremental)

                # 获取当前配置
                current_config = db_manager.get_llm_config(provider)
                if current_config:
                    # 更新模型列表
                    config_data = current_config["config"]
                    config_data["models"] = models

                    # 保存回数据库
                    db_manager.save_llm_config(
                        provider=provider,
                        config_json=json.dumps(config_data, ensure_ascii=False),
                        category_id=current_config.get("category_id"),
                        is_default=current_config.get("is_default", False),
                    )

            return jsonify({"success": True, "models": models})
        except Exception as e:
            logger.error(f"获取{provider}模型列表失败: {e}")
            return (
                jsonify({"success": False, "error": f"获取模型列表失败: {str(e)}"}),
                500,
            )
    except Exception as e:
        logger.error(f"获取模型列表失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# 添加一个简单的根路由，用于健康检查
@app.route("/", methods=["GET"])
def health_check():
    """健康检查端点"""
    return "ASR Service is running!"


# 处理 OPTIONS 请求
@app.route("/", defaults={"path": ""}, methods=["OPTIONS"])
@app.route("/<path:path>", methods=["OPTIONS"])
def options_handler(_):
    response = make_response()
    response.status_code = 200
    return response


if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="FunASR 语音识别服务")
    parser.add_argument("port", nargs="?", type=int, default=6100, help="服务端口号")
    parser.add_argument(
        "--model", type=str, default="paraformer-zh-streaming", help="语音识别模型"
    )
    parser.add_argument("--vad-model", type=str, default="", help="语音活动检测模型")
    parser.add_argument("--punc-model", type=str, default="", help="标点符号模型")
    parser.add_argument("--spk-model", type=str, default="", help="说话人分割模型")
    parser.add_argument(
        "--disable-update", action="store_true", help="禁用模型自动更新"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda",
        choices=["cuda", "cpu"],
        help="使用的设备类型 (cuda 或 cpu)",
    )
    parser.add_argument(
        "--ngpu", type=int, default=0, help="使用的 GPU 设备 ID (0, 1, ...)"
    )
    parser.add_argument(
        "--hotwords", type=str, default="", help="热词列表，提高特定词汇的识别准确率"
    )
    parser.add_argument(
        "--data-storage-path",
        type=str,
        default="",
        help="数据存储目录路径，用于存储音频文件和数据库",
    )

    args = parser.parse_args()

    # 更新模型参数
    model_params["model"] = args.model
    model_params["vad_model"] = args.vad_model
    model_params["punc_model"] = args.punc_model
    model_params["spk_model"] = args.spk_model
    model_params["disable_update"] = args.disable_update
    model_params["device"] = args.device
    model_params["ngpu"] = args.ngpu
    model_params["hotwords"] = args.hotwords

    # 输出模型参数
    logger.info(f"使用模型参数: {model_params}")

    # 初始化数据库管理器和音频存储管理器
    data_storage_path = args.data_storage_path if args.data_storage_path else None
    logger.info(f"数据存储目录: {data_storage_path or '默认目录'}")

    # 初始化数据库管理器和音频存储管理器
    db_manager = DBManager(db_path=data_storage_path)
    audio_storage = AudioStorage(storage_dir=data_storage_path)

    # 初始化LLM服务管理器
    llm_manager = LLMServiceManager()

    # 从数据库加载LLM配置
    load_llm_configs()

    # 获取端口参数
    port = args.port

    # 同步加载模型
    # load_asr_model()

    # 输出明确的启动信息，确保 Electron 能够捕获
    print(f"* Running on http://127.0.0.1:{port}")
    sys.stdout.flush()  # 确保输出被立即刷新

    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)
