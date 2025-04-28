<script setup>
import { ref, watch, onMounted } from "vue";

const props = defineProps({
  settings: Object,
  onSave: Function,
});

// 创建本地设置状态的副本，以便在保存前进行编辑
const localSettings = ref({
  autoInsert: props.settings.autoInsert,
  alwaysOnTop: props.settings.alwaysOnTop,
  floatingMode: props.settings.floatingMode || false, // 浮动球模式
  visualizerType: props.settings.visualizerType || "wechat",
  lazyLoadBackend: props.settings.lazyLoadBackend || false, // 后端服务后置启动
  port: props.settings.port || 6100, // 后端服务端口
  debugMode: props.settings.debugMode || false, // Debug模式
  realtimeMode:
    props.settings.realtimeMode !== undefined
      ? props.settings.realtimeMode
      : true, // 实时流式识别模式
  audioInputDevice: props.settings.audioInputDevice || "", // 音频输入设备ID
  dataStoragePath: props.settings.dataStoragePath || "", // 数据存储目录
  modelParams: {
    model: props.settings.modelParams.model,
    vadModel: props.settings.modelParams.vadModel,
    puncModel: props.settings.modelParams.puncModel,
    spkModel: props.settings.modelParams.spkModel,
    disableUpdate: props.settings.modelParams.disableUpdate,
    device: props.settings.modelParams.device || "cuda",
    ngpu:
      props.settings.modelParams.ngpu !== undefined
        ? props.settings.modelParams.ngpu
        : 0,
    hotwords: props.settings.modelParams.hotwords || "",
  },
});

// 音频设备列表
const audioInputDevices = ref([]);

// 获取可用的音频输入设备
async function getAudioInputDevices() {
  try {
    // 请求麦克风权限，这样才能获取设备标签
    await navigator.mediaDevices.getUserMedia({ audio: true });

    // 获取所有媒体设备
    const devices = await navigator.mediaDevices.enumerateDevices();

    // 过滤出音频输入设备
    audioInputDevices.value = devices
      .filter((device) => device.kind === "audioinput")
      .map((device) => ({
        deviceId: device.deviceId,
        label: device.label || `麦克风 ${device.deviceId.substring(0, 5)}...`,
      }));

    // 添加默认选项
    audioInputDevices.value.unshift({ deviceId: "", label: "默认设备" });

    console.log("可用音频输入设备:", audioInputDevices.value);
  } catch (error) {
    console.error("获取音频设备失败:", error);
  }
}

// 组件挂载时获取音频设备
onMounted(() => {
  getAudioInputDevices();
});

// 可用的模型选项
const modelOptions = [
  {
    value: "iic/SenseVoiceSmall",
    label: "SenseVoice Small (中文多功能, 330M)",
  },
  { value: "paraformer-zh", label: "Paraformer 中文模型 (非实时, 220M)" },
  {
    value: "paraformer-zh-streaming",
    label: "Paraformer 中文流式模型 (实时, 220M)",
  },
  { value: "paraformer-en", label: "Paraformer 英文模型 (非实时, 220M)" },
  { value: "conformer-en", label: "Conformer 英文模型 (非实时, 220M)" },
  { value: "iic/Whisper-large-v3", label: "Whisper Large V3 (多语言, 1550M)" },
  {
    value: "iic/Whisper-large-v3-turbo",
    label: "Whisper Large V3 Turbo (多语言, 809M)",
  },
  { value: "Qwen-Audio", label: "音频文本多模态大模型（预训练）(多语言, 8B)" },
  // { value: "Qwen/Qwen-Audio-Chat", label: "Whisper Large V3 (多语言, 1550M)" },
  {
    value: "iic/emotion2vec_plus_large",
    label: "情感识别模型  (40000小时，4种情感类别, 300M)",
  },
];

const vadModelOptions = [
  { value: "fsmn-vad", label: "FSMN VAD 模型" },
  { value: "", label: "不使用" },
];

const puncModelOptions = [
  { value: "ct-punc", label: "CT 标点模型" },
  { value: "", label: "不使用" },
];

const speakModelOptions = [
  { value: "cam++", label: "说话人确认/分割模型" },
  { value: "", label: "不使用" },
];

// 可用的声纹效果选项
const visualizerOptions = [
  { value: "wechat", label: "微信式声纹" },
  { value: "circular", label: "圆形声纹" },
  { value: "bars", label: "柱状声纹" },
];

// 设备选项
const deviceOptions = [
  { value: "cuda", label: "GPU (CUDA)" },
  { value: "cpu", label: "CPU" },
];

