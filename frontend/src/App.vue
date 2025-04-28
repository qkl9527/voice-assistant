<script setup>
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from "vue";
import Settings from "./components/Settings.vue";
import History from "./components/History.vue";
import AudioVisualizer from "./components/AudioVisualizer.vue";
import MessageBox from "./components/MessageBox.vue";

// 当前视图
const currentView = ref("main"); // 'main', 'settings', 'history'

// 状态变量
const isRecording = ref(false);
const recognizedText = ref("");
const serviceStatus = ref("正在连接...");
const autoInsert = ref(true);
const mediaRecorder = ref(null);
const audioChunks = ref([]);
const audioFirstChunk = ref(null);
const apiBaseUrl = ref("");
const streamingInterval = ref(null);
const audioContext = ref(null);
const analyser = ref(null);
const isAlwaysOnTop = ref(false); // 窗口置顶状态
const isFloatingMode = ref(false); // 浮动球模式状态
const textareaRef = ref(null); // 文本区域引用
const isRealtimeMode = ref(true); // 录音模式：true为实时流式识别，false为一次性识别
// 实时录音分片管理
const currentChunkIndex = ref(0); // 当前分片索引
const currentRecordId = ref(null); // 当前录音记录ID
// 消息提示框
const messageBoxShow = ref(false);
const messageBoxTitle = ref("提示");
const messageBoxMessage = ref("");
const messageBoxConfirm = ref(false);
const messageBoxShowClose = ref(true);
const messageBoxType = ref("info"); // 'info', 'success', 'warning', 'error'
// 使用设置中的端口号
const getPort = () => settings.value.port || 6100;

// 侧边栏状态
const isSidebarCollapsed = ref(false);

// 历史记录已移至后端SQLite数据库

// 设置
const settings = ref({
  autoInsert: true,
  alwaysOnTop: false,
  floatingMode: false, // 浮动球模式
  visualizerType: "wechat", // 默认声纹效果类型
  lazyLoadBackend: true, // 后端服务后置启动
  port: 6100, // 后端服务端口
  debugMode: false, // Debug模式
  realtimeMode: true, // 实时流式识别模式
  audioInputDevice: "", // 音频输入设备ID
  dataStoragePath: "", // 数据存储目录
  modelParams: {
    model: "paraformer-zh",
    vadModel: "fsmn-vad",
    puncModel: "",
    spkModel: "", // cam++
    disableUpdate: true,
    device: "cuda", // cuda 或 cpu
    ngpu: 0, // GPU 设备 ID
    hotwords: "", // 热词列表
  },
});

// 加载设置
async function loadSettings() {
  if (window.electronAPI) {
    try {
      // 从本地存储加载设置
      const savedSettings = await window.electronAPI.loadFromStorage(
        "settings"
      );
      if (savedSettings) {
        // 确保声纹效果类型存在
        if (!savedSettings.visualizerType) {
          savedSettings.visualizerType = "wechat";
        }

        // 创建一个新的设置对象，而不是直接使用加载的对象
        settings.value = {
          autoInsert: savedSettings.autoInsert,
          alwaysOnTop: savedSettings.alwaysOnTop,
          floatingMode: savedSettings.floatingMode || false,
          visualizerType: savedSettings.visualizerType,
          lazyLoadBackend: savedSettings.lazyLoadBackend,
          port: savedSettings.port || 6100,
          debugMode: savedSettings.debugMode || false,
          realtimeMode:
            savedSettings.realtimeMode !== undefined
              ? savedSettings.realtimeMode
              : true,
          audioInputDevice: savedSettings.audioInputDevice || "",
          dataStoragePath: savedSettings.dataStoragePath || "",
          modelParams: {
            model: savedSettings.modelParams.model,
            vadModel: savedSettings.modelParams.vadModel,
            puncModel: savedSettings.modelParams.puncModel,
            spkModel: savedSettings.modelParams.spkModel,
            disableUpdate: savedSettings.modelParams.disableUpdate,
            device: savedSettings.modelParams.device || "cuda",
            ngpu:
              savedSettings.modelParams.ngpu !== undefined
                ? savedSettings.modelParams.ngpu
                : 0,
            hotwords: savedSettings.modelParams.hotwords || "",
          },
        };

        // 同步设置到应用状态
        autoInsert.value = settings.value.autoInsert;
        isAlwaysOnTop.value = settings.value.alwaysOnTop;
        isFloatingMode.value = settings.value.floatingMode;
        isRealtimeMode.value = settings.value.realtimeMode;

        // 如果有必要，更新模型参数
        await window.electronAPI.setModelParams({
          ...settings.value.modelParams,
        });

        console.log("已加载设置:", JSON.stringify(settings.value, null, 2));
      }
    } catch (error) {
      console.error("加载设置失败:", error);
    }
  }
}

