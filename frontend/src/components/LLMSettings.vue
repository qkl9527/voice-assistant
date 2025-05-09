<template>
  <div class="llm-settings-container">
    <h2>大语言模型设置</h2>

    <div class="provider-tabs-container">
      <div class="category-tabs">
        <div
          v-for="category in providerCategories"
          :key="category.id"
          :class="['category-tab', { active: activeCategory === category.id }]"
          @click="setActiveCategory(category.id)"
        >
          {{ category.name }}
        </div>
      </div>

      <div class="provider-tabs">
        <div
          v-for="provider in filteredProviders"
          :key="provider.id"
          :class="['provider-tab', { active: activeProvider === provider.id }]"
          @click="setActiveProvider(provider.id)"
        >
          {{ provider.name }}
        </div>
      </div>

      <div class="search-container">
        <input
          type="text"
          v-model="searchQuery"
          placeholder="搜索模型..."
          class="search-input"
        />
      </div>
    </div>

    <div class="provider-settings">
      <!-- 动态配置界面 -->
      <div v-if="activeProvider && providerConfigs[activeProvider]">
        <!-- API密钥 -->
        <div class="setting-item" v-if="hasField('api_key')">
          <div class="setting-label">
            <label :for="`${activeProvider}-api-key`">API密钥</label>
            <span class="setting-description"
              >{{ getProviderName() }} API密钥</span
            >
          </div>
          <div class="setting-control">
            <input
              type="password"
              :id="`${activeProvider}-api-key`"
              v-model="providerConfigs[activeProvider].api_key"
              class="text-input"
              :placeholder="getApiKeyPlaceholder()"
            />
          </div>
        </div>

        <!-- Secret密钥 (百度千帆等) -->
        <div class="setting-item" v-if="hasField('secret_key')">
          <div class="setting-label">
            <label :for="`${activeProvider}-secret-key`">Secret密钥</label>
            <span class="setting-description"
              >{{ getProviderName() }} Secret密钥</span
            >
          </div>
          <div class="setting-control">
            <input
              type="password"
              :id="`${activeProvider}-secret-key`"
              v-model="providerConfigs[activeProvider].secret_key"
              class="text-input"
              placeholder="..."
            />
          </div>
        </div>

        <!-- Access Key (AWS等) -->
        <div class="setting-item" v-if="hasField('access_key')">
          <div class="setting-label">
            <label :for="`${activeProvider}-access-key`">Access Key</label>
            <span class="setting-description"
              >{{ getProviderName() }} Access Key</span
            >
          </div>
          <div class="setting-control">
            <input
              type="password"
              :id="`${activeProvider}-access-key`"
              v-model="providerConfigs[activeProvider].access_key"
              class="text-input"
              placeholder="..."
            />
          </div>
        </div>

        <!-- Project ID (华为云等) -->
        <div class="setting-item" v-if="hasField('project_id')">
          <div class="setting-label">
            <label :for="`${activeProvider}-project-id`">项目ID</label>
            <span class="setting-description"
              >{{ getProviderName() }} 项目ID</span
            >
          </div>
          <div class="setting-control">
            <input
              type="text"
              :id="`${activeProvider}-project-id`"
              v-model="providerConfigs[activeProvider].project_id"
              class="text-input"
              placeholder="..."
            />
          </div>
        </div>

        <!-- Region (AWS等) -->
        <div class="setting-item" v-if="hasField('region')">
          <div class="setting-label">
            <label :for="`${activeProvider}-region`">区域</label>
            <span class="setting-description"
              >{{ getProviderName() }} 服务区域</span
            >
          </div>
          <div class="setting-control">
            <input
              type="text"
              :id="`${activeProvider}-region`"
              v-model="providerConfigs[activeProvider].region"
              class="text-input"
              placeholder="us-east-1"
            />
          </div>
        </div>

        <!-- Endpoint (Azure等) -->
        <div class="setting-item" v-if="hasField('endpoint')">
          <div class="setting-label">
            <label :for="`${activeProvider}-endpoint`">终端节点</label>
            <span class="setting-description"
              >{{ getProviderName() }} 终端节点</span
            >
          </div>
          <div class="setting-control">
            <input
              type="text"
              :id="`${activeProvider}-endpoint`"
              v-model="providerConfigs[activeProvider].endpoint"
              class="text-input"
              placeholder="https://your-resource-name.openai.azure.com"
            />
          </div>
        </div>

        <!-- Deployment Name (Azure等) -->
        <div class="setting-item" v-if="hasField('deployment_name')">
          <div class="setting-label">
            <label :for="`${activeProvider}-deployment-name`">部署名称</label>
            <span class="setting-description"
              >{{ getProviderName() }} 部署名称</span
            >
          </div>
          <div class="setting-control">
            <input
              type="text"
              :id="`${activeProvider}-deployment-name`"
              v-model="providerConfigs[activeProvider].deployment_name"
              class="text-input"
              placeholder="your-deployment-name"
            />
          </div>
        </div>

        <!-- API Version (Azure等) -->
        <div class="setting-item" v-if="hasField('api_version')">
          <div class="setting-label">
            <label :for="`${activeProvider}-api-version`">API版本</label>
            <span class="setting-description"
              >{{ getProviderName() }} API版本</span
            >
          </div>
          <div class="setting-control">
            <input
              type="text"
              :id="`${activeProvider}-api-version`"
              v-model="providerConfigs[activeProvider].api_version"
              class="text-input"
              placeholder="2023-05-15"
            />
          </div>
        </div>

        <!-- API基础URL -->
        <div class="setting-item" v-if="hasField('base_url')">
          <div class="setting-label">
            <label :for="`${activeProvider}-base-url`">API基础URL</label>
            <span class="setting-description"
              >可选，用于自定义API端点或使用代理</span
            >
          </div>
          <div class="setting-control">
            <input
              type="text"
              :id="`${activeProvider}-base-url`"
              v-model="providerConfigs[activeProvider].base_url"
              class="text-input"
              :placeholder="getBaseUrlPlaceholder()"
            />
          </div>
        </div>

        <!-- 模型选择 -->
        <div class="setting-item" v-if="hasField('model')">
          <div class="setting-label">
            <label :for="`${activeProvider}-model`">模型</label>
            <span class="setting-description"
              >选择要使用的{{ getProviderName() }}模型</span
            >
          </div>
          <div class="setting-control">
            <select
              :id="`${activeProvider}-model`"
              v-model="providerConfigs[activeProvider].model"
              class="select-input"
            >
              <option
                v-for="model in getProviderModels(activeProvider)"
                :key="model"
                :value="model"
              >
                {{ model }}
              </option>
            </select>
          </div>
        </div>

        <!-- 温度参数 -->
        <div class="setting-item" v-if="hasField('temperature')">
          <div class="setting-label">
            <label :for="`${activeProvider}-temperature`">温度</label>
            <span class="setting-description">控制生成文本的随机性 (0-1)</span>
          </div>
          <div class="setting-control">
            <input
              type="range"
              :id="`${activeProvider}-temperature`"
              v-model.number="providerConfigs[activeProvider].temperature"
              min="0"
              max="1"
              step="0.1"
              class="range-input"
            />
            <span class="range-value">{{
              providerConfigs[activeProvider].temperature
            }}</span>
          </div>
        </div>

        <!-- 最大令牌数 -->
        <div class="setting-item" v-if="hasField('max_tokens')">
          <div class="setting-label">
            <label :for="`${activeProvider}-max-tokens`">最大令牌数</label>
            <span class="setting-description">生成文本的最大长度</span>
          </div>
          <div class="setting-control">
            <input
              type="number"
              :id="`${activeProvider}-max-tokens`"
              v-model.number="providerConfigs[activeProvider].max_tokens"
              min="1"
              max="8192"
              class="number-input"
            />
          </div>
        </div>
      </div>

      <!-- 设为默认 -->
      <div class="setting-item">
        <div class="setting-label">
          <label for="is-default">设为默认</label>
          <span class="setting-description"
            >将此服务设为默认使用的大语言模型服务</span
          >
        </div>
        <div class="setting-control">
          <label class="switch">
            <input type="checkbox" id="is-default" v-model="isDefault" />
            <span class="slider round"></span>
          </label>
        </div>
      </div>
    </div>

    <div class="settings-actions">
      <button class="btn-reset" @click="resetSettings">重置</button>
      <button class="btn-save" @click="saveSettings">保存</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";

