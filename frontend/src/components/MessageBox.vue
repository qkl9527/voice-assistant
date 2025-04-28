<script setup>
import { ref, watch, onMounted } from "vue";

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
    default: true,
  },
});

const emit = defineEmits(["update:show", "confirm", "close"]);

// 内部显示状态
const visible = ref(props.show);
const timer = ref(null);

// 监听外部show属性变化
watch(
  () => props.show,
  (newVal) => {
    visible.value = newVal;
    if (newVal && props.duration > 0) {
      startTimer();
    }
  }
);

// 监听内部visible变化，同步到外部
watch(visible, (newVal) => {
  emit("update:show", newVal);
});

// 关闭消息框
function closeMessageBox() {
  visible.value = false;
  clearTimer();
  emit("close");
}

// 确认按钮点击
function confirmAction() {
  emit("confirm");
  closeMessageBox();
}

// 开始自动关闭计时器
function startTimer() {
  clearTimer();
  if (props.duration > 0) {
    timer.value = setTimeout(() => {
      closeMessageBox();
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
function getTypeClass() {
  return `message-${props.type}`;
}

// 组件挂载时，如果显示且设置了自动关闭，则启动计时器
onMounted(() => {
  if (props.show && props.duration > 0) {
    startTimer();
  }
});
</script>

<template>
  <transition name="message-fade">
    <div v-if="visible" class="message-container">
      <div class="message" :class="getTypeClass()">
        <div class="message-content">
          <i class="fas" :class="getIconClass()"></i>
          <span class="message-text">
            <span v-if="title" class="message-title">{{ title }}</span>
            {{ message }}
          </span>
          <button
            v-if="showClose"
            class="message-close"
            @click="closeMessageBox"
          >
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div v-if="showConfirm" class="message-footer">
          <button class="message-confirm" @click="confirmAction">
            {{ confirmText }}
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<style scoped>
.message-container {
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

.message {
  background-color: #fff;
  border-radius: 2px;
  box-shadow: 0 3px 6px -4px rgba(0, 0, 0, 0.12),
    0 6px 16px 0 rgba(0, 0, 0, 0.08), 0 9px 28px 8px rgba(0, 0, 0, 0.05);
  padding: 10px 16px;
  margin-bottom: 8px;
  pointer-events: auto;
  max-width: 80%;
  min-width: 150px;
  display: inline-flex;
  flex-direction: column;
  border-left: 4px solid transparent;
}

.message-info {
  border-left-color: #1890ff;
}

.message-success {
  border-left-color: #52c41a;
}

.message-warning {
  border-left-color: #faad14;
}

.message-error {
  border-left-color: #f5222d;
}

.message-content {
  display: flex;
  align-items: flex-start;
  width: 100%;
}

.message-content i {
  margin-right: 8px;
  font-size: 16px;
  margin-top: 2px;
  flex-shrink: 0;
}

.message-text {
  flex: 1;
  font-size: 14px;
  line-height: 1.5715;
  color: rgba(0, 0, 0, 0.85);
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.message-title {
  display: block;
  margin-bottom: 4px;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.85);
}

.message-close {
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
  width: 20px;
  height: 20px;
}

.message-close:hover {
  color: rgba(0, 0, 0, 0.75);
}

.message-footer {
  margin-top: 8px;
  display: flex;
  justify-content: flex-end;
}

.message-confirm {
  padding: 4px 15px;
  border-radius: 2px;
  border: 1px solid transparent;
  background-color: #1890ff;
  color: white;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
  height: 32px;
  line-height: 1.5;
}

.message-confirm:hover {
  background-color: #40a9ff;
}

/* 类型样式 */
.message-info i {
  color: #1890ff;
}

.message-success i {
  color: #52c41a;
}

.message-warning i {
  color: #faad14;
}

.message-error i {
  color: #f5222d;
}

/* 动画效果 */
.message-fade-enter-active {
  animation: messageIn 0.3s ease-out;
}

.message-fade-leave-active {
  animation: messageOut 0.3s ease-in;
}

@keyframes messageIn {
  0% {
    opacity: 0;
    transform: translateY(-16px);
    margin-top: -16px;
  }
  100% {
    opacity: 1;
    transform: translateY(0);
    margin-top: 0;
  }
}

@keyframes messageOut {
  0% {
    opacity: 1;
    transform: translateY(0);
    margin-top: 0;
    max-height: 150px;
  }
  100% {
    opacity: 0;
    transform: translateY(-16px);
    margin-top: -16px;
    max-height: 0;
    padding: 0;
  }
}
</style>
