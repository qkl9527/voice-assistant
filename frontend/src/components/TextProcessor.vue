<template>
  <div class="text-processor-container">
    <div class="processor-header">
      <h3>AI文本处理</h3>
      <div class="model-selector">
        <select
          v-model="selectedModel"
          class="model-select"
          :disabled="isProcessing || !text"
        >
          <option value="" disabled>
            {{ availableModels.length === 0 ? "加载中..." : "请选择模型" }}
          </option>
          <option
            v-for="model in availableModels"
            :key="model.id"
            :value="model.id"
          >
            {{ model.name }}
          </option>
        </select>
      </div>
      <div class="processor-actions">
        <button
          v-for="operation in operations"
          :key="operation.id"
          class="processor-action-btn"
          :disabled="isProcessing || !text || !selectedModel"
          @click="processText(operation.id)"
        >
          <i :class="operation.icon"></i>
          {{ operation.name }}
        </button>
      </div>
    </div>

    <div class="processor-content">
      <div class="original-text">
        <div class="text-header">
          <span>原始文本</span>
        </div>
        <div class="text-content">
          <textarea
            v-model="text"
            placeholder="输入或粘贴需要处理的文本..."
            class="text-area"
            :disabled="isProcessing"
          ></textarea>
        </div>
      </div>

      <div class="processed-text">
        <div class="text-header">
          <span>处理结果</span>
          <div class="text-actions" v-if="processedText">
            <button class="text-action-btn" @click="copyToClipboard">
              <i class="fas fa-copy"></i>
              复制
            </button>
            <button class="text-action-btn" @click="useProcessedText">
              <i class="fas fa-check"></i>
              使用结果
            </button>
          </div>
        </div>
        <div class="text-content">
          <div v-if="isProcessing" class="processing-indicator">
            <i class="fas fa-spinner fa-spin"></i>
            处理中...
          </div>
          <textarea
            v-else
            v-model="processedText"
            placeholder="处理结果将显示在这里..."
            class="text-area"
            readonly
          ></textarea>
        </div>
      </div>
    </div>

    <div v-if="error" class="error-message">
      <i class="fas fa-exclamation-circle"></i>
      {{ error }}
    </div>
  </div>
</template>

<script setup>
import { ref, defineProps, defineEmits, onMounted } from "vue";