const props = defineProps({
  apiBaseUrl: {
    type: String,
    required: true,
  },
});

const emit = defineEmits(["saved"]);

// 模型分类
const providerCategories = ref([
  { id: "all", name: "全部" },
  { id: "international", name: "国际模型" },
  { id: "chinese", name: "国内模型" },
  { id: "cloud", name: "云服务" },
  { id: "local", name: "本地部署" },
  { id: "aggregator", name: "聚合服务" },
]);

// 当前活动的分类
const activeCategory = ref("all");

// 搜索查询
const searchQuery = ref("");

// 支持的服务提供商
const providers = ref([
  // 国际模型
  { id: "openai", name: "OpenAI", category: "international" },
  { id: "anthropic", name: "Anthropic", category: "international" },
  { id: "gemini", name: "Google Gemini", category: "international" },
  { id: "groq", name: "Groq", category: "international" },
  { id: "copilot", name: "GitHub Copilot", category: "international" },
  { id: "moonshot", name: "硅基流动", category: "international" },

  // 国内模型
  { id: "zhipu", name: "智谱AI", category: "chinese" },
  { id: "qianfan", name: "百度千帆", category: "chinese" },
  { id: "dashscope", name: "阿里云灵积", category: "chinese" },
  { id: "qwen", name: "阿里云百炼", category: "chinese" },
  { id: "bytedance", name: "字节跳动(豆包)", category: "chinese" },

  // 云服务
  { id: "huawei", name: "华为云", category: "cloud" },
  { id: "aws", name: "AWS Bedrock", category: "cloud" },
  { id: "azure", name: "Azure OpenAI", category: "cloud" },

  // 本地部署
  { id: "ollama", name: "Ollama", category: "local" },

  // 聚合服务
  { id: "oneapi", name: "OneAPI", category: "aggregator" },
  { id: "openrouter", name: "OpenRouter", category: "aggregator" },
  { id: "litellm", name: "LiteLLM", category: "aggregator" },
]);

