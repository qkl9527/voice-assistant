import os
import time
import uuid
import logging
import wave
import base64
import io
import tempfile

logger = logging.getLogger(__name__)


class AudioStorage:
    """音频文件存储管理类"""

    def __init__(self, storage_dir=None):
        """初始化音频存储管理器

        Args:
            storage_dir: 音频文件存储目录，如果为None，则使用默认目录
        """
        if storage_dir is None:
            # 默认在用户目录下创建音频存储目录
            user_home = os.path.expanduser("~")
            app_data_dir = os.path.join(user_home, ".voice-assistant")
            self.storage_dir = os.path.join(app_data_dir, "audio_files")
        else:
            app_data_dir = storage_dir

        self.storage_dir = os.path.join(app_data_dir, "audio_files")

        # 确保目录存在
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)

        logger.info(f"音频存储目录: {self.storage_dir}")

    def save_audio_file(self, audio_data, mode="onetime", chunk_index=None):
        """保存音频文件

        Args:
            audio_data: 音频数据（base64编码的字符串或文件对象）
            mode: 录音模式 ('onetime' 或 'realtime')
            chunk_index: 分片索引，仅在realtime模式下使用

        Returns:
            保存的音频文件路径
        """
        try:
            # 生成唯一文件名
            timestamp = int(time.time() * 1000)
            unique_id = str(uuid.uuid4())[:8]

            if mode == "realtime" and chunk_index is not None:
                # 实时录音模式，使用分片索引
                filename = f"realtime_{timestamp}_{unique_id}_chunk_{chunk_index}.wav"
            else:
                # 一次性录音模式
                filename = f"onetime_{timestamp}_{unique_id}.wav"

            file_path = os.path.join(self.storage_dir, filename)

            # 处理不同类型的音频数据
            if isinstance(audio_data, str) and audio_data.startswith(
                ("data:", "base64:")
            ):
                # base64编码的音频数据
                self._save_base64_audio(audio_data, file_path)
            elif hasattr(audio_data, "save"):
                # Flask文件对象
                audio_data.save(file_path)
            else:
                # 其他类型，尝试直接写入
                with open(file_path, "wb") as f:
                    f.write(audio_data)

            logger.info(f"音频文件保存成功: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"保存音频文件失败: {e}")
            return None

    def _save_base64_audio(self, base64_audio, file_path):
        """保存base64编码的音频数据

        Args:
            base64_audio: base64编码的音频数据
            file_path: 保存路径
        """
        try:
            # 解码base64数据
            audio_data = base64.b64decode(
                base64_audio.split(",")[1] if "," in base64_audio else base64_audio
            )

            # 写入文件
            with open(file_path, "wb") as f:
                f.write(audio_data)

            return True
        except Exception as e:
            logger.error(f"保存base64音频失败: {e}")
            return False

    def delete_audio_file(self, file_path):
        """删除音频文件

        Args:
            file_path: 音频文件路径

        Returns:
            是否删除成功
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"删除音频文件成功: {file_path}")
                return True
            else:
                logger.warning(f"音频文件不存在: {file_path}")
                return False
        except Exception as e:
            logger.error(f"删除音频文件失败: {e}")
            return False

    def get_audio_file_path(self, filename):
        """获取音频文件的完整路径

        Args:
            filename: 文件名

        Returns:
            完整的文件路径
        """
        return os.path.join(self.storage_dir, filename)

    def base64_to_wav(self, base64_audio):
        """将base64编码的音频数据转换为临时WAV文件

        Args:
            base64_audio: base64编码的音频数据

        Returns:
            临时文件路径
        """
        try:
            # 解码base64数据
            audio_data = base64.b64decode(
                base64_audio.split(",")[1] if "," in base64_audio else base64_audio
            )

            # 创建临时文件
            temp_file = os.path.join(self.storage_dir, f"temp_audio_{time.time()}.wav")

            # 写入WAV文件
            with open(temp_file, "wb") as f:
                f.write(audio_data)

            return temp_file
        except Exception as e:
            logger.error(f"base64转WAV失败: {e}")
            return None
