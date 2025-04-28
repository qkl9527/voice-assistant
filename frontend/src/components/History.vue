<script setup>
import { ref, computed, onMounted } from "vue";

const props = defineProps({
  apiBaseUrl: String,
  onSelect: Function,
  onDelete: Function,
  onClear: Function,
});

// 历史记录数据
const records = ref([]);
const loading = ref(false);
const error = ref(null);

// 音频播放
const currentAudio = ref(null);
const isPlaying = ref(false);
const expandedRecordId = ref(null);
const playingRecordId = ref(null); // 当前正在播放的记录ID
const playingChunkId = ref(null); // 当前正在播放的分片ID

// 搜索功能
const searchQuery = ref("");
const filteredRecords = computed(() => {
  if (!searchQuery.value.trim()) {
    return records.value;
  }

  const query = searchQuery.value.toLowerCase();
  return records.value.filter(
    (record) =>
      record.text.toLowerCase().includes(query) ||
      new Date(record.timestamp)
        .toLocaleString()
        .toLowerCase()
        .includes(query) ||
      record.mode.toLowerCase().includes(query)
  );
});

// 加载历史记录
async function loadRecords() {
  loading.value = true;
  error.value = null;

  try {
    const response = await fetch(`${props.apiBaseUrl}/api/history`);
    if (!response.ok) {
      throw new Error(`加载历史记录失败: ${response.status}`);
    }

    const data = await response.json();
    if (data.success && data.records) {
      records.value = data.records;
    } else {
      throw new Error(data.error || "加载历史记录失败");
    }
  } catch (err) {
    console.error("加载历史记录失败:", err);
    error.value = err.message;
  } finally {
    loading.value = false;
  }
}

// 删除历史记录
async function deleteRecord(recordId) {
  try {
    const response = await fetch(
      `${props.apiBaseUrl}/api/history/${recordId}`,
      {
        method: "DELETE",
      }
    );

    if (!response.ok) {
      throw new Error(`删除记录失败: ${response.status}`);
    }

    const data = await response.json();
    if (data.success) {
      // 从本地列表中移除
      records.value = records.value.filter((record) => record.id !== recordId);

      // 如果有回调函数，调用它
      if (props.onDelete) {
        props.onDelete(recordId);
      }
    } else {
      throw new Error(data.error || "删除记录失败");
    }
  } catch (err) {
    console.error("删除记录失败:", err);
    alert(`删除记录失败: ${err.message}`);
  }
}

// 清空历史记录
async function clearAllRecords() {
  if (!confirm("确定要清空所有历史记录吗？此操作不可撤销。")) {
    return;
  }

  try {
    const response = await fetch(`${props.apiBaseUrl}/api/history`, {
      method: "DELETE",
    });

    if (!response.ok) {
      throw new Error(`清空记录失败: ${response.status}`);
    }

    const data = await response.json();
    if (data.success) {
      // 清空本地列表
      records.value = [];

      // 如果有回调函数，调用它
      if (props.onClear) {
        props.onClear();
      }
    } else {
      throw new Error(data.error || "清空记录失败");
    }
  } catch (err) {
    console.error("清空记录失败:", err);
    alert(`清空记录失败: ${err.message}`);
  }
}

// 播放音频
function playAudio(record) {
  // 如果当前有音频在播放，先停止
  if (currentAudio.value) {
    currentAudio.value.pause();
    currentAudio.value = null;
    isPlaying.value = false;
    playingRecordId.value = null;
    playingChunkId.value = null;
  }

  // 获取音频文件路径
  let audioPath;
  if (record.is_chunked) {
    // 如果是分片录音，播放第一个分片
    if (record.chunks && record.chunks.length > 0) {
      const chunk = record.chunks[0];
      audioPath = chunk.audio_path;
    } else {
      console.error("没有找到分片音频");
      return;
    }
  } else {
    // 一次性录音
    audioPath = record.audio_path;
  }

  if (!audioPath) {
    console.error("没有音频文件路径");
    return;
  }

  // 提取文件名
  const filename = audioPath.split("/").pop();

  // 创建音频元素
  const audio = new Audio(`${props.apiBaseUrl}/api/audio/${filename}`);
  currentAudio.value = audio;
  playingRecordId.value = record.id;

  // 监听播放结束事件
  audio.addEventListener("ended", () => {
    isPlaying.value = false;
    playingRecordId.value = null;
    playingChunkId.value = null;
  });

  // 开始播放
  audio.play();
  isPlaying.value = true;
}

