<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from "vue";

const props = defineProps({
  analyser: Object,
  isRecording: Boolean,
  visualizerType: {
    type: String,
    default: "circular", // 默认为圆形波形
  },
});

const canvasRef = ref(null);
const animationFrameId = ref(null);
const dataArray = ref(null);
const bufferLength = ref(0);
const canvasCtx = ref(null);

// 初始化可视化器
function initVisualizer() {
  if (!props.analyser || !canvasRef.value) return;

  // 设置分析器参数
  props.analyser.fftSize = 256;
  bufferLength.value = props.analyser.frequencyBinCount;
  dataArray.value = new Uint8Array(bufferLength.value);

  // 获取画布上下文
  canvasCtx.value = canvasRef.value.getContext("2d");

  // 设置画布尺寸
  resizeCanvas();

  // 开始绘制
  if (props.isRecording) {
    startDrawing();
  }
}

// 调整画布大小
function resizeCanvas() {
  if (!canvasRef.value || !canvasCtx.value) return;

  const canvas = canvasRef.value;
  const container = canvas.parentElement;

  canvas.width = container.clientWidth;
  canvas.height = container.clientHeight;
}

// 绘制圆形波形
function drawCircularVisualizer(canvas, dataArray) {
  const centerX = canvas.width / 2;
  const centerY = canvas.height / 2;
  const radius = Math.min(centerX, centerY) - 5;
  const barWidth = (Math.PI * 2) / bufferLength.value;

  // 绘制中心点
  canvasCtx.value.beginPath();
  canvasCtx.value.arc(centerX, centerY, 2, 0, Math.PI * 2);
  canvasCtx.value.fillStyle = "#1890ff";
  canvasCtx.value.fill();

  // 绘制波形线
  for (let i = 0; i < bufferLength.value; i++) {
    // 计算高度，根据音量调整
    const amplitude = dataArray[i] / 255.0;
    const barHeight = radius * amplitude * 0.5 + radius * 0.5;

    // 计算角度
    const angle = i * barWidth;

    // 计算终点坐标
    const x = centerX + Math.cos(angle) * barHeight;
    const y = centerY + Math.sin(angle) * barHeight;

    // 设置颜色，根据音量变化
    const intensity = amplitude;
    const r = 24 + Math.round(intensity * 100);
    const g = 144 + Math.round(intensity * 111);
    const b = 255;

    // 绘制线条
    canvasCtx.value.beginPath();
    canvasCtx.value.moveTo(centerX, centerY);
    canvasCtx.value.lineTo(x, y);
    canvasCtx.value.strokeStyle = `rgb(${r}, ${g}, ${b})`;
    canvasCtx.value.lineWidth = 2;
    canvasCtx.value.stroke();

    // 绘制终点圆点
    canvasCtx.value.beginPath();
    canvasCtx.value.arc(x, y, 2, 0, Math.PI * 2);
    canvasCtx.value.fillStyle = `rgb(${r}, ${g}, ${b})`;
    canvasCtx.value.fill();
  }
}

// 绘制类似微信的波形效果
function drawWechatVisualizer(canvas, dataArray) {
  const width = canvas.width;
  const height = canvas.height;
  const barWidth = (width / bufferLength.value) * 2.5;
  const barSpacing = 2;
  const barCount = Math.floor(width / (barWidth + barSpacing));
  const barStep = Math.floor(bufferLength.value / barCount) || 1;

  // 绘制波形
  canvasCtx.value.fillStyle = "#1890ff";

  for (let i = 0; i < barCount; i++) {
    const dataIndex = i * barStep;
    if (dataIndex < bufferLength.value) {
      const amplitude = dataArray[dataIndex] / 255.0;
      const barHeight = Math.max(3, height * amplitude * 0.7);

      // 计算x坐标，使波形居中
      const x =
        (width - (barCount * (barWidth + barSpacing) - barSpacing)) / 2 +
        i * (barWidth + barSpacing);
      const y = (height - barHeight) / 2;

      // 绘制圆角矩形
      const radius = Math.min(barWidth / 2, barHeight / 2, 4);
      canvasCtx.value.beginPath();
      canvasCtx.value.moveTo(x + radius, y);
      canvasCtx.value.lineTo(x + barWidth - radius, y);
      canvasCtx.value.quadraticCurveTo(
        x + barWidth,
        y,
        x + barWidth,
        y + radius
      );
      canvasCtx.value.lineTo(x + barWidth, y + barHeight - radius);
      canvasCtx.value.quadraticCurveTo(
        x + barWidth,
        y + barHeight,
        x + barWidth - radius,
        y + barHeight
      );
      canvasCtx.value.lineTo(x + radius, y + barHeight);
      canvasCtx.value.quadraticCurveTo(
        x,
        y + barHeight,
        x,
        y + barHeight - radius
      );
      canvasCtx.value.lineTo(x, y + radius);
      canvasCtx.value.quadraticCurveTo(x, y, x + radius, y);
      canvasCtx.value.fill();
    }
  }
}

