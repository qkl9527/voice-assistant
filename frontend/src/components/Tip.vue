<script setup>
import { ref, watch, onMounted, computed } from "vue";

const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: "提示",
  },
  message: {
    type: String,
    default: "",
  },
  type: {
    type: String,
    default: "info", // 'info', 'success', 'warning', 'error'
  },
  duration: {
    type: Number,
    default: 3000, // 自动关闭时间，0表示不自动关闭
  },
  showClose: {
    type: Boolean,
    default: true,
  },
  confirmText: {
    type: String,
    default: "确定",
  },
  showConfirm: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["update:show", "confirm", "close"]);

// 内部显示状态
const visible = ref(props.show);
const timer = ref(null);
const isClosing = ref(false);

// 监听外部show属性变化
watch(
  () => props.show,
  (newVal) => {
    if (newVal) {
      isClosing.value = false;
      visible.value = true;
      if (props.duration > 0) {
        startTimer();
      }
    } else {
      startClosing();
    }
  }
);

// 监听内部visible变化，同步到外部
watch(visible, (newVal) => {
  if (!newVal) {
    emit("update:show", false);
  }
});

// 关闭消息框
function closeTip() {
  startClosing();
  clearTimer();
  emit("close");
}

// 开始关闭动画
function startClosing() {
  isClosing.value = true;
  setTimeout(() => {
    visible.value = false;
    isClosing.value = false;
  }, 300); // 动画持续时间
}

// 确认按钮点击
function confirmAction() {
  emit("confirm");
  closeTip();
}

// 开始自动关闭计时器
function startTimer() {
  clearTimer();
  if (props.duration > 0) {
    timer.value = setTimeout(() => {
      closeTip();
    }, props.duration);
  }
}

// 清除计时器
function clearTimer() {
  if (timer.value) {
    clearTimeout(timer.value);
    timer.value = null;
  }
}

// 获取图标类名
function getIconClass() {
  switch (props.type) {
    case "success":
      return "fa-check-circle";
    case "warning":
      return "fa-exclamation-triangle";
    case "error":
      return "fa-times-circle";
    case "info":
    default:
      return "fa-info-circle";
  }
}

// 获取类型对应的颜色类
const typeClass = computed(() => `tip-${props.type}`);

// 组件挂载时，如果显示且设置了自动关闭，则启动计时器
onMounted(() => {
  if (props.show && props.duration > 0) {
    startTimer();
  }
});
</script>

<template>
  <div v-if="visible" class="tip-container">
    <div class="tip" :class="[typeClass, { 'tip-closing': isClosing }]">
      <div class="tip-content">
        <div class="tip-icon">
          <i class="fas" :class="getIconClass()"></i>
        </div>
        <div class="tip-text">
          <div v-if="title" class="tip-title">{{ title }}</div>
          <div class="tip-message">{{ message }}</div>
        </div>
        <button
          v-if="showClose"
          class="tip-close"
          @click="closeTip"
          aria-label="关闭"
        >
          <i class="fas fa-times"></i>
        </button>
      </div>
      <div v-if="showConfirm" class="tip-footer">
        <button class="tip-confirm" @click="confirmAction">
          {{ confirmText }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tip-container {
  position: fixed;
  top: 20px;
  left: 0;
  right: 0;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  pointer-events: none;
  z-index: 9999;
}

.tip {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1),
    0 5px 10px -5px rgba(0, 0, 0, 0.04);
  padding: 16px;
  margin-bottom: 8px;
  pointer-events: auto;
  max-width: 90%;
  min-width: 300px;
  display: inline-flex;
  flex-direction: column;
  transform: translateY(0) scale(1);
  opacity: 1;
  transition: transform 0.3s ease, opacity 0.3s ease;
  overflow: hidden;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.tip-closing {
  transform: translateY(-20px) scale(0.95);
  opacity: 0;
}

.tip-content {
  display: flex;
  align-items: flex-start;
  width: 100%;
}

.tip-icon {
  margin-right: 12px;
  font-size: 18px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tip-text {
  flex: 1;
  font-size: 13px;
  line-height: 1.6;
  color: rgba(0, 0, 0, 0.85);
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.tip-title {
  font-weight: 600;
  margin-bottom: 4px;
  font-size: 14px;
  color: rgba(0, 0, 0, 0.85);
}

.tip-message {
  color: rgba(0, 0, 0, 0.65);
}

.tip-close {
  background: none;
  border: none;
  font-size: 12px;
  cursor: pointer;
  color: rgba(0, 0, 0, 0.45);
  margin-left: 12px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  transition: all 0.2s;
}

.tip-close:hover {
  background-color: rgba(0, 0, 0, 0.05);
  color: rgba(0, 0, 0, 0.75);
}

.tip-footer {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}

.tip-confirm {
  padding: 5px 14px;
  border-radius: 6px;
  border: none;
  background-color: #1890ff;
  color: white;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
  font-weight: 500;
  box-shadow: 0 2px 5px rgba(24, 144, 255, 0.2);
}

.tip-confirm:hover {
  background-color: #40a9ff;
  box-shadow: 0 4px 8px rgba(24, 144, 255, 0.3);
}

/* 类型样式 */
.tip-info {
  border-left: 4px solid #1890ff;
}
.tip-info .tip-icon {
  color: #1890ff;
}

.tip-success {
  border-left: 4px solid #52c41a;
}
.tip-success .tip-icon {
  color: #52c41a;
}

.tip-warning {
  border-left: 4px solid #faad14;
}
.tip-warning .tip-icon {
  color: #faad14;
}

.tip-error {
  border-left: 4px solid #f5222d;
}
.tip-error .tip-icon {
  color: #f5222d;
}
</style>