// 保存设置
async function saveSettings(newSettings) {
  if (window.electronAPI) {
    try {
      // 确保声纹效果类型存在
      if (!newSettings.visualizerType) {
        newSettings.visualizerType = "wechat";
      }

      // 更新本地设置
      settings.value = {
        autoInsert: newSettings.autoInsert,
        alwaysOnTop: newSettings.alwaysOnTop,
        floatingMode: newSettings.floatingMode || false,
        visualizerType: newSettings.visualizerType,
        lazyLoadBackend: newSettings.lazyLoadBackend || true,
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

      // 同步设置到应用状态
      autoInsert.value = newSettings.autoInsert;
      isRealtimeMode.value = settings.value.realtimeMode;

      // 更新窗口置顶状态
      if (isAlwaysOnTop.value !== newSettings.alwaysOnTop) {
        await window.electronAPI.toggleAlwaysOnTop();
        isAlwaysOnTop.value = newSettings.alwaysOnTop;
      }

      // 保存浮动球模式设置，但不自动切换
      // 只在设置中保存用户的选择，下次启动时生效

      // 更新Debug模式状态
      if (settings.value.debugMode !== newSettings.debugMode) {
        await window.electronAPI.toggleDebugMode();
      }

      // 如果模型参数发生变化，更新模型参数
      const currentParams = JSON.stringify(settings.value.modelParams);
      const newParams = JSON.stringify(newSettings.modelParams);

      if (true || currentParams !== newParams) {
        await window.electronAPI.setModelParams({
          ...settings.value.modelParams,
        });
        serviceStatus.value = "模型参数已更新，服务正在重启...";
        // todo 是否要重启服务
        await checkServiceStatus();
      }

      // 创建一个只包含可序列化数据的对象来保存
      const settingsToSave = {
        autoInsert: settings.value.autoInsert,
        alwaysOnTop: settings.value.alwaysOnTop,
        floatingMode: settings.value.floatingMode,
        visualizerType: settings.value.visualizerType,
        lazyLoadBackend: settings.value.lazyLoadBackend,
        port: settings.value.port,
        debugMode: settings.value.debugMode,
        realtimeMode: settings.value.realtimeMode,
        audioInputDevice: settings.value.audioInputDevice,
        dataStoragePath: settings.value.dataStoragePath,
        modelParams: {
          model: settings.value.modelParams.model,
          vadModel: settings.value.modelParams.vadModel,
          puncModel: settings.value.modelParams.puncModel,
          spkModel: settings.value.modelParams.spkModel,
          disableUpdate: settings.value.modelParams.disableUpdate,
          device: settings.value.modelParams.device,
          ngpu: settings.value.modelParams.ngpu,
          hotwords: settings.value.modelParams.hotwords,
        },
      };

      // 保存到本地存储
      await window.electronAPI.saveToStorage("settings", settingsToSave);
      console.log("设置已保存:", settingsToSave, newSettings);

      // 切回主视图
      currentView.value = "main";
    } catch (error) {
      console.error("保存设置失败:", error);
      alert("保存设置失败: " + error.message);
    }
  }
}

// 历史记录相关函数已经移除，现在直接使用后端API
// 从历史记录中选择条目时的处理
function selectHistoryItem(item) {
  recognizedText.value = item.text;
  currentView.value = "main";
}

// 切换侧边栏折叠状态
function toggleSidebar() {
  isSidebarCollapsed.value = !isSidebarCollapsed.value;

  // 如果有本地存储，保存折叠状态
  if (window.electronAPI) {
    window.electronAPI.saveToStorage("sidebarState", {
      collapsed: isSidebarCollapsed.value,
    });
  }
}

// 加载侧边栏状态
async function loadSidebarState() {
  if (window.electronAPI) {
    try {
      const state = await window.electronAPI.loadFromStorage("sidebarState");
      if (state && typeof state.collapsed === "boolean") {
        isSidebarCollapsed.value = state.collapsed;
      }
    } catch (error) {
      console.error("加载侧边栏状态失败:", error);
    }
  }
}

// 当切换视图时，如果侧边栏是折叠的，展开它
watch(currentView, (newView, oldView) => {
  if (isSidebarCollapsed.value) {
    isSidebarCollapsed.value = false;
  }

  // 如果从设置视图切换回主视图，确保声纹效果类型正确应用
  if (newView === "main" && oldView === "settings") {
    // 重新初始化可视化器，使其应用新的声纹效果类型
    console.log(
      "切换回主视图，当前声纹效果类型:",
      settings.value.visualizerType
    );

    // 强制更新声纹效果类型
    nextTick(() => {
      // 通过临时更改然后恢复来触发响应式更新
      const currentType = settings.value.visualizerType;
      settings.value = { ...settings.value, visualizerType: "temp" };
      nextTick(() => {
        settings.value = { ...settings.value, visualizerType: currentType };
      });
    });
  }
});

// 获取 API 基础 URL
onMounted(async () => {
  try {
    // 检查是否在 Electron 环境中
    if (window.electronAPI) {
      // 加载设置和侧边栏状态
      await loadSettings();
      await loadSidebarState();

      // 获取窗口置顶状态
      if (!settings.value.alwaysOnTop && isAlwaysOnTop.value) {
        // 如果设置中的置顶状态与实际不符，进行同步
        isAlwaysOnTop.value = false;
      }

      if (isAlwaysOnTop.value) {
        await window.electronAPI.toggleAlwaysOnTop();
      }

      // 获取当前浮动球模式状态
      const floatingModeState = await window.electronAPI.getFloatingModeState();
      isFloatingMode.value = floatingModeState;

      // 如果设置中需要浮动球模式，但当前不是浮动球模式，则切换到浮动球模式
      if (settings.value.floatingMode && !floatingModeState) {
        await window.electronAPI.toggleFloatingMode();
        isFloatingMode.value = true;
      }

      // 获取Debug模式状态
      const debugModeState = await window.electronAPI.getDebugModeState();
      if (settings.value.debugMode !== debugModeState) {
        // 如果设置中的Debug模式状态与实际不符，进行同步
        await window.electronAPI.toggleDebugMode();
        settings.value.debugMode = debugModeState;
      }

      // 检查是否需要后置启动后端服务
      if (!settings.value.lazyLoadBackend) {
        // 如果不是后置启动，则立即启动服务
        apiBaseUrl.value = await window.electronAPI.getApiBaseUrl();
        await checkServiceStatus();
      } else {
        // 如果是后置启动，设置服务状态为未启动
        serviceStatus.value = "服务未启动";
      }

      // 注册浮动球模式变化监听
      window.electronAPI.onFloatingModeChanged((isFloating) => {
        console.log("浮动球模式变化:", isFloating);
        isFloatingMode.value = isFloating;
      });
    } else {
      // 在浏览器环境中，假设 API 在本地运行
      apiBaseUrl.value = `http://localhost:${getPort()}`;
      await checkServiceStatus();
    }

    // 初始化音频上下文
    try {
      audioContext.value = new (window.AudioContext ||
        window.webkitAudioContext)();
      analyser.value = audioContext.value.createAnalyser();
      analyser.value.fftSize = 2048;
    } catch (error) {
      console.error("初始化音频上下文失败:", error);
    }
  } catch (error) {
    console.error("获取 API URL 失败:", error);
    serviceStatus.value = "连接失败";
  }
});

// 检查服务状态
async function checkServiceStatus() {
  // 如果没有 API 基础 URL，说明服务未启动
  if (!apiBaseUrl.value) {
    serviceStatus.value = "服务未启动";
    return false;
  }

  try {
    console.log(`检查服务状态: ${apiBaseUrl.value}/api/status`);
    const response = await fetch(`${apiBaseUrl.value}/api/status`, {
      mode: "cors",
      credentials: "omit",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
    });
    if (response.ok) {
      const data = await response.json();
      console.log("服务状态响应:", data);
      serviceStatus.value = data.model_loaded ? "已连接" : "模型加载中...";
      return data.model_loaded;
    } else {
      console.log("服务状态响应不正常:", response.status);
      serviceStatus.value = "连接失败1";
      return false;
    }
  } catch (error) {
    console.error("检查服务状态失败:", error);
    serviceStatus.value = "连接失败2";
    return false;
  }
}

// 开始录音
async function startRecording() {
  try {
    audioFirstChunk.value = null;

    // 重置分片索引和记录ID
    if (isRealtimeMode.value) {
      currentChunkIndex.value = 0;

      // 获取最后一个记录id+1的值
      const response = await fetch(
        `${apiBaseUrl.value}/api/get_last_record_id`,
        {
          method: "GET",
          mode: "cors",
          credentials: "omit",
        }
      );

      if (response.ok) {
        const last_record_data = await response.json();
        currentRecordId.value = last_record_data.last_record_id;
      }
    }

    // 设置音频约束，如果有选择特定设备则使用该设备
    const audioConstraints = { audio: true };

    // 如果设置了特定的音频输入设备，则在约束中指定
    if (settings.value.audioInputDevice) {
      audioConstraints.audio = {
        deviceId: { exact: settings.value.audioInputDevice },
      };
    }

    const stream = await navigator.mediaDevices.getUserMedia(audioConstraints);
    mediaRecorder.value = new MediaRecorder(stream);
    audioChunks.value = [];
    recognizedText.value = "";

    // 连接音频分析器
    if (audioContext.value) {
      const source = audioContext.value.createMediaStreamSource(stream);
      source.connect(analyser.value);
    }

    // 收集音频数据
    mediaRecorder.value.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.value.push(event.data);

        if (!audioFirstChunk.value) {
          audioFirstChunk.value = event.data;
        }
      }
    };

    // 录音停止时的处理
    mediaRecorder.value.onstop = async () => {
      // 关闭音频流的所有轨道
      stream.getTracks().forEach((track) => track.stop());

      // 清除实时识别定时器
      if (streamingInterval.value) {
        clearInterval(streamingInterval.value);
        streamingInterval.value = null;
      }

      // 如果是一次性识别模式，在停止录音时发送所有音频数据进行识别
      if (!isRealtimeMode.value && audioChunks.value.length > 0) {
        const audioBlob = new Blob(audioChunks.value, {
          type: "audio/wav",
        });
        await sendAudioForRecognition(audioBlob);
      } else if (isRealtimeMode.value && currentRecordId.value) {
        // 如果是实时模式，发送最后一个分片标记
        console.log("发送最后一个分片标记，记录ID:", currentRecordId.value);
        try {
          const response = await fetch(
            `${apiBaseUrl.value}/api/recognize_stream`,
            {
              method: "POST",
              mode: "cors",
              credentials: "omit",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                is_last_chunk: true,
                record_id: currentRecordId.value,
                chunk_index: currentChunkIndex.value,
                audio: null, // 不需要音频数据，只是标记最后一个分片
              }),
            }
          );

          if (response.ok) {
            // currentRecordId.value = currentRecordId.value + 1;
            console.log("最后一个分片标记发送成功");
          }
        } catch (error) {
          console.error("发送最后一个分片标记失败:", error);
        }
      }
    };

    // 开始录音
    mediaRecorder.value.start(200); // 每200ms触发一次 ondataavailable 事件
    isRecording.value = true;

    // 如果是实时流式识别模式，设置定时发送音频数据
    if (isRealtimeMode.value) {
      streamingInterval.value = setInterval(async () => {
        if (audioChunks.value.length > 0) {
          console.log(
            "streamingInterval:",
            audioFirstChunk.value,
            audioChunks.value[0]
          );
          if (audioChunks.value[0] == audioFirstChunk.value) {
            audioChunks.value.shift();
          }
          const audioBlob = new Blob(
            [audioFirstChunk.value, ...audioChunks.value],
            {
              type: "audio/wav",
            }
          );
          audioChunks.value = [];
          await sendStreamingAudio(
            audioBlob,
            currentRecordId.value,
            currentChunkIndex.value
          );
          currentChunkIndex.value = currentChunkIndex.value + 1;
        }
      }, 2000);
    }
  } catch (error) {
    console.error("开始录音失败:", error);
    showMessage(
      "录音失败",
      "无法访问麦克风，请确保已授予麦克风权限。",
      "error"
    );
  }
}