// 过滤后的提供商列表
const filteredProviders = computed(() => {
  return providers.value.filter((provider) => {
    // 先按分类过滤
    const categoryMatch =
      activeCategory.value === "all" ||
      provider.category === activeCategory.value;

    // 再按搜索词过滤
    const searchMatch =
      searchQuery.value === "" ||
      provider.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      provider.id.toLowerCase().includes(searchQuery.value.toLowerCase());

    return categoryMatch && searchMatch;
  });
});

// 当前活动的提供商
const activeProvider = ref("openai");

// 设置活动分类
function setActiveCategory(categoryId) {
  activeCategory.value = categoryId;
}

// 是否设为默认
const isDefault = ref(false);

// 各提供商配置
const providerConfigs = ref({});

// 各提供商模型列表
const providerModels = ref({});

// 获取指定提供商的模型列表
function getProviderModels(providerId) {
  return providerModels.value[providerId] || [];
}

// 设置活动提供商
function setActiveProvider(providerId) {
  activeProvider.value = providerId;
}

// 检查当前提供商是否有指定字段
function hasField(fieldName) {
  return (
    activeProvider.value &&
    providerConfigs.value[activeProvider.value] &&
    fieldName in providerConfigs.value[activeProvider.value]
  );
}

// 获取当前提供商名称
function getProviderName() {
  const provider = providers.value.find((p) => p.id === activeProvider.value);
  return provider ? provider.name : activeProvider.value;
}

// 获取API密钥占位符
function getApiKeyPlaceholder() {
  const placeholders = {
    openai: "sk-...",
    anthropic: "sk-ant-...",
    gemini: "AIza...",
    groq: "gsk_...",
    moonshot: "sk-...",
    dashscope: "sk-...",
    default: "请输入API密钥",
  };

  return placeholders[activeProvider.value] || placeholders.default;
}

// 获取基础URL占位符
function getBaseUrlPlaceholder() {
  // 从提供商列表中查找当前提供商
  const provider = providers.value.find((p) => p.id === activeProvider.value);
  if (provider && provider.base_url_default) {
    return provider.base_url_default;
  }

  // 如果没有找到默认值，返回通用提示
  return "请输入API基础URL";
}