const props = defineProps({
  apiBaseUrl: {
    type: String,
    required: true,
  },
  initialText: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["processed", "use-result"]);

// 文本内容
const text = ref(props.initialText || "");
const processedText = ref("");
const isProcessing = ref(false);
const error = ref("");
const lastOperation = ref("");

// 模型选择
const selectedModel = ref("");
const availableModels = ref([]);

// 可用的处理操作
const operations = [
  { id: "fix_typos", name: "修正错别字", icon: "fas fa-spell-check" },
  { id: "polish_text", name: "润色文本", icon: "fas fa-magic" },
  { id: "summarize", name: "概述内容", icon: "fas fa-compress-alt" },
  { id: "translate", name: "翻译(中译英)", icon: "fas fa-language" },
];

// 加载LLM模型列表
async function loadLLMModels() {
  try {
    if (!props.apiBaseUrl) return false;

    console.log("正在加载LLM模型列表...");
    const response = await fetch(
      `${props.apiBaseUrl}/api/llm/providers?only_configured=true`
    );
    if (response.ok) {
      const data = await response.json();
      if (data.success && data.providers) {
        // 获取所有可用的LLM模型
        const allModels = [];
        let defaultModel = null;

        data.providers.forEach((provider) => {
          if (provider.models && provider.models.length > 0) {
            // 为每个模型添加提供商信息
            const providerModels = provider.models.map((model) => ({
              id: `${provider.id}:${model}`,
              name: `${provider.name} - ${model}`,
              provider: provider.id,
              model: model,
              is_default: provider.is_default || false,
            }));

            // 如果是默认提供商，记录其最后一个模型（假设是最新更新的）
            if (provider.is_default && providerModels.length > 0) {
              defaultModel = providerModels[providerModels.length - 1];
            }

            allModels.push(...providerModels);
          }
        });

        availableModels.value = allModels;
        console.log(`成功加载了${allModels.length}个LLM模型`);

        // 尝试从本地存储获取上次使用的模型
        let lastUsedModel = null;
        if (window.electronAPI) {
          try {
            const lastUsedModelData = await window.electronAPI.loadFromStorage(
              "lastUsedLLMModel"
            );
            if (lastUsedModelData && lastUsedModelData.modelId) {
              // 检查上次使用的模型是否仍然可用
              const modelExists = allModels.some(
                (model) => model.id === lastUsedModelData.modelId
              );
              if (modelExists) {
                lastUsedModel = lastUsedModelData.modelId;
              }
            }
          } catch (e) {
            console.error("加载上次使用的模型失败:", e);
          }
        }

        // 选择模型的优先级：
        // 1. 上次使用的模型（如果存在）
        // 2. 默认提供商的最新模型
        // 3. 第一个可用模型
        if (!selectedModel.value && allModels.length > 0) {
          if (lastUsedModel) {
            selectedModel.value = lastUsedModel;
            console.log("使用上次选择的模型:", lastUsedModel);
          } else if (defaultModel) {
            selectedModel.value = defaultModel.id;
            console.log("使用默认提供商的最新模型:", defaultModel.id);
          } else {
            selectedModel.value = allModels[0].id;
            console.log("使用第一个可用模型:", allModels[0].id);
          }
        }

        return allModels.length > 0;
      }
    }
    return false;
  } catch (error) {
    console.error("加载LLM模型列表失败:", error);
    return false;
  }
}

// 保存用户选择的模型
async function saveSelectedModel(modelId) {
  if (window.electronAPI && modelId) {
    try {
      await window.electronAPI.saveToStorage("lastUsedLLMModel", {
        modelId: modelId,
        timestamp: new Date().toISOString(),
      });
      console.log("已保存用户选择的模型:", modelId);
    } catch (e) {
      console.error("保存用户选择的模型失败:", e);
    }
  }
}

// 处理文本
async function processText(operation) {
  if (isProcessing.value || !text.value.trim() || !selectedModel.value) return;

  isProcessing.value = true;
  error.value = "";
  lastOperation.value = operation;

  try {
    // 解析选中的模型
    const [provider, model] = selectedModel.value.split(":");

    // 保存用户选择的模型
    await saveSelectedModel(selectedModel.value);

    const payload = {
      text: text.value,
      operation: operation,
      provider: provider,
      model: model,
    };

    // 如果是翻译操作，添加目标语言
    if (operation === "translate") {
      payload.target_language = "英文";
    }

    const response = await fetch(`${props.apiBaseUrl}/api/llm/process`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (data.success) {
      processedText.value = data.result;
      emit("processed", {
        original: text.value,
        processed: data.result,
        operation: operation,
      });
    } else {
      error.value = data.error || "处理失败";
      // 不清空处理结果，只显示错误提示
    }
  } catch (err) {
    console.error("处理文本失败:", err);
    error.value = err.message || "处理失败，请检查网络连接";
    // 不清空处理结果，只显示错误提示
  } finally {
    isProcessing.value = false;
  }
}

// 复制到剪贴板
function copyToClipboard() {
  if (!processedText.value) return;

  navigator.clipboard
    .writeText(processedText.value)
    .then(() => {
      alert("已复制到剪贴板");
    })
    .catch((err) => {
      console.error("复制失败:", err);
      alert("复制失败");
    });
}

// 使用处理结果
function useProcessedText() {
  if (!processedText.value) return;

  emit("use-result", processedText.value);
}

// 组件挂载时加载模型列表
onMounted(async () => {
  // 加载LLM模型列表
  await loadLLMModels();
});
</script>

<style scoped>
.text-processor-container {
  padding: 15px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.processor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  flex-wrap: wrap;
  gap: 10px;
}

.processor-header h3 {
  margin: 0;
  color: #333;
  flex: 1;
}

.model-selector {
  min-width: 200px;
  max-width: 300px;
}

.model-select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  background-color: #fff;
  cursor: pointer;
}

.model-select:focus {
  outline: none;
  border-color: #4a6cf7;
}

.model-select:disabled {
  background-color: #f9f9f9;
  cursor: not-allowed;
}

.processor-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.processor-action-btn {
  padding: 6px 12px;
  background-color: #4a6cf7;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 5px;
  transition: background-color 0.3s;
}

.processor-action-btn:hover {
  background-color: #3a5ce5;
}

.processor-action-btn:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.processor-action-btn i {
  font-size: 12px;
}

.processor-content {
  display: flex;
  gap: 15px;
  margin-bottom: 15px;
}

.original-text,
.processed-text {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.text-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-weight: bold;
  color: #555;
}

.text-actions {
  display: flex;
  gap: 8px;
}

.text-action-btn {
  padding: 4px 8px;
  background-color: #f0f0f0;
  color: #333;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 5px;
  transition: background-color 0.3s;
}

.text-action-btn:hover {
  background-color: #e0e0e0;
}

.text-content {
  flex: 1;
  position: relative;
}

.text-area {
  width: 100%;
  height: 200px;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  resize: none;
  font-size: 14px;
  line-height: 1.5;
}

.text-area:focus {
  outline: none;
  border-color: #4a6cf7;
}

.text-area:disabled {
  background-color: #f9f9f9;
  cursor: not-allowed;
}

.processing-indicator {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background-color: rgba(255, 255, 255, 0.8);
  color: #4a6cf7;
  font-size: 16px;
  gap: 10px;
}

.processing-indicator i {
  font-size: 24px;
}

.error-message {
  padding: 10px;
  background-color: #fff3f3;
  color: #d32f2f;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.error-message i {
  font-size: 16px;
}
</style>
