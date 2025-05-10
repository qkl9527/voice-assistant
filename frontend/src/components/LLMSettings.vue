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
        <!-- 未配置密钥时的提示 -->
        <div
          class="setting-notice api-key-notice"
          v-if="
            !isConfigured(activeProvider) &&
            activeProvider !== 'ollama' &&
            (hasField('api_key') ||
              hasField('secret_key') ||
              hasField('access_key') ||
              (activeProvider === 'azure' &&
                (hasField('endpoint') || hasField('deployment_name'))))
          "
        >
          <i class="fas fa-info-circle"></i>
          <span v-if="activeProvider === 'azure'"
            >请先配置API密钥、终端节点和部署名称等必要参数，然后才能使用此模型</span
          >
          <span v-else-if="hasField('secret_key') && !hasField('api_key')"
            >请先配置Secret密钥等必要参数，然后才能使用此模型</span
          >
          <span v-else-if="hasField('access_key')"
            >请先配置Access Key等必要参数，然后才能使用此模型</span
          >
          <span v-else>请先配置API密钥等必要参数，然后才能使用此模型</span>
        </div>

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
          <div class="setting-control model-control">
            <!-- 当model_url为空但有模型列表时，显示下拉框和输入框组合 -->
            <div
              v-if="!hasModelUrl(activeProvider) && hasModels(activeProvider)"
              class="model-input-group"
            >
              <select
                :id="`${activeProvider}-model-select`"
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
                <option value="custom">自定义模型...</option>
              </select>
              <input
                v-if="providerConfigs[activeProvider].model === 'custom'"
                type="text"
                :id="`${activeProvider}-model-custom`"
                v-model="customModel"
                class="text-input"
                placeholder="请输入模型名称"
                @input="updateCustomModel"
              />
            </div>
            <!-- 当model_url为空且没有模型列表时，显示纯输入框 -->
            <input
              v-else-if="!hasModelUrl(activeProvider)"
              type="text"
              :id="`${activeProvider}-model`"
              v-model="providerConfigs[activeProvider].model"
              class="text-input"
              placeholder="请输入模型名称"
            />
            <!-- 当model_url不为空时，显示下拉框 -->
            <select
              v-else
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
            <div class="model-buttons">
              <button
                class="btn-reload-models"
                @click="fetchModels(activeProvider, false)"
                :disabled="
                  isLoadingModels ||
                  !hasModelUrl(activeProvider) ||
                  (!isConfigured(activeProvider) && activeProvider !== 'ollama')
                "
                :title="
                  !hasModelUrl(activeProvider)
                    ? '该平台不支持获取模型列表'
                    : !isConfigured(activeProvider) &&
                      activeProvider !== 'ollama'
                    ? '请先配置API密钥'
                    : '全量更新模型列表'
                "
              >
                <i
                  :class="[
                    'fas',
                    isLoadingModels ? 'fa-spinner fa-spin' : 'fa-sync-alt',
                  ]"
                ></i>
              </button>
              <button
                class="btn-reload-models"
                @click="fetchModels(activeProvider, true)"
                :disabled="
                  isLoadingModels ||
                  !hasModelUrl(activeProvider) ||
                  (!isConfigured(activeProvider) && activeProvider !== 'ollama')
                "
                :title="
                  !hasModelUrl(activeProvider)
                    ? '该平台不支持获取模型列表'
                    : !isConfigured(activeProvider) &&
                      activeProvider !== 'ollama'
                    ? '请先配置API密钥'
                    : '增量更新模型列表'
                "
              >
                <i class="fas fa-plus"></i>
              </button>
            </div>
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
const providerCategories = ref([{ id: "all", name: "全部" }]);

// 当前活动的分类
const activeCategory = ref("all");

// 搜索查询
const searchQuery = ref("");

// 支持的服务提供商
const providers = ref([]);

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

// 模型加载状态
const isLoadingModels = ref(false);

// 自定义模型输入
const customModel = ref("");

// 获取指定提供商的模型列表
function getProviderModels(providerId) {
  return providerModels.value[providerId] || [];
}

// 检查提供商是否有模型列表
function hasModels(providerId) {
  return (
    providerModels.value[providerId] &&
    providerModels.value[providerId].length > 0
  );
}

// 更新自定义模型
function updateCustomModel() {
  if (customModel.value && customModel.value.trim() !== "") {
    providerConfigs.value[activeProvider.value].model = customModel.value;
  }
}

// 设置活动提供商
function setActiveProvider(providerId) {
  // 如果切换到不同的提供商
  if (activeProvider.value !== providerId) {
    // 重置自定义模型
    customModel.value = "";

    activeProvider.value = providerId;

    // 检查是否有配置
    const provider = providers.value.find((p) => p.id === providerId);
    if (provider && provider.is_configured) {
      // 如果已配置，检查是否需要设置默认值
      const config = providerConfigs.value[providerId];
      if (!config.model && providerModels.value[providerId]?.length > 0) {
        config.model = providerModels.value[providerId][0];
      }

      // 如果当前模型是"custom"，但没有自定义模型值，则设置为第一个可用模型
      if (
        config.model === "custom" &&
        !customModel.value &&
        providerModels.value[providerId]?.length > 0
      ) {
        config.model = providerModels.value[providerId][0];
      }
    }
  }
}

