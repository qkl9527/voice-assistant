<template>
  <div class="help-feedback-container">
    <div class="about-section">
      <div v-if="appIconPath" class="app-logo">
        <img :src="appIconPath" alt="VoiceAssistant Logo" />
      </div>
      <h2>VoiceAssistant</h2>
      <div class="version-info">
        <p class="version">版本 {{ systemInfo.appVersion || "0.0.0" }}</p>
        <p class="copyright">© 2025 All Rights Reserved</p>
      </div>

      <div class="description">
        <p>
          VoiceAssistant是一款功能强大的语音识别和文本处理工具，支持多种语音识别模型和大语言模型，为您提供高效的语音转文字和文本处理体验。
        </p>
      </div>
    </div>

    <div class="features-section">
      <h3>主要功能</h3>
      <ul>
        <li>
          <i class="fas fa-microphone"></i>
          <div>
            <h4>语音识别</h4>
            <p>支持实时流式和一次性两种识别模式，可选择多种语音识别模型</p>
          </div>
        </li>
        <li>
          <i class="fas fa-magic"></i>
          <div>
            <h4>AI文本处理</h4>
            <p>支持错别字修正、文本润色、内容概述和中英文翻译等功能</p>
          </div>
        </li>
        <li>
          <i class="fas fa-robot"></i>
          <div>
            <h4>多平台大语言模型</h4>
            <p>支持OpenAI、Anthropic、百度千帆、智谱AI等多个大语言模型平台</p>
          </div>
        </li>
        <li>
          <i class="fas fa-history"></i>
          <div>
            <h4>历史记录</h4>
            <p>自动保存识别历史，方便查询和重用</p>
          </div>
        </li>
      </ul>
    </div>

    <div class="feedback-section">
      <h3>反馈与支持</h3>
      <p>
        如果您在使用过程中遇到任何问题，或有任何建议和反馈，请通过以下方式联系我们：
      </p>

      <div class="contact-methods">
        <!-- <div class="contact-item">
          <i class="fas fa-envelope"></i>
          <span>电子邮件：</span>
        </div> -->
        <div class="contact-item">
          <i class="fab fa-github"></i>
          <span
            >GitHub：<a href="#" @click.prevent="openGitHub"
              >https://github.com/qkl9527/voice-assistant</a
            ></span
          >
        </div>
        <div class="contact-item">
          <i class="fas fa-comment-dots"></i>
          <span
            >反馈和建议：<a href="#" @click.prevent="openIssues"
              >https://github.com/qkl9527/voice-assistant/issues</a
            ></span
          >
        </div>
      </div>
    </div>

    <div class="system-info-section">
      <h3>系统信息</h3>
      <div class="system-info-grid">
        <div class="info-item">
          <span class="info-label">操作系统：</span>
          <span class="info-value">{{ systemInfo.os }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">应用版本：</span>
          <span class="info-value">{{ systemInfo.appVersion || "0.0.0" }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">Electron版本：</span>
          <span class="info-value">{{ systemInfo.electron }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">Chrome版本：</span>
          <span class="info-value">{{ systemInfo.chrome }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">Node.js版本：</span>
          <span class="info-value">{{ systemInfo.node }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">V8版本：</span>
          <span class="info-value">{{ systemInfo.v8 }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";

// 系统信息
const systemInfo = ref({
  os: "获取中...",
  electron: "获取中...",
  chrome: "获取中...",
  node: "获取中...",
  v8: "获取中...",
  appVersion: "获取中...",
});

// 应用图标路径
const appIconPath = ref("");

// 打开GitHub页面
function openGitHub() {
  if (window.electronAPI) {
    window.electronAPI.openExternal(
      "https://github.com/qkl9527/voice-assistant"
    );
  } else {
    window.open("https://github.com/qkl9527/voice-assistant", "_blank");
  }
}

// 打开Issues页面
function openIssues() {
  if (window.electronAPI) {
    window.electronAPI.openExternal(
      "https://github.com/qkl9527/voice-assistant/issues"
    );
  } else {
    window.open("https://github.com/qkl9527/voice-assistant/issues", "_blank");
  }
}

// 获取系统信息
async function getSystemInfo() {
  if (window.electronAPI) {
    try {
      const info = await window.electronAPI.getSystemInfo();
      systemInfo.value = info;
    } catch (error) {
      console.error("获取系统信息失败:", error);
    }
  } else {
    // 浏览器环境下的模拟数据
    systemInfo.value = {
      os: navigator.userAgent.includes("Win")
        ? "Windows"
        : navigator.userAgent.includes("Mac")
        ? "macOS"
        : navigator.userAgent.includes("Linux")
        ? "Linux"
        : "Unknown OS",
      electron: "N/A (浏览器环境)",
      chrome: navigator.userAgent.match(/Chrome\/([0-9.]+)/)?.[1] || "N/A",
      node: "N/A (浏览器环境)",
      v8: "N/A (浏览器环境)",
      appVersion: "N/A (浏览器环境)",
    };
  }
}

// 获取应用图标路径
async function getAppIconPath() {
  if (window.electronAPI) {
    try {
      const iconPath = await window.electronAPI.getAppIconPath();
      if (iconPath) {
        // 将文件路径转换为URL
        // appIconPath.value = `file://${iconPath}`;
        appIconPath.value = iconPath;
        console.log("应用图标路径:", appIconPath.value);
      }
    } catch (error) {
      console.error("获取应用图标路径失败:", error);
    }
  }
}

onMounted(async () => {
  await getSystemInfo();
  await getAppIconPath();
});
</script>

<style scoped>
.help-feedback-container {
  padding: 30px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  max-width: 800px;
  margin: 0 auto;
}

.about-section {
  text-align: center;
  margin-bottom: 40px;
  padding-bottom: 30px;
  border-bottom: 1px solid #eee;
}

.app-logo {
  margin-bottom: 15px;
}

.app-logo img {
  width: 200px;
  height: 200px;
  border-radius: 10px;
}

.about-section h2 {
  font-size: 24px;
  margin: 10px 0;
  color: #333;
}

.version-info {
  margin: 10px 0 20px;
  color: #666;
}

.version {
  font-size: 14px;
  margin: 5px 0;
}

.copyright {
  font-size: 12px;
  margin: 5px 0;
}

.description {
  max-width: 600px;
  margin: 0 auto;
  line-height: 1.6;
  color: #555;
}

.features-section,
.feedback-section,
.system-info-section {
  margin-bottom: 40px;
  padding-bottom: 30px;
  border-bottom: 1px solid #eee;
}

.features-section h3,
.feedback-section h3,
.system-info-section h3 {
  font-size: 18px;
  margin-bottom: 20px;
  color: #333;
  position: relative;
  padding-bottom: 10px;
}

.features-section h3:after,
.feedback-section h3:after,
.system-info-section h3:after {
  content: "";
  position: absolute;
  bottom: 0;
  left: 0;
  width: 50px;
  height: 2px;
  background-color: #4a6cf7;
}

.features-section ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.features-section li {
  display: flex;
  align-items: flex-start;
  margin-bottom: 20px;
}

.features-section li i {
  font-size: 18px;
  color: #4a6cf7;
  margin-right: 15px;
  margin-top: 3px;
}

.features-section li h4 {
  font-size: 16px;
  margin: 0 0 5px;
  color: #333;
}

.features-section li p {
  margin: 0;
  color: #666;
  line-height: 1.5;
}

.contact-methods {
  margin-top: 20px;
}

.contact-item {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.contact-item i {
  font-size: 16px;
  color: #4a6cf7;
  margin-right: 10px;
}

.contact-item a {
  color: #4a6cf7;
  text-decoration: none;
}

.contact-item a:hover {
  text-decoration: underline;
}

.system-info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 15px;
}

.info-item {
  display: flex;
  align-items: center;
}

.info-label {
  font-weight: 500;
  color: #555;
  margin-right: 5px;
}

.info-value {
  color: #666;
}

@media (max-width: 768px) {
  .help-feedback-container {
    padding: 20px;
  }

  .system-info-grid {
    grid-template-columns: 1fr;
  }
}
</style>