// 播放特定分片的音频
function playChunkAudio(chunk, recordId) {
  // 如果当前有音频在播放，先停止
  if (currentAudio.value) {
    currentAudio.value.pause();
    currentAudio.value = null;
    isPlaying.value = false;
    playingRecordId.value = null;
    playingChunkId.value = null;
  }

  // 获取音频文件路径
  const audioPath = chunk.audio_path;
  if (!audioPath) {
    console.error("没有分片音频文件路径");
    return;
  }

  // 提取文件名
  const filename = audioPath.split("/").pop();

  // 创建音频元素
  const audio = new Audio(`${props.apiBaseUrl}/api/audio/${filename}`);
  currentAudio.value = audio;
  playingRecordId.value = recordId;
  playingChunkId.value = chunk.id;

  // 监听播放结束事件
  audio.addEventListener("ended", () => {
    isPlaying.value = false;
    playingRecordId.value = null;
    playingChunkId.value = null;
  });

  // 开始播放
  audio.play();
  isPlaying.value = true;
}

// 停止播放
function stopAudio() {
  if (currentAudio.value) {
    currentAudio.value.pause();
    currentAudio.value = null;
    isPlaying.value = false;
    playingRecordId.value = null;
    playingChunkId.value = null;
  }
}

// 展开/折叠记录详情
function toggleRecordDetails(recordId) {
  if (expandedRecordId.value === recordId) {
    expandedRecordId.value = null;
  } else {
    expandedRecordId.value = recordId;
  }
}

// 格式化日期时间
function formatDateTime(timestamp) {
  const date = new Date(timestamp);
  return date.toLocaleString();
}

// 截断文本
function truncateText(text, maxLength = 50) {
  if (!text) return "";
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + "...";
}

// 获取录音模式显示文本
function getModeText(mode) {
  return mode === "realtime" ? "实时录音" : "一次性录音";
}

// 组件挂载时加载历史记录
onMounted(() => {
  if (props.apiBaseUrl) {
    loadRecords();
  }
});
</script>

<template>
  <div class="history-container">
    <div class="history-header">
      <h2>历史记录</h2>
      <div class="history-actions">
        <div class="search-box">
          <i class="fas fa-search search-icon"></i>
          <input
            type="text"
            v-model="searchQuery"
            placeholder="搜索历史记录..."
            class="search-input"
          />
        </div>
        <button
          class="clear-history-btn"
          @click="clearAllRecords"
          :disabled="!records.length"
        >
          <i class="fas fa-trash-alt"></i>
          清空
        </button>
        <button class="refresh-btn" @click="loadRecords" :disabled="loading">
          <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
          刷新
        </button>
      </div>
    </div>

    <!-- 加载中状态 -->
    <div class="loading-state" v-if="loading">
      <i class="fas fa-spinner fa-spin"></i>
      <p>加载中...</p>
    </div>

    <!-- 错误状态 -->
    <div class="error-state" v-else-if="error">
      <i class="fas fa-exclamation-circle"></i>
      <p>{{ error }}</p>
      <button @click="loadRecords" class="retry-btn">重试</button>
    </div>

    <!-- 历史记录列表 -->
    <div class="history-list" v-else-if="filteredRecords.length">
      <div
        v-for="record in filteredRecords"
        :key="record.id"
        class="history-item"
        :class="{ expanded: expandedRecordId === record.id }"
      >
        <div class="history-item-header">
          <div
            class="history-item-content"
            @click="onSelect ? onSelect(record) : null"
          >
            <div class="history-item-text">{{ truncateText(record.text) }}</div>
            <div class="history-item-info">
              <span class="history-item-mode">{{
                getModeText(record.mode)
              }}</span>
              <span class="history-item-time">{{
                formatDateTime(record.timestamp)
              }}</span>
            </div>
          </div>

          <div class="history-item-actions">
            <!-- 音频播放按钮 -->
            <button
              v-if="
                record.audio_path ||
                (record.is_chunked && record.chunks && record.chunks.length)
              "
              class="action-btn play-btn"
              @click="
                playingRecordId === record.id && !playingChunkId
                  ? stopAudio()
                  : playAudio(record)
              "
              :title="
                playingRecordId === record.id && !playingChunkId
                  ? '停止播放'
                  : '播放音频'
              "
            >
              <i
                :class="[
                  'fas',
                  playingRecordId === record.id && !playingChunkId
                    ? 'fa-stop'
                    : 'fa-play',
                ]"
              ></i>
            </button>

            <!-- 展开/折叠按钮 -->
            <button
              v-if="record.is_chunked && record.chunks && record.chunks.length"
              class="action-btn expand-btn"
              @click="toggleRecordDetails(record.id)"
              :title="expandedRecordId === record.id ? '折叠' : '展开'"
            >
              <i
                :class="[
                  'fas',
                  expandedRecordId === record.id
                    ? 'fa-chevron-up'
                    : 'fa-chevron-down',
                ]"
              ></i>
            </button>

            <!-- 删除按钮 -->
            <button
              class="action-btn delete-btn"
              @click="deleteRecord(record.id)"
              title="删除"
            >
              <i class="fas fa-trash-alt"></i>
            </button>
          </div>
        </div>

        <!-- 分片详情 -->
        <div
          class="history-item-details"
          v-if="
            expandedRecordId === record.id && record.is_chunked && record.chunks
          "
        >
          <div class="chunks-list">
            <div
              v-for="chunk in record.chunks"
              :key="chunk.id"
              class="chunk-item"
            >
              <div class="chunk-index">{{ chunk.chunk_index + 1 }}</div>
              <div class="chunk-text">{{ chunk.text }}</div>
              <div class="chunk-actions">
                <!-- 分片音频播放按钮 -->
                <button
                  v-if="chunk.audio_path"
                  class="chunk-play-btn"
                  @click="
                    playingChunkId === chunk.id && playingRecordId === record.id
                      ? stopAudio()
                      : playChunkAudio(chunk, record.id)
                  "
                  :title="
                    playingChunkId === chunk.id && playingRecordId === record.id
                      ? '停止播放'
                      : '播放分片音频'
                  "
                >
                  <i
                    :class="[
                      'fas',
                      playingChunkId === chunk.id &&
                      playingRecordId === record.id
                        ? 'fa-stop'
                        : 'fa-play',
                    ]"
                  ></i>
                </button>
                <div class="chunk-time">
                  {{ formatDateTime(chunk.timestamp) }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div class="empty-history" v-else>
      <i class="fas fa-history empty-icon"></i>
      <p v-if="searchQuery">没有找到匹配的历史记录</p>
      <p v-else>暂无历史记录</p>
    </div>
  </div>
</template>

<style scoped>
.history-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.history-header {
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.history-header h2 {
  margin-top: 0;
  margin-bottom: 15px;
  font-size: 1.5rem;
  color: #333;
}

.history-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-box {
  position: relative;
  flex: 1;
  margin-right: 10px;
}

.search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: #999;
}

.search-input {
  width: 100%;
  padding: 8px 10px 8px 35px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
}

.clear-history-btn,
.refresh-btn {
  padding: 8px 12px;
  background-color: #f5f5f5;
  border: none;
  border-radius: 4px;
  color: #666;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  transition: background-color 0.2s;
  margin-left: 8px;
}

.clear-history-btn:hover,
.refresh-btn:hover {
  background-color: #e0e0e0;
}

.clear-history-btn:disabled,
.refresh-btn:disabled {
  background-color: #f5f5f5;
  color: #ccc;
  cursor: not-allowed;
}

.loading-state,
.error-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 40px 20px;
  color: #999;
}