// GPU ID 选项 (0-3)
const gpuOptions = [
  { value: 0, label: "GPU 0" },
  { value: 1, label: "GPU 1" },
  { value: 2, label: "GPU 2" },
  { value: 3, label: "GPU 3" },
];

// 保存设置
function saveSettings() {
  props.onSave(localSettings.value);
}

// 重置设置
function resetSettings() {
  localSettings.value = {
    autoInsert: props.settings.autoInsert,
    alwaysOnTop: props.settings.alwaysOnTop,
    floatingMode: props.settings.floatingMode || false,
    visualizerType: props.settings.visualizerType || "wechat",
    lazyLoadBackend: props.settings.lazyLoadBackend || false,
    port: props.settings.port || 6100,
    debugMode: props.settings.debugMode || false,
    realtimeMode:
      props.settings.realtimeMode !== undefined
        ? props.settings.realtimeMode
        : true,
    audioInputDevice: props.settings.audioInputDevice || "",
    dataStoragePath: props.settings.dataStoragePath || "",
    modelParams: {
      model: props.settings.modelParams.model,
      vadModel: props.settings.modelParams.vadModel,
      puncModel: props.settings.modelParams.puncModel,
      spkModel: props.settings.modelParams.spkModel,
      disableUpdate: props.settings.modelParams.disableUpdate,
      device: props.settings.modelParams.device || "cuda",
      ngpu:
        props.settings.modelParams.ngpu !== undefined
          ? props.settings.modelParams.ngpu
          : 0,
      hotwords: props.settings.modelParams.hotwords || "",
    },
  };
}

// 当props变化时更新本地设置
watch(
  () => props.settings,
  (newSettings) => {
    localSettings.value = {
      autoInsert: newSettings.autoInsert,
      alwaysOnTop: newSettings.alwaysOnTop,
      floatingMode: newSettings.floatingMode || false,
      visualizerType: newSettings.visualizerType || "wechat",
      lazyLoadBackend: newSettings.lazyLoadBackend || false,
      port: newSettings.port || 6100,
      debugMode: newSettings.debugMode || false,
      realtimeMode:
        newSettings.realtimeMode !== undefined
          ? newSettings.realtimeMode
          : true,
      audioInputDevice: newSettings.audioInputDevice || "",
      dataStoragePath: newSettings.dataStoragePath || "",
      modelParams: {
        model: newSettings.modelParams.model,
        vadModel: newSettings.modelParams.vadModel,
        puncModel: newSettings.modelParams.puncModel,
        spkModel: newSettings.modelParams.spkModel,
        disableUpdate: newSettings.modelParams.disableUpdate,
        device: newSettings.modelParams.device || "cuda",
        ngpu:
          newSettings.modelParams.ngpu !== undefined
            ? newSettings.modelParams.ngpu
            : 0,
        hotwords: newSettings.modelParams.hotwords || "",
      },
    };
  },
  { deep: true }
);
</script>