// 检查提供商是否已配置API密钥
function isConfigured(providerId) {
  const provider = providers.value.find((p) => p.id === providerId);
  return provider && provider.is_configured;
}

// 检查提供商是否有model_url
function hasModelUrl(providerId) {
  const provider = providers.value.find((p) => p.id === providerId);
  return provider && provider.model_url && provider.model_url.trim() !== "";
}

// 从API获取模型列表
async function fetchModels(providerId, isIncremental = false) {
  if (!providerId || isLoadingModels.value) return;

  // 检查是否已配置API密钥
  if (!isConfigured(providerId) && providerId !== "ollama") {
    alert("请先配置API密钥后再获取模型列表");
    return;
  }

  try {
    isLoadingModels.value = true;

    // 获取当前配置
    const currentConfig = providerConfigs.value[providerId];

    // 获取平台信息
    const provider = providers.value.find((p) => p.id === providerId);
    if (!provider) {
      alert(`未找到提供商信息: ${providerId}`);
      isLoadingModels.value = false;
      return;
    }

    // 发送请求获取模型列表
    const response = await fetch(`${props.apiBaseUrl}/api/llm/fetch_models`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        provider: providerId,
        config: currentConfig,
        is_incremental: isIncremental,
      }),
    });

    if (response.ok) {
      const data = await response.json();
      if (data.success && data.models && data.models.length > 0) {
        // 更新模型列表
        if (isIncremental && providerModels.value[providerId]) {
          // 增量更新：合并现有模型和新模型，去重
          const existingModels = new Set(providerModels.value[providerId]);
          data.models.forEach((model) => existingModels.add(model));
          providerModels.value[providerId] = Array.from(existingModels);
        } else {
          // 全量更新：直接使用新模型列表
          providerModels.value[providerId] = data.models;
        }

        // 更新提供商的模型列表
        provider.models = providerModels.value[providerId];

        // 如果当前选择的模型不在列表中且不是自定义模型，选择第一个模型
        if (
          currentConfig.model !== "custom" &&
          !provider.models.includes(currentConfig.model) &&
          provider.models.length > 0
        ) {
          currentConfig.model = provider.models[0];
        }

        alert(
          `成功${isIncremental ? "增量" : "全量"}获取到${
            data.models.length
          }个模型，当前共有${provider.models.length}个模型`
        );
      } else {
        alert("未获取到模型列表，请检查API配置");
      }
    } else {
      const errorData = await response.json();
      alert(`获取模型列表失败: ${errorData.error || "请检查API配置"}`);
    }
  } catch (error) {
    console.error("获取模型列表失败:", error);
    alert(`获取模型列表失败: ${error.message}`);
  } finally {
    isLoadingModels.value = false;
  }
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
        // 按更新时间排序，确保最新的配置在最后
        const sortedConfigs = [...data.configs].sort((a, b) => {
          return new Date(a.updated_at) - new Date(b.updated_at);
        });

        // 更新配置
        sortedConfigs.forEach((config) => {
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

          // 获取当前配置
          const currentConfig = providerConfigs.value[providerId];
          const newConfig = config.config;

          // 保存敏感信息
          const sensitiveInfo = {
            api_key: currentConfig.api_key,
            secret_key: currentConfig.secret_key,
            access_key: currentConfig.access_key,
          };

          // 完全替换配置（使用最新的配置）
          for (const key in newConfig) {
            currentConfig[key] = newConfig[key];
          }

          // 恢复敏感信息
          if (sensitiveInfo.api_key)
            currentConfig.api_key = sensitiveInfo.api_key;
          if (sensitiveInfo.secret_key)
            currentConfig.secret_key = sensitiveInfo.secret_key;
          if (sensitiveInfo.access_key)
            currentConfig.access_key = sensitiveInfo.access_key;

          // 如果是默认配置，设置为活动提供商
          if (config.is_default) {
            activeProvider.value = providerId;
            isDefault.value = true;
          }

          // 如果当前模型不在模型列表中，且不是"custom"，则可能是自定义模型
          if (
            currentConfig.model &&
            providerModels.value[providerId] &&
            !providerModels.value[providerId].includes(currentConfig.model) &&
            currentConfig.model !== "custom"
          ) {
            // 如果平台没有model_url，则将该模型添加到模型列表中
            const provider = providers.value.find((p) => p.id === providerId);
            if (
              provider &&
              (!provider.model_url || provider.model_url.trim() === "")
            ) {
              // 增量更新模型列表
              if (!providerModels.value[providerId]) {
                providerModels.value[providerId] = [];
              }
              providerModels.value[providerId].push(currentConfig.model);
            }
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
    const currentConfig = providerConfigs.value[activeProvider.value];

    // 检查配置是否有效（例如，是否有API密钥）
    let isConfigured = false;
    if (activeProvider.value === "ollama") {
      // Ollama是本地服务，不需要API密钥
      isConfigured = true;
    } else if (
      activeProvider.value === "qianfan" &&
      currentConfig.secret_key &&
      currentConfig.api_key
    ) {
      // 百度千帆需要两个密钥
      isConfigured = true;
    } else if (
      activeProvider.value === "aws" &&
      currentConfig.access_key &&
      currentConfig.secret_key
    ) {
      // AWS需要两个密钥
      isConfigured = true;
    } else if (
      activeProvider.value === "azure" &&
      currentConfig.api_key &&
      currentConfig.endpoint &&
      currentConfig.deployment_name
    ) {
      // Azure需要API密钥、终端节点和部署名称
      isConfigured = true;
    } else if (currentConfig.api_key) {
      // 其他服务只需要API密钥
      isConfigured = true;
    }

    // 如果没有配置API密钥，提示用户
    if (!isConfigured && activeProvider.value !== "ollama") {
      const confirmSave = confirm(
        "您尚未配置API密钥或必要参数，该模型将无法使用。是否仍要保存？"
      );
      if (!confirmSave) {
        return;
      }
    }

    // 获取当前提供商的分类
    const provider = providers.value.find((p) => p.id === activeProvider.value);
    const category_id = provider ? provider.category : null;

    // 创建配置的深拷贝，避免修改原始对象
    const configToSave = JSON.parse(JSON.stringify(currentConfig));

    // 检查API密钥是否为星号，如果是则设置为空字符串，让后端保留原有值
    if (configToSave.api_key === "******") {
      console.log("API密钥为星号，将使用后端保存的原有值");
      configToSave.api_key = "";
    }

    if (configToSave.secret_key === "******") {
      console.log("Secret密钥为星号，将使用后端保存的原有值");
      configToSave.secret_key = "";
    }

    if (configToSave.access_key === "******") {
      console.log("Access Key为星号，将使用后端保存的原有值");
      configToSave.access_key = "";
    }

    const config = {
      provider: activeProvider.value,
      config: configToSave,
      category_id: category_id,
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
          model_url: provider.model_url,
          models: provider.models || [],
          sort: provider.sort || 0,
          is_configured: provider.is_configured,
        }));

        // 更新模型列表并初始化配置
        data.providers.forEach((provider) => {
          // 更新模型列表 - 确保即使未配置API密钥也加载模型列表
          if (provider.models && provider.models.length > 0) {
            providerModels.value[provider.id] = provider.models;
          } else {
            // 如果没有模型列表，初始化为空数组
            providerModels.value[provider.id] = [];
          }

          // 初始化配置（如果不存在）
          if (!providerConfigs.value[provider.id]) {
            // 创建默认配置
            const defaultConfig = {
              temperature: 0.7,
              max_tokens: 1000,
              model: "", // 初始化为空字符串
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
          } else if (
            !providerConfigs.value[provider.id].model &&
            provider.models &&
            provider.models.length > 0
          ) {
            // 如果配置已存在但没有模型，设置默认模型
            providerConfigs.value[provider.id].model = provider.models[0];
          }
        });

        console.log("成功加载提供商和模型列表");
      }
    }
  } catch (error) {
    console.error("加载提供商和模型列表失败:", error);
  }
}