.loading-state i,
.error-state i {
  font-size: 2rem;
  margin-bottom: 15px;
}

.error-state {
  color: #ff4d4f;
}

.retry-btn {
  margin-top: 15px;
  padding: 6px 12px;
  background-color: #f5f5f5;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px 20px;
}

.history-item {
  display: flex;
  flex-direction: column;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.history-item:last-child {
  border-bottom: none;
}

.history-item-header {
  display: flex;
  align-items: center;
}

.history-item-content {
  flex: 1;
  cursor: pointer;
  padding-right: 10px;
}

.history-item-text {
  font-size: 0.95rem;
  color: #333;
  margin-bottom: 5px;
}

.history-item-info {
  display: flex;
  align-items: center;
  font-size: 0.8rem;
  color: #999;
}

.history-item-mode {
  background-color: #f0f0f0;
  padding: 2px 6px;
  border-radius: 10px;
  margin-right: 8px;
}

.history-item-time {
  color: #999;
}

.history-item-actions {
  display: flex;
  align-items: center;
}

.action-btn {
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  padding: 5px;
  font-size: 0.9rem;
  opacity: 0.6;
  transition: opacity 0.2s;
  margin-left: 5px;
}

.action-btn:hover {
  opacity: 1;
}

.play-btn:hover {
  color: #1890ff;
}

.expand-btn:hover {
  color: #52c41a;
}

.delete-btn:hover {
  color: #ff4d4f;
}

.history-item-details {
  margin-top: 10px;
  padding: 10px;
  background-color: #f9f9f9;
  border-radius: 4px;
}

.chunks-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chunk-item {
  display: flex;
  align-items: flex-start;
  padding: 8px;
  background-color: #fff;
  border-radius: 4px;
  border: 1px solid #eee;
}

.chunk-index {
  background-color: #1890ff;
  color: white;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  margin-right: 10px;
  flex-shrink: 0;
}

.chunk-text {
  flex: 1;
  font-size: 0.9rem;
  color: #333;
}

.chunk-actions {
  display: flex;
  align-items: center;
  margin-left: 10px;
}

.chunk-play-btn {
  background: none;
  border: none;
  color: #1890ff;
  cursor: pointer;
  padding: 5px;
  font-size: 0.9rem;
  opacity: 0.8;
  transition: opacity 0.2s;
  margin-right: 8px;
}

.chunk-play-btn:hover {
  opacity: 1;
}

.chunk-time {
  font-size: 0.8rem;
  color: #999;
  white-space: nowrap;
}

.empty-history {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #999;
  padding: 40px 20px;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 15px;
  opacity: 0.3;
}

.empty-history p {
  font-size: 1rem;
  margin: 0;
}
</style>