<template>
  <div class="settings-container">
    <h2>设置</h2>

    <div class="settings-section">
      <h3>基本设置</h3>

      <div class="setting-item">
        <div class="setting-label">
          <label for="data-storage-path">数据存储目录</label>
          <span class="setting-description"
            >设置用户数据（音频文件、历史记录等）的存储目录<br />留空使用默认目录:
            ~/.voice-assistant</span
          >
        </div>
        <div class="setting-control">
          <input
            type="text"
            id="data-storage-path"
            v-model="localSettings.dataStoragePath"
            class="text-input"
            placeholder="例如: /Users/username/Documents/voice-data"
          />
        </div>
      </div>

      <div class="setting-item">
        <div class="setting-label">
          <label for="auto-insert">自动插入文本</label>
          <span class="setting-description"
            >识别后自动将文本插入到当前焦点位置</span
          >
        </div>
        <div class="setting-control">
          <label class="switch">
            <input
              type="checkbox"
              id="auto-insert"
              v-model="localSettings.autoInsert"
            />
            <span class="slider round"></span>
          </label>
        </div>
      </div>

      <div class="setting-item">
        <div class="setting-label">
          <label for="always-on-top">窗口置顶</label>
          <span class="setting-description">保持应用窗口始终在最前面</span>
        </div>
        <div class="setting-control">
          <label class="switch">
            <input
              type="checkbox"
              id="always-on-top"
              v-model="localSettings.alwaysOnTop"
            />
            <span class="slider round"></span>
          </label>
        </div>
      </div>

      <div class="setting-item">
        <div class="setting-label">
          <label for="floating-mode">浮动球模式</label>
          <span class="setting-description"
            >启动时使用浮动球模式，只显示录音按钮和声纹效果（仅影响下次启动）</span
          >
        </div>
        <div class="setting-control">
          <label class="switch">
            <input
              type="checkbox"
              id="floating-mode"
              v-model="localSettings.floatingMode"
            />
            <span class="slider round"></span>
          </label>
        </div>
      </div>

      <div class="setting-item">
        <div class="setting-label">
          <label for="visualizer-type">声纹效果类型</label>
          <span class="setting-description">选择录音时的声纹可视化效果</span>
        </div>
        <div class="setting-control">
          <select id="visualizer-type" v-model="localSettings.visualizerType">
            <option
              v-for="option in visualizerOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>
        </div>
      </div>

      <div class="setting-item">
        <div class="setting-label">
          <label for="realtime-mode">默认录音识别模式</label>
          <span class="setting-description"
            >选择默认的录音识别模式:
            {{
              localSettings.realtimeMode ? "实时流式识别" : "一次性识别"
            }}</span
          >
        </div>
        <div class="setting-control">
          <label class="switch">
            <input
              type="checkbox"
              id="realtime-mode"
              v-model="localSettings.realtimeMode"
            />
            <span class="slider round"></span>
          </label>
        </div>
      </div>

      <div class="setting-item">
        <div class="setting-label">
          <label for="lazy-load-backend">后端服务后置启动</label>
          <span class="setting-description"
            >应用启动时不自动加载语音识别模型，加快启动速度</span
          >
        </div>
        <div class="setting-control">
          <label class="switch">
            <input
              type="checkbox"
              id="lazy-load-backend"
              v-model="localSettings.lazyLoadBackend"
            />
            <span class="slider round"></span>
          </label>
        </div>
      </div>

      <div class="setting-item">
        <div class="setting-label">
          <label for="port">后端服务端口</label>
          <span class="setting-description"
            >设置后端服务的端口号，需要重启应用生效</span
          >
        </div>
        <div class="setting-control">
          <input
            type="number"
            id="port"
            v-model.number="localSettings.port"
            min="1024"
            max="65535"
            class="port-input"
          />
        </div>
      </div>

      <!-- Debug模式 -->
      <div class="setting-item">
        <div class="setting-label">
          <label for="debug-mode">Debug模式</label>
          <span class="setting-description">启用开发者工具，用于调试应用</span>
        </div>
        <div class="setting-control">
          <label class="switch">
            <input
              type="checkbox"
              id="debug-mode"
              v-model="localSettings.debugMode"
            />
            <span class="slider round"></span>
          </label>
        </div>
      </div>

      <div class="setting-item">
        <div class="setting-label">
          <label for="audio-input-device">音频输入设备</label>
          <span class="setting-description"
            >选择用于录音的麦克风或音频输入设备</span
          >
        </div>
        <div class="setting-control">
          <select
            id="audio-input-device"
            v-model="localSettings.audioInputDevice"
          >
            <option
              v-for="device in audioInputDevices"
              :key="device.deviceId"
              :value="device.deviceId"
            >
              {{ device.label }}
            </option>
          </select>
          <button
            class="refresh-devices-btn"
            @click="getAudioInputDevices"
            title="刷新设备列表"
          >
            <i class="fas fa-sync-alt"></i>
          </button>
        </div>
      </div>
    </div>

    <div class="settings-section">
      <h3>模型设置</h3>
      <p class="section-description">修改模型设置后需要重启服务才能生效</p>

      <div class="setting-item">
        <div class="setting-label">
          <label for="model">语音识别模型</label>
        </div>
        <div class="setting-control">
          <select id="model" v-model="localSettings.modelParams.model">
            <option
              v-for="option in modelOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>
        </div>
      </div>

      <div class="setting-item">
        <div class="setting-label">
          <label for="vad-model">语音活动检测模型</label>
        </div>
        <div class="setting-control">
          <select id="vad-model" v-model="localSettings.modelParams.vadModel">
            <option
              v-for="option in vadModelOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>
        </div>
      </div>

      <div class="setting-item">
        <div class="setting-label">
          <label for="punc-model">标点符号模型</label>
        </div>
        <div class="setting-control">
          <select id="punc-model" v-model="localSettings.modelParams.puncModel">
            <option
              v-for="option in puncModelOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>
        </div>
      </div>

      <div class="setting-item">
        <div class="setting-label">
          <label for="speak-model">说话人确认/分割模型</label>
        </div>
        <div class="setting-control">
          <select id="speak-model" v-model="localSettings.modelParams.spkModel">
            <option
              v-for="option in speakModelOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>
        </div>
      </div>

      <div class="setting-item">
        <div class="setting-label">
          <label for="device">计算设备</label>
          <span class="setting-description">选择使用 GPU 或 CPU 进行计算</span>
        </div>
        <div class="setting-control">
          <select id="device" v-model="localSettings.modelParams.device">
            <option
              v-for="option in deviceOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>
        </div>
      </div>

      <div
        class="setting-item"
        v-if="localSettings.modelParams.device === 'cuda'"
      >
        <div class="setting-label">
          <label for="ngpu">GPU 设备 ID</label>
          <span class="setting-description">选择要使用的 GPU 设备 ID</span>
        </div>
        <div class="setting-control">
          <select id="ngpu" v-model="localSettings.modelParams.ngpu">
            <option
              v-for="option in gpuOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>
        </div>
      </div>

      <div class="setting-item">
        <div class="setting-label">
          <label for="disable-update">禁用模型自动更新</label>
          <span class="setting-description">防止模型在使用过程中自动更新</span>
        </div>
        <div class="setting-control">
          <label class="switch">
            <input
              type="checkbox"
              id="disable-update"
              v-model="localSettings.modelParams.disableUpdate"
            />
            <span class="slider round"></span>
          </label>
        </div>
      </div>

      <div class="setting-item">
        <div class="setting-label">
          <label for="hotwords">热词列表</label>
          <span class="setting-description"
            >提高特定词汇的识别准确率，多个词用逗号分隔<br />一行一个热词和权重:例如:
            语音识别 10<br />设置后需要重启服务才能生效</span
          >
        </div>
        <div class="setting-control">
          <textarea
            id="hotwords"
            v-model="localSettings.modelParams.hotwords"
            class="text-input textarea-input"
            placeholder="输入热词：语音识别 10"
            rows="5"
          ></textarea>
        </div>
      </div>
    </div>

    <div class="settings-actions">
      <button class="btn-reset" @click="resetSettings">重置</button>
      <button class="btn-save" @click="saveSettings">保存</button>
    </div>
  </div>