// 加载配置
async function loadConfigs() {
  try {
    const response = await fetch(`${props.apiBaseUrl}/api/llm/configs`);
    if (response.ok) {
      const data = await response.json();
      if (data.success && data.configs) {
        // 更新配置
        data.configs.forEach((config) => {
          const providerId = config.provider;

          // 如果提供商配置不存在，先创建一个空配置
          if (!providerConfigs.value[providerId]) {
            providerConfigs.value[providerId] = {
              temperature: 0.7,
              max_tokens: 1000,
            };

            // 尝试从提供商列表中获取默认值
            const provider = providers.value.find((p) => p.id === providerId);
            if (provider) {
              if (provider.base_url_default) {
                providerConfigs.value[providerId].base_url =
                  provider.base_url_default;
              }

              // 如果有模型列表，使用第一个模型
              if (providerModels.value[providerId]?.length > 0) {
                providerConfigs.value[providerId].model =
                  providerModels.value[providerId][0];
              }
            }
          }

          // 更新配置，但保留敏感信息
          const currentConfig = providerConfigs.value[providerId];
          const newConfig = config.config;

          // 合并配置，但不覆盖敏感信息
          for (const key in newConfig) {
            if (
              key !== "api_key" &&
              key !== "secret_key" &&
              key !== "access_key"
            ) {
              currentConfig[key] = newConfig[key];
            }
          }

          // 如果是默认配置，设置为活动提供商
          if (config.is_default) {
            activeProvider.value = providerId;
            isDefault.value = true;
          }
        });

        console.log("成功加载LLM配置");
      }
    }
  } catch (error) {
    console.error("加载LLM配置失败:", error);
  }
}

// 保存配置
async function saveSettings() {
  try {
    const config = {
      provider: activeProvider.value,
      config: providerConfigs.value[activeProvider.value],
      is_default: isDefault.value,
    };

    const response = await fetch(`${props.apiBaseUrl}/api/llm/configs`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(config),
    });

    if (response.ok) {
      const data = await response.json();
      if (data.success) {
        alert("配置保存成功");
        emit("saved");
      } else {
        alert(`保存失败: ${data.error}`);
      }
    } else {
      alert("保存失败，请检查网络连接");
    }
  } catch (error) {
    console.error("保存LLM配置失败:", error);
    alert(`保存失败: ${error.message}`);
  }
}

// 重置设置
async function resetSettings() {
  try {
    // 从提供商列表中查找当前提供商
    const provider = providers.value.find((p) => p.id === activeProvider.value);

    if (provider) {
      // 保留当前API密钥和其他敏感信息
      const currentConfig = { ...providerConfigs.value[activeProvider.value] };
      const sensitiveKeys = [
        "api_key",
        "secret_key",
        "access_key",
        "project_id",
        "endpoint",
        "deployment_name",
      ];

      // 创建重置后的配置
      const resetConfig = {
        temperature: 0.7,
        max_tokens: 1000,
      };

      // 如果有默认的base_url，使用它
      if (provider.base_url_default) {
        resetConfig.base_url = provider.base_url_default;
      }

      // 如果有模型列表，使用第一个模型
      if (providerModels.value[activeProvider.value]?.length > 0) {
        resetConfig.model = providerModels.value[activeProvider.value][0];
      }

      // 保留敏感信息
      sensitiveKeys.forEach((key) => {
        if (currentConfig[key]) {
          resetConfig[key] = currentConfig[key];
        }
      });

      // 更新配置
      providerConfigs.value[activeProvider.value] = resetConfig;

      console.log("重置配置成功");
    } else {
      console.error("未找到当前提供商信息");
    }
  } catch (error) {
    console.error("重置设置失败:", error);
  }
}

// 加载提供商和模型列表
async function loadProviders() {
  try {
    const response = await fetch(`${props.apiBaseUrl}/api/llm/providers`);
    if (response.ok) {
      const data = await response.json();
      if (data.success && data.providers) {
        // 更新提供商列表
        providers.value = data.providers.map((provider) => ({
          id: provider.id,
          name: provider.name,
          category: provider.category || "all", // 如果后端没有提供分类，默认为"all"
          base_url_default: provider.base_url_default,
        }));

        // 更新模型列表并初始化配置
        data.providers.forEach((provider) => {
          // 更新模型列表
          if (provider.models && provider.models.length > 0) {
            providerModels.value[provider.id] = provider.models;
          }

          // 初始化配置（如果不存在）
          if (!providerConfigs.value[provider.id]) {
            // 创建默认配置
            const defaultConfig = {
              temperature: 0.7,
              max_tokens: 1000,
            };

            // 添加默认的base_url
            if (provider.base_url_default) {
              defaultConfig.base_url = provider.base_url_default;
            }

            // 添加默认模型
            if (provider.models && provider.models.length > 0) {
              defaultConfig.model = provider.models[0];
            }

            // 根据提供商类型添加特定字段
            if (provider.id === "azure") {
              defaultConfig.api_version = "2023-05-15";
              defaultConfig.endpoint = "";
              defaultConfig.deployment_name = "";
            } else if (provider.id === "aws") {
              defaultConfig.region = "us-east-1";
              defaultConfig.access_key = "";
              defaultConfig.secret_key = "";
            } else if (provider.id === "qianfan") {
              defaultConfig.api_key = "";
              defaultConfig.secret_key = "";
            } else if (provider.id !== "ollama") {
              // Ollama不需要API密钥
              defaultConfig.api_key = "";
            }

            // 保存到配置对象
            providerConfigs.value[provider.id] = defaultConfig;
          }
        });

        console.log("成功加载提供商和模型列表");
      }
    }
  } catch (error) {
    console.error("加载提供商和模型列表失败:", error);
  }
}

