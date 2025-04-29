import os
import sys
import platform
import urllib.request
import zipfile
import tarfile
import shutil
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# FFmpeg 下载链接
FFMPEG_URLS = {
    "Windows": "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
    "Darwin": "https://evermeet.cx/ffmpeg/ffmpeg-5.1.zip",  # macOS
    "Linux": "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz",
}


def get_venv_bin_dir():
    """获取虚拟环境的 bin 目录"""
    if platform.system() == "Windows":
        return os.path.join("../.venv", "Scripts")
    return os.path.join("../.venv", "bin")


def download_file(url, dest_path):
    """下载文件到指定路径"""
    logger.info(f"正在下载 FFmpeg: {url}")
    try:
        urllib.request.urlretrieve(url, dest_path)
        logger.info(f"下载完成: {dest_path}")
        return True
    except Exception as e:
        logger.error(f"下载失败: {e}")
        return False


def extract_ffmpeg(archive_path, system):
    """解压 FFmpeg 文件"""
    extract_dir = "ffmpeg_temp"
    logger.info(f"正在解压 FFmpeg: {archive_path}")

    try:
        if archive_path.endswith(".zip"):
            with zipfile.ZipFile(archive_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)
        elif archive_path.endswith(".tar.xz"):
            with tarfile.open(archive_path, "r:xz") as tar_ref:
                tar_ref.extractall(extract_dir)

        return extract_dir
    except Exception as e:
        logger.error(f"解压失败: {e}")
        return None


def setup_ffmpeg():
    """设置 FFmpeg"""
    system = platform.system()
    if system not in FFMPEG_URLS:
        logger.error(f"不支持的操作系统: {system}")
        return False

    # 创建临时下载目录
    os.makedirs("temp", exist_ok=True)

    # 下载文件
    file_ext = ".zip" if system in ["Windows", "Darwin"] else ".tar.xz"
    download_path = os.path.join("temp", f"ffmpeg{file_ext}")

    if not download_file(FFMPEG_URLS[system], download_path):
        return False

    # 解压文件
    extract_dir = extract_ffmpeg(download_path, system)
    if not extract_dir:
        return False

    try:
        # 获取 ffmpeg 可执行文件
        venv_bin_dir = get_venv_bin_dir()
        os.makedirs(venv_bin_dir, exist_ok=True)

        # 根据系统找到并复制 ffmpeg 可执行文件
        if system == "Windows":
            ffmpeg_exe = "ffmpeg.exe"
            for root, _, files in os.walk(extract_dir):
                if ffmpeg_exe in files:
                    src_path = os.path.join(root, ffmpeg_exe)
                    dst_path = os.path.join(venv_bin_dir, ffmpeg_exe)
                    shutil.copy2(src_path, dst_path)
                    break
        else:
            ffmpeg_name = "ffmpeg"
            for root, _, files in os.walk(extract_dir):
                if ffmpeg_name in files:
                    src_path = os.path.join(root, ffmpeg_name)
                    dst_path = os.path.join(venv_bin_dir, ffmpeg_name)
                    shutil.copy2(src_path, dst_path)
                    # 设置执行权限
                    os.chmod(dst_path, 0o755)
                    break

        logger.info(f"FFmpeg 已成功安装到: {venv_bin_dir}")

        # 清理临时文件
        shutil.rmtree("temp", ignore_errors=True)
        shutil.rmtree(extract_dir, ignore_errors=True)

        return True

    except Exception as e:
        logger.error(f"安装 FFmpeg 失败: {e}")
        return False


if __name__ == "__main__":
    if setup_ffmpeg():
        logger.info("FFmpeg 设置完成")
    else:
        logger.error("FFmpeg 设置失败")
        sys.exit(1)