</template>

<style scoped>
.settings-container {
  padding: 20px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

h2 {
  margin-top: 0;
  margin-bottom: 20px;
  font-size: 1.5rem;
  color: #333;
}

.settings-section {
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #eee;
}

.settings-section:last-child {
  border-bottom: none;
}

h3 {
  margin-top: 0;
  margin-bottom: 15px;
  font-size: 1.2rem;
  color: #333;
}

.section-description {
  margin-top: -10px;
  margin-bottom: 15px;
  font-size: 0.9rem;
  color: #666;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding: 10px 0;
}

.setting-label {
  flex: 1;
}

.setting-label label {
  display: block;
  font-weight: 500;
  margin-bottom: 5px;
}

.setting-description {
  display: block;
  font-size: 0.85rem;
  color: #666;
}

.setting-control {
  flex: 0 0 auto;
  margin-left: 20px;
}

select {
  width: 200px;
  padding: 8px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background-color: #fff;
  font-size: 0.9rem;
}

.settings-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.btn-save,
.btn-reset {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background-color 0.2s;
}

.btn-save {
  background-color: #1890ff;
  color: white;
}

.btn-save:hover {
  background-color: #40a9ff;
}

.btn-reset {
  background-color: #f0f0f0;
  color: #333;
}

.btn-reset:hover {
  background-color: #e0e0e0;
}

.setting-control {
  display: flex;
  align-items: center;
}

.refresh-devices-btn {
  margin-left: 8px;
  background-color: #f0f0f0;
  border: none;
  border-radius: 4px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background-color 0.2s;
}

.refresh-devices-btn:hover {
  background-color: #e0e0e0;
}

.refresh-devices-btn i {
  font-size: 14px;
  color: #555;
}

/* 开关样式 */
.switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: 0.4s;
}

.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.4s;
}

input:checked + .slider {
  background-color: #1890ff;
}

input:focus + .slider {
  box-shadow: 0 0 1px #1890ff;
}

input:checked + .slider:before {
  transform: translateX(20px);
}

.slider.round {
  border-radius: 24px;
}

.slider.round:before {
  border-radius: 50%;
}

.mode-label {
  margin-left: 10px;
  font-size: 0.9rem;
  color: #666;
}

/* 端口输入框样式 */
.port-input {
  width: 100px;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
  color: #333;
  background-color: white;
  transition: border-color 0.3s;
}

.port-input:focus {
  outline: none;
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

/* 文本输入框样式 */
.text-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
  color: #333;
  background-color: white;
  transition: border-color 0.3s;
}

.text-input:focus {
  outline: none;
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

/* 多行文本输入框样式 */
.textarea-input {
  resize: vertical;
  min-height: 100px;
  font-family: inherit;
  line-height: 1.5;
}
</style>