// 组件挂载时加载配置和提供商信息
onMounted(async () => {
  await loadProviders(); // 先加载提供商信息
  await loadConfigs(); // 再加载用户配置
});
</script>

<style scoped>
.llm-settings-container {
  padding: 20px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

h2 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #333;
  font-size: 1.5rem;
}

.provider-tabs-container {
  display: flex;
  flex-direction: column;
  margin-bottom: 20px;
}

.category-tabs {
  display: flex;
  overflow-x: auto;
  scrollbar-width: thin;
  border-bottom: 1px solid #ddd;
  margin-bottom: 10px;
}

.category-tab {
  padding: 10px 15px;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.3s;
  white-space: nowrap;
}

.category-tab:hover {
  background-color: #f5f5f5;
}

.category-tab.active {
  border-bottom: 2px solid #4a6cf7;
  color: #4a6cf7;
  font-weight: bold;
}

.provider-tabs {
  display: flex;
  flex-wrap: wrap;
  margin-bottom: 15px;
  max-height: 120px;
  overflow-y: auto;
  scrollbar-width: thin;
  border: 1px solid #eee;
  border-radius: 4px;
  padding: 5px;
}

.provider-tab {
  padding: 8px 12px;
  margin: 4px;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.3s;
  background-color: #f5f5f5;
  font-size: 0.9rem;
}

.provider-tab:hover {
  background-color: #e0e0e0;
}

.provider-tab.active {
  background-color: #4a6cf7;
  color: white;
  font-weight: bold;
}

.search-container {
  margin-bottom: 10px;
}

.search-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.search-input:focus {
  border-color: #4a6cf7;
  outline: none;
}

.provider-settings {
  margin-bottom: 20px;
}

.setting-item {
  display: flex;
  margin-bottom: 15px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.setting-label {
  flex: 1;
  padding-right: 15px;
}

.setting-label label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  color: #333;
}

.setting-description {
  display: block;
  font-size: 0.85rem;
  color: #666;
}

.setting-control {
  flex: 2;
}

.text-input,
.select-input,
.number-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.text-input:focus,
.select-input:focus,
.number-input:focus {
  border-color: #4a6cf7;
  outline: none;
}

.range-input {
  width: calc(100% - 40px);
  margin-right: 10px;
  vertical-align: middle;
}

.range-value {
  display: inline-block;
  width: 30px;
  text-align: center;
  font-weight: bold;
  color: #4a6cf7;
}

.settings-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.btn-reset,
.btn-save {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s;
}

.btn-reset {
  background-color: #f5f5f5;
  color: #333;
}

.btn-save {
  background-color: #4a6cf7;
  color: white;
}

.btn-reset:hover {
  background-color: #e0e0e0;
}

.btn-save:hover {
  background-color: #3a5ce5;
}

/* 开关样式 */
.switch {
  position: relative;
  display: inline-block;
  width: 50px;
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
  height: 16px;
  width: 16px;
  left: 4px;
  bottom: 4px;
  background-color: white;
  transition: 0.4s;
}

input:checked + .slider {
  background-color: #4a6cf7;
}

input:focus + .slider {
  box-shadow: 0 0 1px #4a6cf7;
}

input:checked + .slider:before {
  transform: translateX(26px);
}

.slider.round {
  border-radius: 24px;
}

.slider.round:before {
  border-radius: 50%;
}
</style>