// 停止录音
async function stopRecording() {
  if (mediaRecorder.value && isRecording.value) {
    mediaRecorder.value.stop();
    isRecording.value = false;

    // 清除实时识别定时器
    if (streamingInterval.value) {
      clearInterval(streamingInterval.value);
      streamingInterval.value = null;
    }

    // 历史记录现在由后端自动处理
  }
}

// 发送音频进行实时识别
async function sendStreamingAudio(audioBlob, record_id, chunk_id) {
  try {
    // 将音频转换为 base64
    const reader = new FileReader();
    reader.readAsDataURL(audioBlob);
    reader.onloadend = async () => {
      const base64Audio = reader.result;

      // 准备请求数据，包含分片索引和记录ID
      const requestData = {
        audio: base64Audio,
        auto_insert: autoInsert.value,
        chunk_index: chunk_id,
        record_id: record_id,
        is_last_chunk: false,
      };

      const response = await fetch(`${apiBaseUrl.value}/api/recognize_stream`, {
        method: "POST",
        mode: "cors",
        credentials: "omit",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestData),
      });

      if (response.ok) {
        const data = await response.json();

        // 更新记录ID（如果是第一个分片，后端会创建新记录并返回ID）
        // if (data.record_id && currentChunkIndex.value === 0) {
        //   currentRecordId.value = data.record_id;
        //   console.log("获取到新的记录ID:", currentRecordId.value);
        // }

        if (data.text && data.text.trim() !== "") {
          // 如果文本发生变化，更新显示
          if (recognizedText.value !== data.text) {
            recognizedText.value = recognizedText.value + data.text;

            // 自动滚动到底部
            await scrollToBottom();
          }
        }
      } else {
        const error = await response.json();
        console.error("实时识别失败:", error);
      }
    };
  } catch (error) {
    console.error("发送音频失败:", error);
  }
}

