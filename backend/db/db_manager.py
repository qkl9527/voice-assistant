import os
import sqlite3
import logging
import time
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (record_id) REFERENCES recognition_records (id) ON DELETE CASCADE
            )
            """
            )

            conn.commit()
            logger.info("数据库初始化成功")
        except Exception as e:
            logger.error(f"初始化数据库失败: {e}")
        finally:
            if conn:
                conn.close()

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
