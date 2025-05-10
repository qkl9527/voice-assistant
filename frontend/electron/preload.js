const { contextBridge, ipcRenderer } = require("electron");

// 在 window 对象上暴露 electron API
contextBridge.exposeInMainWorld("electronAPI", {
  getApiBaseUrl: () => ipcRenderer.invoke("get-api-base-url"),
  checkPythonService: () => ipcRenderer.invoke("check-python-service"),
  restartPythonService: () => ipcRenderer.invoke("restart-python-service"),
  toggleAlwaysOnTop: () => ipcRenderer.invoke("toggle-always-on-top"),
  getAlwaysOnTopState: () => ipcRenderer.invoke("get-always-on-top-state"),
  toggleDebugMode: () => ipcRenderer.invoke("toggle-debug-mode"),
  getDebugModeState: () => ipcRenderer.invoke("get-debug-mode-state"),
  setModelParams: (params) => ipcRenderer.invoke("set-model-params", params),
  getModelParams: () => ipcRenderer.invoke("get-model-params"),
  setDataStoragePath: (path) =>
    ipcRenderer.invoke("set-data-storage-path", path),
  platform: process.platform,

  // 浮动球模式 API
  toggleFloatingMode: () => ipcRenderer.invoke("toggle-floating-mode"),
  getFloatingModeState: () => ipcRenderer.invoke("get-floating-mode-state"),
  saveWindowState: () => ipcRenderer.invoke("save-window-state"),
  moveFloatingWindow: (dx, dy) =>
    ipcRenderer.invoke("move-floating-window", dx, dy),
  // 添加浮动球模式变化监听
  onFloatingModeChanged: (callback) => {
    ipcRenderer.on("floating-mode-changed", (_, isFloating) =>
      callback(isFloating)
    );
  },

  // 服务状态 API
  getServiceStatus: () => ipcRenderer.invoke("get-service-status"),

  // 本地存储API
  saveToStorage: (key, data) =>
    ipcRenderer.invoke("save-to-storage", key, data),
  loadFromStorage: (key) => ipcRenderer.invoke("load-from-storage", key),

  // 系统信息API
  getSystemInfo: () => ipcRenderer.invoke("get-system-info"),
  openExternal: (url) => ipcRenderer.invoke("open-external", url),
  getAppIconPath: () => ipcRenderer.invoke("get-app-icon-path"),
});

// 当 DOM 加载完成时执行
window.addEventListener("DOMContentLoaded", () => {
  const replaceText = (selector, text) => {
    const element = document.getElementById(selector);
    if (element) element.innerText = text;
  };

  for (const dependency of ["chrome", "node", "electron"]) {
    replaceText(`${dependency}-version`, process.versions[dependency]);
  }
});