// 发送音频进行识别
async function sendAudioForRecognition(audioBlob) {
  try {
    const formData = new FormData();
    formData.append("audio", audioBlob, "recording.wav");
    formData.append("auto_insert", autoInsert.value);

    const response = await fetch(`${apiBaseUrl.value}/api/recognize`, {
      mode: "cors",
      credentials: "omit",
      method: "POST",
      body: formData,
    });

    if (response.ok) {
      const data = await response.json();
      recognizedText.value = data.text;
    } else {
      const error = await response.json();
      console.error("识别失败:", error);
    }
  } catch (error) {
    console.error("发送音频失败:", error);
    showMessage("发送失败", "发送音频失败，请检查网络连接。", "error");
  }
}

// 手动插入文本
async function insertText() {
  if (!recognizedText.value.trim()) return;

  try {
    const response = await fetch(`${apiBaseUrl.value}/api/insert_text`, {
      mode: "cors",
      credentials: "omit",
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text: recognizedText.value }),
    });

    if (!response.ok) {
      const error = await response.json();
      console.error("插入文本失败:", error);
    }
  } catch (error) {
    console.error("插入文本请求失败:", error);
  }
}

// 清空识别文本
function clearText() {
  recognizedText.value = "";
  // showMessage("已清空", "识别文本已清空", "info", 1500);
}

// 启动或重启服务
async function startOrRestartService() {
  if (window.electronAPI) {
    // 根据当前状态决定是启动还是重启
    if (serviceStatus.value === "服务未启动") {
      serviceStatus.value = "正在启动服务...";
      try {
        // 获取API基础URL（这会启动服务）
        apiBaseUrl.value = await window.electronAPI.getApiBaseUrl();
        // 等待一些时间，给服务启动的时间
        await new Promise((resolve) => setTimeout(resolve, 1000));
        await checkServiceStatus();
      } catch (error) {
        console.error("启动服务失败:", error);
        serviceStatus.value = "启动失败";
        showMessage("启动失败", "语音识别服务启动失败，请重试", "error");
      }
    } else {
      // 如果服务已经存在但连接失败，则重启服务
      serviceStatus.value = "正在重启服务...";
      try {
        await window.electronAPI.restartPythonService();
        // 等待一些时间，给服务重启的时间
        await new Promise((resolve) => setTimeout(resolve, 1000));
        await checkServiceStatus();
      } catch (error) {
        console.error("重启服务失败:", error);
        serviceStatus.value = "重启失败";
        showMessage("重启失败", "语音识别服务重启失败，请重试", "error");
      }
    }
  }
}

// 重启服务
async function restartService() {
  if (window.electronAPI) {
    serviceStatus.value = "正在重启服务...";
    try {
      serviceStatus.value = await window.electronAPI.restartPythonService();
      checkServiceStatus();
    } catch (error) {
      console.error("重启服务失败:", error);
      serviceStatus.value = "重启失败";
      showMessage("重启失败", "语音识别服务重启失败，请重试", "error");
    }
  }
}

// 切换窗口置顶状态 - 通过设置页面调用

// 切换浮动球模式
async function toggleFloatingMode() {
  if (window.electronAPI) {
    // 切换浮动球模式状态
    await window.electronAPI.toggleFloatingMode();
    // 注意：我们不再直接设置 isFloatingMode.value
    // 因为现在我们使用事件监听来更新这个状态
    // 这样可以确保前端和主进程的状态保持同步

    // 注意：我们不更新settings.value.floatingMode
    // 因为这只是当前会话的状态，而不是用户的默认偏好设置
    // 设置中的floatingMode只在应用启动时生效，之后只能通过设置页面修改
  }
}

// 浮动球拖动相关变量
const isDragging = ref(false);
const dragStartPos = ref({ x: 0, y: 0 });

// 开始拖动
function startDrag(event) {
  // 只处理鼠标左键
  if (event.button !== 0) return;

  // 如果点击的是按钮或其子元素，不处理拖动
  if (
    event.target.closest(".floating-record-btn") ||
    event.target.closest(".floating-restore-btn") ||
    event.target.closest(".floating-status-container") ||
    event.target.closest(".service-status-collapsed") ||
    event.target.closest(".floating-mode-toggle-btn") ||
    event.target.closest("button") // 添加这一行确保所有按钮都不会触发拖动
  ) {
    return;
  }

  isDragging.value = true;
  dragStartPos.value = { x: event.clientX, y: event.clientY };

  // 添加鼠标移动和松开事件
  document.addEventListener("mousemove", onDrag);
  document.addEventListener("mouseup", stopDrag);

  // 防止文本选中
  event.preventDefault();
}

// 拖动过程
function onDrag(event) {
  if (!isDragging.value) return;

  // 计算移动距离
  const dx = event.clientX - dragStartPos.value.x;
  const dy = event.clientY - dragStartPos.value.y;

  // 重置起始位置
  dragStartPos.value = { x: event.clientX, y: event.clientY };

  // 移动窗口
  if (window.electronAPI) {
    window.electronAPI.moveFloatingWindow(dx, dy);
  }
}

// 停止拖动
function stopDrag() {
  isDragging.value = false;
  document.removeEventListener("mousemove", onDrag);
  document.removeEventListener("mouseup", stopDrag);
}

// 自动滚动到文本区域底部
async function scrollToBottom() {
  if (textareaRef.value) {
    await nextTick();
    textareaRef.value.scrollTop = textareaRef.value.scrollHeight;
  }
}

// 监听文本变化，自动滚动到底部
watch(recognizedText, async () => {
  await scrollToBottom();
});

// 显示消息提示框
function showMessage(
  title,
  message,
  confirm = false,
  hasCloseButton = false,
  type = "info",
  duration = 3000
) {
  messageBoxTitle.value = title;
  messageBoxMessage.value = message;
  messageBoxConfirm.value = confirm;
  messageBoxShowClose.value = hasCloseButton;
  messageBoxType.value = type;
  messageBoxShow.value = true;

  // 如果设置了自动关闭时间，则自动关闭
  if (duration > 0) {
    setTimeout(() => {
      messageBoxShow.value = false;
    }, duration);
  }
}