// 绘制柱状波形
function drawBarVisualizer(canvas, dataArray) {
  const width = canvas.width;
  const height = canvas.height;
  const barWidth = (width / bufferLength.value) * 2.5;
  const barSpacing = 2;
  const barCount = Math.floor(width / (barWidth + barSpacing));
  const barStep = Math.floor(bufferLength.value / barCount) || 1;

  for (let i = 0; i < barCount; i++) {
    const dataIndex = i * barStep;
    if (dataIndex < bufferLength.value) {
      const amplitude = dataArray[dataIndex] / 255.0;
      const barHeight = Math.max(4, height * amplitude * 0.8);

      // 计算x坐标，使波形居中
      const x =
        (width - (barCount * (barWidth + barSpacing) - barSpacing)) / 2 +
        i * (barWidth + barSpacing);

      // 设置颜色，根据音量变化
      const intensity = amplitude;
      const r = 24 + Math.round(intensity * 100);
      const g = 144 + Math.round(intensity * 111);
      const b = 255;
      canvasCtx.value.fillStyle = `rgb(${r}, ${g}, ${b})`;

      // 从底部向上绘制柱状图
      canvasCtx.value.fillRect(x, height - barHeight, barWidth, barHeight);
    }
  }
}

// 开始绘制
function startDrawing() {
  if (!props.analyser || !canvasCtx.value) return;

  // 停止之前的动画
  if (animationFrameId.value) {
    cancelAnimationFrame(animationFrameId.value);
  }

  // 绘制函数
  function draw() {
    // 请求下一帧
    animationFrameId.value = requestAnimationFrame(draw);

    // 获取频率数据
    props.analyser.getByteFrequencyData(dataArray.value);

    // 清空画布
    const canvas = canvasRef.value;
    canvasCtx.value.clearRect(0, 0, canvas.width, canvas.height);

    // 根据选择的可视化类型绘制不同效果
    switch (props.visualizerType) {
      case "wechat":
        drawWechatVisualizer(canvas, dataArray.value);
        break;
      case "bars":
        drawBarVisualizer(canvas, dataArray.value);
        break;
      case "circular":
      default:
        drawCircularVisualizer(canvas, dataArray.value);
        break;
    }
  }

  // 开始动画
  draw();
}

// 停止绘制
function stopDrawing() {
  if (animationFrameId.value) {
    cancelAnimationFrame(animationFrameId.value);
    animationFrameId.value = null;

    // 清空画布
    if (canvasRef.value && canvasCtx.value) {
      canvasCtx.value.clearRect(
        0,
        0,
        canvasRef.value.width,
        canvasRef.value.height
      );
    }
  }
}

// 监听录音状态变化
watch(
  () => props.isRecording,
  (newValue) => {
    if (newValue) {
      startDrawing();
    } else {
      stopDrawing();
    }
  }
);

// 监听分析器变化
watch(
  () => props.analyser,
  () => {
    if (props.analyser) {
      initVisualizer();
    }
  }
);

// 监听可视化类型变化
watch(
  () => props.visualizerType,
  (newType) => {
    console.log("声纹效果类型变化为:", newType);
    if (props.analyser) {
      // 如果正在录音，重新开始绘制
      if (props.isRecording) {
        startDrawing();
      } else {
        // 如果没有录音，绘制一个静态的演示效果
        drawStaticDemo();
      }
    }
  }
);

// 绘制静态演示效果
function drawStaticDemo() {
  if (!canvasRef.value || !canvasCtx.value) return;

  // 清空画布
  const canvas = canvasRef.value;
  canvasCtx.value.clearRect(0, 0, canvas.width, canvas.height);

  // 创建模拟数据
  const demoDataArray = new Uint8Array(128);
  for (let i = 0; i < demoDataArray.length; i++) {
    // 创建一个波浪形状的数据模式
    demoDataArray[i] = 30 + Math.sin(i * 0.1) * 20 + Math.random() * 15;
  }

  // 根据选择的可视化类型绘制不同效果
  switch (props.visualizerType) {
    case "wechat":
      drawWechatVisualizer(canvas, demoDataArray);
      break;
    case "bars":
      drawBarVisualizer(canvas, demoDataArray);
      break;
    case "circular":
    default:
      drawCircularVisualizer(canvas, demoDataArray);
      break;
  }
}

// 组件挂载时初始化
onMounted(() => {
  window.addEventListener("resize", resizeCanvas);

  if (props.analyser) {
    initVisualizer();
  } else {
    // 如果没有分析器，也显示一个静态演示
    nextTick(() => {
      if (canvasRef.value) {
        canvasCtx.value = canvasRef.value.getContext("2d");
        resizeCanvas();
        drawStaticDemo();
      }
    });
  }
});

// 组件卸载时清理
onUnmounted(() => {
  window.removeEventListener("resize", resizeCanvas);
  stopDrawing();
});
</script>

<template>
  <div class="audio-visualizer">
    <canvas ref="canvasRef" class="visualizer-canvas"></canvas>
  </div>
</template>

<style scoped>
.audio-visualizer {
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
  border-radius: 8px;
}

.visualizer-canvas {
  width: 100%;
  height: 100%;
  display: block;
}
</style>