// 加载分类
async function loadCategories() {
  try {
    const response = await fetch(`${props.apiBaseUrl}/api/llm/categories`);
    if (response.ok) {
      const data = await response.json();
      if (data.success && data.categories) {
        // 保留"全部"分类
        const allCategory = providerCategories.value.find(
          (c) => c.id === "all"
        );

        // 更新分类列表
        providerCategories.value = [
          allCategory, // 保持"全部"分类在第一位
          ...data.categories
            .map((c) => ({
              id: c.category_id,
              name: c.name,
              description: c.description,
            }))
            .filter((c) => c.id !== "all"),
        ];

        console.log("成功加载LLM分类");
      }
    }
  } catch (error) {
    console.error("加载LLM分类失败:", error);
  }
}

// 组件挂载时加载配置和提供商信息
onMounted(async () => {
  await loadCategories(); // 先加载分类信息
  await loadProviders(); // 再加载提供商信息
  await loadConfigs(); // 最后加载用户配置
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

.model-control {
  display: flex;
  align-items: center;
  gap: 10px;
}

.model-input-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex: 1;
  width: 100%;
}

.model-input-group select,
.model-input-group input {
  width: 100%;
}

.model-buttons {
  display: flex;
  gap: 5px;
}

.setting-notice {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  margin-top: 10px;
  margin-bottom: 15px;
  background-color: #f8f9fa;
  border-radius: 4px;
  border-left: 4px solid #17a2b8;
  color: #495057;
  font-size: 0.9rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.api-key-notice {
  margin-top: 0;
  margin-bottom: 20px;
  background-color: #fff8e1;
  border-left: 4px solid #ffc107;
}

.api-key-notice i {
  color: #ffc107;
}

.setting-notice i {
  color: #17a2b8;
  font-size: 1.1rem;
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

.btn-reload-models {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 4px;
  background-color: #f5f5f5;
  color: #333;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
  flex-shrink: 0;
}

.btn-reload-models:hover:not(:disabled) {
  background-color: #e0e0e0;
}

.btn-reload-models:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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