// 切换录音模式
function toggleRecordingMode() {
  // 如果正在录音，无法切换模式，显示提示消息
  if (isRecording.value) {
    console.log("正在录音无法切换");
    showMessage(
      "无法切换模式",
      "正在录音中，请先停止录音后再切换模式",
      "warning"
    );
    return;
  }

  isRealtimeMode.value = !isRealtimeMode.value;

  // 更新设置中的录音模式（但不保存到本地存储，只是临时更改）
  // settings.value = {
  //   ...settings.value,
  //   realtimeMode: isRealtimeMode.value,
  // };

  console.log(
    `已切换到${isRealtimeMode.value ? "实时流式" : "一次性"}识别模式`
  );
}

// 组件卸载时清理资源
onUnmounted(() => {
  if (mediaRecorder.value && isRecording.value) {
    mediaRecorder.value.stop();
  }

  if (streamingInterval.value) {
    clearInterval(streamingInterval.value);
  }

  if (audioContext.value) {
    audioContext.value.close();
  }
});
</script>

<template>
  <div
    class="app-container"
    :class="{
      'sidebar-collapsed': isSidebarCollapsed,
      'floating-mode': isFloatingMode,
    }"
  >
    <!-- 侧边栏折叠按钮 -->
    <button
      @click="toggleSidebar"
      class="sidebar-toggle"
      :title="isSidebarCollapsed ? '展开侧边栏' : '折叠侧边栏'"
    >
      <i
        :class="[
          'fas',
          isSidebarCollapsed ? 'fa-angle-right' : 'fa-angle-left',
        ]"
      ></i>
    </button>

    <!-- 侧边栏 -->
    <div class="sidebar">
      <div class="sidebar-header">
        <h2>VoiceAssistant</h2>
      </div>

      <div class="sidebar-menu">
        <button
          @click="currentView = 'main'"
          :class="['sidebar-item', currentView === 'main' ? 'active' : '']"
        >
          <i class="fas fa-microphone"></i>
          <span>语音识别</span>
        </button>

        <button
          @click="currentView = 'history'"
          :class="['sidebar-item', currentView === 'history' ? 'active' : '']"
        >
          <i class="fas fa-history"></i>
          <span>历史记录</span>
        </button>

        <button
          @click="currentView = 'settings'"
          :class="['sidebar-item', currentView === 'settings' ? 'active' : '']"
        >
          <i class="fas fa-cog"></i>
          <span>设置</span>
        </button>
      </div>

      <div class="sidebar-footer">
        <div class="service-status">
          <span
            :class="[
              'status-indicator',
              serviceStatus === '已连接' ? 'online' : 'offline',
            ]"
          ></span>
          <span class="status-text">{{ serviceStatus }}</span>
        </div>

        <div class="service-actions">
          <button
            @click="checkServiceStatus"
            class="icon-btn check-model-btn"
            title="检查服务"
          >
            <i class="fas fa-info"></i>
          </button>
          <button
            @click="restartService"
            class="icon-btn restart-btn"
            title="重启服务"
          >
            <i class="fas fa-sync-alt"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-container">
      <!-- 折叠时显示的服务状态 -->
      <div
        v-if="isSidebarCollapsed && !isFloatingMode"
        class="collapsed-status"
      >
        <div class="service-status-collapsed">
          <span
            :class="[
              'status-indicator',
              serviceStatus === '已连接' ? 'online' : 'offline',
            ]"
          ></span>
          <span class="status-text">{{ serviceStatus }}</span>
        </div>
      </div>

      <!-- 浮动球模式切换按钮 -->
      <button
        v-if="!isFloatingMode && currentView === 'main'"
        @click="toggleFloatingMode"
        class="floating-toggle-btn"
        title="切换浮动球模式"
      >
        <i class="fas fa-compress-alt"></i>
      </button>

      <!-- 浮动球模式 -->
      <div v-if="isFloatingMode" class="floating-ball-mode">
        <!-- 服务状态指示器 -->
        <div class="floating-status-container">
          <div class="service-status-collapsed">
            <span
              :class="[
                'status-indicator',
                'floating-status-indicator',
                serviceStatus === '已连接' ? 'online' : 'offline',
              ]"
            ></span>
            <!-- <span class="status-text floating-status-text">{{
              serviceStatus
            }}</span> -->
          </div>
        </div>
        <!-- 恢复按钮 -->
        <button
          @click.stop="toggleFloatingMode"
          class="floating-restore-btn"
          title="恢复正常模式"
          :style="{
            fontSize: '0.8em',
            top: '10px',
            right: '10px',
            width: '28px',
            height: '28px',
          }"
        >
          <i class="fas fa-expand-alt"></i>
        </button>

        <div class="floating-ball-content" @mousedown.self="startDrag">
          <!-- 声纹可视化 -->
          <div class="floating-visualizer" :class="{ active: isRecording }">
            <AudioVisualizer
              :analyser="analyser"
              :isRecording="isRecording"
              :visualizerType="settings.visualizerType"
            />
          </div>

          <!-- 服务未启动或未连接时显示启动服务按钮 -->
          <div
            v-if="
              serviceStatus === '服务未启动' ||
              serviceStatus === '连接失败1' ||
              serviceStatus === '连接失败2' ||
              serviceStatus.includes('失败')
            "
            class="floating-service-not-started"
          >
            <button
              @click="startOrRestartService()"
              class="floating-start-service-btn"
              :title="
                serviceStatus === '服务未启动' ? '启动服务' : '重新启动服务'
              "
            >
              <i class="fas fa-play"></i>
            </button>
          </div>

          <!-- 服务正在加载时显示加载中状态 -->
          <div
            v-else-if="
              serviceStatus === '模型加载中...' ||
              serviceStatus === '正在启动服务...' ||
              serviceStatus === '正在重启服务...'
            "
            class="floating-service-loading"
          >
            <div class="floating-loading-spinner"></div>
          </div>

          <!-- 服务已连接时显示录音控制 -->
          <div v-else class="floating-recording-controls">
            <!-- 录音模式切换按钮 -->
            <button
              @click="toggleRecordingMode"
              class="floating-mode-toggle-btn"
              :title="
                isRealtimeMode
                  ? '切换到一次性识别模式'
                  : '切换到实时流式识别模式'
              "
              :disabled="isRecording || serviceStatus !== '已连接'"
            >
              <i
                class="fas"
                :class="isRealtimeMode ? 'fa-stream' : 'fa-file-audio'"
              ></i>
            </button>

            <!-- 录音按钮 -->
            <button
              @click="isRecording ? stopRecording() : startRecording()"
              :class="['floating-record-btn', isRecording ? 'recording' : '']"
              :disabled="serviceStatus !== '已连接'"
            >
              <i
                :class="['fas', isRecording ? 'fa-stop' : 'fa-microphone']"
              ></i>
            </button>
          </div>
        </div>
      </div>

      <!-- 主识别界面 -->
      <div v-if="currentView === 'main' && !isFloatingMode" class="main-view">
        <!-- 英雄区域 - 录音控制和声纹可视化 -->
        <div class="hero-section">
          <div class="hero-content">
            <div class="visualizer-container" :class="{ active: isRecording }">
              <AudioVisualizer
                :analyser="analyser"
                :isRecording="isRecording"
                :visualizerType="settings.visualizerType"
              />
            </div>

            <!-- 服务未启动或未连接时显示启动服务按钮 -->
            <div
              v-if="
                serviceStatus === '服务未启动' ||
                serviceStatus === '连接失败1' ||
                serviceStatus === '连接失败2' ||
                serviceStatus.includes('失败')
              "
              class="service-not-started"
            >
              <p v-if="serviceStatus === '服务未启动'">语音识别服务未启动</p>
              <p v-else>服务连接失败，请重新启动</p>
              <button
                @click="startOrRestartService()"
                class="start-service-btn"
              >
                <i class="fas fa-play"></i>
                {{
                  serviceStatus === "服务未启动" ? "启动服务" : "重新启动服务"
                }}
              </button>
            </div>

            <!-- 服务正在加载时显示加载中状态 -->
            <div
              v-else-if="
                serviceStatus === '模型加载中...' ||
                serviceStatus === '正在启动服务...' ||
                serviceStatus === '正在重启服务...'
              "
              class="service-loading"
            >
              <div class="loading-spinner"></div>
              <p>{{ serviceStatus }}</p>
            </div>

            <!-- 录音模式切换按钮 -->
            <div v-else class="recording-controls">
              <div class="recording-mode-toggle">
                <button
                  @click="toggleRecordingMode"
                  class="mode-toggle-btn"
                  :title="
                    isRealtimeMode
                      ? '切换到一次性识别模式'
                      : '切换到实时流式识别模式'
                  "
                  :disabled="isRecording || serviceStatus !== '已连接'"
                >
                  <i
                    class="fas"
                    :class="isRealtimeMode ? 'fa-stream' : 'fa-file-audio'"
                  ></i>
                  <span>{{
                    isRealtimeMode ? "实时流式识别" : "一次性识别"
                  }}</span>
                </button>
              </div>

              <!-- 服务已连接时显示录音按钮 -->
              <button
                @click="isRecording ? stopRecording() : startRecording()"
                :class="['record-btn', isRecording ? 'recording' : '']"
                :disabled="serviceStatus !== '已连接'"
              >
                <i
                  :class="['fas', isRecording ? 'fa-stop' : 'fa-microphone']"
                ></i>
                {{ isRecording ? "停止录音" : "开始录音" }}
              </button>
            </div>
          </div>
        </div>

        <!-- 识别结果区域 -->
        <div class="result-container">
          <textarea
            v-model="recognizedText"
            placeholder="说话开始识别..."
            class="result-text"
            rows="5"
            ref="textareaRef"
          ></textarea>

          <div class="action-buttons">
            <button
              @click="insertText"
              :disabled="!recognizedText.trim()"
              class="action-btn"
            >
              <i class="fas fa-paste"></i>
              插入文本
            </button>
            <button
              @click="clearText"
              :disabled="!recognizedText.trim()"
              class="action-btn"
            >
              <i class="fas fa-trash-alt"></i>
              清空
            </button>
          </div>
        </div>
      </div>

      <!-- 历史记录界面 -->
      <History
        v-if="currentView === 'history'"
        :apiBaseUrl="apiBaseUrl"
        :onSelect="selectHistoryItem"
      />

      <!-- 设置界面 -->
      <Settings
        v-if="currentView === 'settings'"
        :settings="settings"
        :onSave="saveSettings"
      />
    </div>
    <!-- 消息提示框 -->
    <MessageBox
      v-model:show="messageBoxShow"
      :title="messageBoxTitle"
      :message="messageBoxMessage"
      :type="messageBoxType"
      :showConfirm="messageBoxConfirm"
      :showClose="messageBoxShowClose"
      :duration="0"
      @close="messageBoxShow = false"
    />
  </div>
</template>

<style scoped>
:root {
  --primary-color: #1890ff;
  --primary-hover: #40a9ff;
  --success-color: #52c41a;
  --warning-color: #faad14;
  --error-color: #f5222d;
  --text-color: #333;
  --text-secondary: #666;
  --border-color: #eee;
  --bg-color: #f5f5f5;
  --sidebar-width: 220px;
  --header-height: 60px;
  --border-radius: 8px;
  --shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* 全局样式 */
.app-container {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
    "Helvetica Neue", Arial, sans-serif;
  color: var(--text-color);
  background-color: var(--bg-color);
  position: relative;
}

/* 侧边栏折叠按钮 */
.sidebar-toggle {
  position: absolute;
  left: calc(var(--sidebar-width) - 15px);
  top: 30px;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background-color: white;
  border: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 20;
  transition: all 0.3s ease;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.sidebar-toggle:hover {
  background-color: var(--primary-color);
  color: white;
}

/* 侧边栏折叠状态 */
.app-container.sidebar-collapsed .sidebar {
  transform: translateX(-100%);
  margin-left: calc(-1 * var(--sidebar-width));
}

.app-container.sidebar-collapsed .sidebar-toggle {
  left: 15px;
}

/* 折叠时的导航和状态样式 */
.collapsed-header {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  background-color: white;
  box-shadow: var(--shadow);
  z-index: 15;
  padding: 0;
  transition: all 0.3s ease;
}

.collapsed-status {
  position: fixed;
  top: 15px;
  left: 50px;
  z-index: 15;
  background-color: white;
  padding: 5px 10px;
  border-radius: 20px;
  box-shadow: var(--shadow);
}

.service-status-collapsed {
  display: flex;
  align-items: center;
}

/* 侧边栏样式 */
.sidebar {
  width: var(--sidebar-width);
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: white;
  border-right: 1px solid var(--border-color);
  box-shadow: var(--shadow);
  z-index: 10;
  transition: transform 0.3s ease;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid var(--border-color);
}

.sidebar-header h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 500;
  color: var(--primary-color);
}

.sidebar-menu {
  flex: 1;
  padding: 20px 0;
  overflow-y: auto;
}

.sidebar-item {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 12px 20px;
  border: none;
  background: none;
  text-align: left;
  font-size: 1rem;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.sidebar-item:hover {
  background-color: rgba(24, 144, 255, 0.1);
  color: var(--primary-color);
}

.sidebar-item.active {
  background-color: rgba(24, 144, 255, 0.15);
  color: var(--primary-color);
  font-weight: 500;
}

.sidebar-item i {
  margin-right: 12px;
  font-size: 1.1rem;
  width: 20px;
  text-align: center;
}

.sidebar-footer {
  padding: 15px 20px;
  border-top: 1px solid var(--border-color);
}

.service-status {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.status-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 8px;
}
.floating-status-indicator {
  margin-right: 0px;
}

@keyframes statusPulse {
  0% {
    box-shadow: 0 0 0 0 rgba(82, 196, 26, 0.6);
  }
  70% {
    box-shadow: 0 0 0 6px rgba(82, 196, 26, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(82, 196, 26, 0);
  }
}

.status-indicator.online {
  background-color: var(--success-color);
}

.status-indicator.offline {
  background-color: var(--error-color);
}

.status-text {
  font-size: 0.9rem;
  color: var(--text-secondary);
}
.floating-status-text {
  font-size: 0.6rem;
}

.service-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

/* 主内容区样式 */
.main-container {
  flex: 1;
  padding: 30px;
  overflow-y: auto;
  transition: all 0.3s ease;
  width: calc(100% - var(--sidebar-width));
}

.app-container.sidebar-collapsed .main-container {
  margin-left: 0;
  width: 100%;
}

.main-view {
  max-width: 800px;
  margin: 0 auto;
}

/* 英雄区域样式 */
.hero-section {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 30px;
  padding: 30px;
  border-radius: var(--border-radius);
  background: linear-gradient(135deg, #f0f4fa 0%, #e4eaf5 100%);
  box-shadow: 0 10px 30px rgba(24, 144, 255, 0.1);
  position: relative;
  overflow: hidden;
}

.hero-section::before {
  content: "";
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(
    circle,
    rgba(24, 144, 255, 0.05) 0%,
    transparent 70%
  );
  z-index: 1;
}

.hero-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  max-width: 600px;
  position: relative;
  z-index: 2;
}

.visualizer-container {
  width: 100%;
  height: 180px;
  margin-bottom: 25px;
  border-radius: var(--border-radius);
  background-color: rgba(255, 255, 255, 0.8);
  box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: all 0.3s ease;
  position: relative;
  z-index: 2;
}

.visualizer-container.active {
  background-color: rgba(24, 144, 255, 0.05);
  box-shadow: inset 0 0 15px rgba(24, 144, 255, 0.2);
  animation: glow 2s infinite alternate;
}

@keyframes glow {
  0% {
    box-shadow: inset 0 0 15px rgba(24, 144, 255, 0.2);
  }
  100% {
    box-shadow: inset 0 0 25px rgba(24, 144, 255, 0.4);
  }
}

.record-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 18px 36px;
  font-size: 1.3rem;
  font-weight: 500;
  border-radius: 50px;
  border: none;
  background-color: var(--primary-color);
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 6px 16px rgba(24, 144, 255, 0.4);
  z-index: 5;
}

.record-btn:hover {
  background-color: var(--primary-hover);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(24, 144, 255, 0.4);
}

.record-btn:disabled {
  background-color: #b0b0b0;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
  cursor: not-allowed;
}

.service-not-started {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
  text-align: center;
  width: 100%;
}

.service-not-started p {
  color: #666;
  font-size: 1.1rem;
  margin: 0;
}

.start-service-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 16px 32px;
  font-size: 1.2rem;
  font-weight: 500;
  border-radius: 50px;
  border: none;
  background-color: #52c41a;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 6px 16px rgba(82, 196, 26, 0.4);
}

.start-service-btn:hover {
  background-color: #73d13d;
  box-shadow: 0 8px 20px rgba(82, 196, 26, 0.5);
  transform: translateY(-2px);
}

/* 加载中状态样式 */
.service-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
  text-align: center;
  width: 100%;
}

.service-loading p {
  color: #666;
  font-size: 1.1rem;
  margin: 0;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(24, 144, 255, 0.2);
  border-radius: 50%;
  border-top-color: var(--primary-color);
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.record-btn.recording {
  background-color: var(--error-color);
  animation: pulse 1.5s infinite;
  box-shadow: 0 4px 16px rgba(245, 34, 45, 0.5);
}

.record-btn.recording:hover {
  background-color: #d32f2f;
  box-shadow: 0 6px 20px rgba(245, 34, 45, 0.6);
}

/* 录音控制区域样式 */
.recording-controls {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
  width: 100%;
}

.recording-mode-toggle {
  display: flex;
  justify-content: center;
  width: 100%;
  margin-bottom: 5px;
}

.mode-toggle-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 20px;
  font-size: 1rem;
  border-radius: 50px;
  border: 1px solid var(--primary-color);
  background-color: white;
  color: var(--primary-color);
  cursor: pointer;
  transition: all 0.3s ease;
}

.mode-toggle-btn:hover {
  background-color: rgba(24, 144, 255, 0.1);
}

.mode-toggle-btn:disabled {
  border-color: #ccc;
  color: #999;
  background-color: #f5f5f5;
  cursor: not-allowed;
}

.mode-toggle-btn i {
  font-size: 0.9rem;
}

/* 浮动球模式下的录音控制 */
.floating-recording-controls {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  position: relative;
  z-index: 15; /* 确保控制区域在可视化器之上 */
  pointer-events: auto; /* 确保控制区域可以接收点击事件 */
}

.floating-mode-toggle-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid var(--primary-color);
  background-color: white;
  color: var(--primary-color);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.8rem;
  -webkit-app-region: no-drag; /* 按钮区域不可拖动 */
  z-index: 10; /* 确保按钮在可视化器之上 */
}

.floating-mode-toggle-btn:hover {
  background-color: rgba(24, 144, 255, 0.1);
}

.floating-mode-toggle-btn:disabled {
  border-color: #ccc;
  color: #999;
  background-color: #f5f5f5;
  cursor: not-allowed;
}

@keyframes pulse {
  0% {
    transform: scale(1);
    box-shadow: 0 4px 16px rgba(245, 34, 45, 0.5);
  }
  50% {
    transform: scale(1.05);
    box-shadow: 0 6px 22px rgba(245, 34, 45, 0.7);
  }
  100% {
    transform: scale(1);
    box-shadow: 0 4px 16px rgba(245, 34, 45, 0.5);
  }
}

/* 结果容器样式 */
.result-container {
  background-color: white;
  padding: 25px;
  border-radius: var(--border-radius);
  box-shadow: var(--shadow);
}

.result-text {
  width: 100%;
  padding: 15px;
  border: 1px solid #e8e8e8;
  border-radius: var(--border-radius);
  font-size: 1.1rem;
  resize: vertical;
  line-height: 1.6;
  transition: border-color 0.3s;
  max-height: 200px;
  overflow-y: auto;
}

.result-text:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border: none;
  border-radius: 4px;
  background-color: var(--primary-color);
  color: white;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover {
  background-color: var(--primary-hover);
}

.action-btn:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

/* 图标按钮样式 */
.icon-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  border: none;
  background-color: #f0f0f0;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.icon-btn:hover {
  background-color: #e0e0e0;
  color: var(--primary-color);
}

.restart-btn:hover {
  color: var(--error-color);
}

.check-model-btn:hover {
  color: var(--primary-color);
}
/* 浮动球模式样式 */
.app-container.floating-mode {
  background: transparent;
  width: 200px;
  height: 200px;
  border-radius: 50%;
  overflow: visible; /* 改为visible确保恢复按钮不被裁剪 */
}

.app-container.floating-mode .sidebar,
.app-container.floating-mode .sidebar-toggle {
  display: none;
}

.app-container.floating-mode .main-container {
  width: 100%;
  height: 100%;
  padding: 0;
  margin: 0;
  background: transparent;
  overflow: visible;
}

.floating-ball-mode {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  overflow: visible;
}

/* 浮动球内容区域和恢复按钮需要能接收点击事件 */
.floating-ball-content,
.floating-record-btn,
.floating-status,
.floating-restore-btn,
.floating-mode-toggle-btn {
  pointer-events: auto;
}

.floating-ball-content {
  width: 150px;
  height: 150px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: visible;
  -webkit-app-region: drag; /* 允许拖动窗口 */
  transition: all 0.3s ease;
  border: 1px solid rgba(24, 144, 255, 0.2);
  margin: 6px 20px; /* 添加边距，确保不会覆盖恢复按钮 */
  z-index: 5; /* 确保内容区域在恢复按钮和状态指示器之下 */
}

.floating-visualizer {
  width: 100%;
  height: 100%;
  position: absolute;
  top: 0;
  left: 0;
  z-index: 1;
  opacity: 0.7;
  display: flex;
  justify-content: center;
  align-items: center;
}

.floating-visualizer.active {
  animation: glow 2s infinite alternate;
}

.floating-record-btn {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background-color: var(--primary-color);
  color: white;
  border: none;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 1.5rem;
  cursor: pointer;
  z-index: 2;
  box-shadow: 0 2px 10px rgba(24, 144, 255, 0.4);
  transition: all 0.3s ease;
  -webkit-app-region: no-drag; /* 按钮区域不可拖动 */
}

.floating-record-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 15px rgba(24, 144, 255, 0.5);
}

.floating-record-btn.recording {
  background-color: var(--error-color);
  animation: pulse 1.5s infinite;
}

.floating-record-btn:disabled {
  background-color: #b0b0b0;
  opacity: 0.7;
  cursor: not-allowed;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.floating-status-container {
  position: absolute;
  top: 15px;
  left: 15px;
  z-index: 20;
  display: flex;
  align-items: center;
  background-color: white;
  padding: 5px;
  border-radius: 20px;
  box-shadow: var(--shadow);
}

.floating-restore-btn {
  position: absolute;
  top: 0px;
  right: 0px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: white;
  border: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  cursor: pointer;
  z-index: 2000; /* 非常高的z-index确保不被遮挡 */
  transition: all 0.2s ease;
  -webkit-app-region: no-drag; /* 按钮区域不可拖动 */
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  pointer-events: auto; /* 确保按钮可以接收点击事件 */
}

.floating-restore-btn:hover {
  background-color: var(--primary-color);
  color: white;
}

.floating-toggle-btn {
  position: fixed;
  top: 15px;
  right: 15px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: white;
  border: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 20;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
}

.floating-toggle-btn:hover {
  background-color: var(--primary-color);
  color: white;
}

/* 浮动球模式下的动画效果 */
@keyframes float {
  0% {
    transform: translateY(0px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  }
  50% {
    transform: translateY(-5px);
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  }
  100% {
    transform: translateY(0px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  }
}

.floating-ball-content {
  animation: float 4s ease-in-out infinite;
}

/* 浮动窗口下的服务未启动状态 */
.floating-service-not-started {
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10;
}

.floating-start-service-btn {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background-color: #52c41a;
  color: white;
  border: none;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 1.5rem;
  cursor: pointer;
  box-shadow: 0 2px 10px rgba(82, 196, 26, 0.4);
  transition: all 0.3s ease;
  -webkit-app-region: no-drag; /* 按钮区域不可拖动 */
}

.floating-start-service-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 15px rgba(82, 196, 26, 0.5);
}

/* 浮动窗口下的服务加载中状态 */
.floating-service-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10;
}

.floating-loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(24, 144, 255, 0.2);
  border-radius: 50%;
  border-top-color: var(--primary-color);
  animation: spin 1s linear infinite;
}
</style>
