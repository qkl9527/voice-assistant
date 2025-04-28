const { app, BrowserWindow, ipcMain, dialog, Menu, Tray } = require("electron");
const path = require("path");
const fs = require("fs");
const PythonService = require("./python-service");

// 设置开发环境变量
process.env.NODE_ENV = "development";

// 全局变量
let mainWindow = null;
let pythonService = null;
let apiBaseUrl = null;
let isAlwaysOnTop = false; // 窗口置顶状态
let servicePort = 6100; // 默认端口
let isDebugMode = true; // Debug模式状态
let isFloatingMode = false; // 浮动球模式状态
let windowPosition = { x: 0, y: 0 }; // 保存窗口位置
let windowSize = { width: 900, height: 670 }; // 保存窗口大小
let dataStoragePath = ""; // 数据存储目录

// 存储路径
const userDataPath = app.getPath("userData");
const storageDir = path.join(userDataPath, "storage");
console.log("storageDir:", storageDir);

// 创建存储目录
if (!fs.existsSync(storageDir)) {
  fs.mkdirSync(storageDir, { recursive: true });
}

// 模型参数
let modelParams = {
  model: "paraformer-zh", // paraformer-zh-streaming
  vadModel: "fsmn-vad", // fsmn-vad
  puncModel: "", // ct-punc
  spkModel: "", // cam++
  disableUpdate: true,
};

// 控制应用生命周期和创建原生浏览器窗口的模块
function createWindow() {
  // 根据浮动球模式设置决定创建什么类型的窗口
  if (isFloatingMode) {
    // 创建浮动球模式窗口（无标题栏）
    mainWindow = new BrowserWindow({
      width: 200,
      height: 200,
      webPreferences: {
        preload: path.join(__dirname, "preload.js"),
        nodeIntegration: false,
        contextIsolation: true,
        enableRemoteModule: false,
        sandbox: true,
        devTools: isDebugMode,
      },
      frame: false, // 隐藏标题栏
      resizable: false,
      transparent: true, // 透明背景，使圆形效果更好
      skipTaskbar: false, // 仍然显示在任务栏
    });

    // 移动到屏幕右上角
    const { width: screenWidth } =
      require("electron").screen.getPrimaryDisplay().workAreaSize;
    mainWindow.setPosition(screenWidth - 220, 100);
  } else {
    // 创建正常模式窗口（有标题栏）
    mainWindow = new BrowserWindow({
      width: windowSize.width,
      height: windowSize.height,
      webPreferences: {
        preload: path.join(__dirname, "preload.js"),
        nodeIntegration: false,
        contextIsolation: true,
        enableRemoteModule: false,
        sandbox: true,
        devTools: isDebugMode,
      },
      frame: true, // 显示标题栏
      resizable: true, // 允许调整大小
    });
  }

  // 加载 index.html
  console.log(
    "process.env.VITE_DEV_SERVER_URL:",
    process.env.VITE_DEV_SERVER_URL
  );
  console.log("env:", process.env.NODE_ENV);
  if (process.env.VITE_DEV_SERVER_URL) {
    mainWindow.loadURL(process.env.VITE_DEV_SERVER_URL);
    // 开发环境下始终打开开发工具
    mainWindow.webContents.openDevTools();
  } else {
    // 生产环境下加载 index.html
    mainWindow.loadFile(path.join(__dirname, "../dist/index.html"));

    // 在生产环境中，根据Debug模式设置决定是否打开开发工具
    if (isDebugMode) {
      mainWindow.webContents.openDevTools();
    }
  }

  // 设置置顶状态
  if (isAlwaysOnTop) {
    mainWindow.setAlwaysOnTop(true);
  }

  // 窗口关闭时的处理
  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

// 启动 Python 后端服务
async function startPythonService() {
  try {
    // 创建 Python 服务实例，使用配置的端口
    pythonService = new PythonService(servicePort);

    // 设置模型参数
    pythonService.setModelParams(modelParams);
    console.log("启动服务时使用的模型参数:", modelParams);

    // 设置数据存储目录
    if (dataStoragePath) {
      pythonService.setDataStoragePath(dataStoragePath);
      console.log("启动服务时使用的数据存储目录:", dataStoragePath);
    }

    const port = await pythonService.start();
    apiBaseUrl = pythonService.getUrl();
    console.log(`Python 服务已启动，URL: ${apiBaseUrl}`);
    return apiBaseUrl;
  } catch (error) {
    console.error("启动 Python 服务失败:", error);
    dialog.showErrorBox(
      "Python 服务启动失败",
      `无法启动语音识别服务: ${error.message}`
    );
    return null;
  }
}

// 加载设置
async function loadSettings() {
  try {
    const filePath = path.join(storageDir, `settings.json`);
    if (fs.existsSync(filePath)) {
      const data = fs.readFileSync(filePath, "utf8");
      const settings = JSON.parse(data);

      // 设置端口
      if (settings.port && Number.isInteger(settings.port)) {
        servicePort = settings.port;
        console.log(`从设置中加载端口: ${servicePort}`);
      }

      // 设置Debug模式
      if (settings.debugMode !== undefined) {
        isDebugMode = settings.debugMode;
        console.log(`从设置中加载Debug模式: ${isDebugMode}`);
      }

      // 加载浮动球模式状态
      if (settings.floatingMode !== undefined) {
        isFloatingMode = settings.floatingMode;
        console.log(`从设置中加载浮动球模式: ${isFloatingMode}`);
      }

      // 加载窗口位置和大小
      if (settings.windowPosition) {
        windowPosition = settings.windowPosition;
      }

      if (settings.windowSize) {
        windowSize = settings.windowSize;
      }

      // 加载数据存储目录
      if (settings.dataStoragePath) {
        dataStoragePath = settings.dataStoragePath;
        console.log(`从设置中加载数据存储目录: ${dataStoragePath}`);
      }

      // 加载模型参数
      if (settings.modelParams) {
        modelParams = {
          model: settings.modelParams.model || modelParams.model,
          vadModel: settings.modelParams.vadModel || modelParams.vadModel,
          puncModel: settings.modelParams.puncModel || modelParams.puncModel,
          spkModel: settings.modelParams.spkModel || modelParams.spkModel,
          disableUpdate:
            settings.modelParams.disableUpdate !== undefined
              ? settings.modelParams.disableUpdate
              : modelParams.disableUpdate,
        };
        console.log(`从设置中加载模型参数:`, modelParams);
      }

      return settings;
    }
    return null;
  } catch (error) {
    console.error(`加载设置失败:`, error);
    return null;
  }
}

// 检查是否需要后置启动后端服务
async function shouldLazyLoadBackend() {
  try {
    // 从已加载的设置中获取后置启动设置
    const filePath = path.join(storageDir, `settings.json`);
    if (fs.existsSync(filePath)) {
      const data = fs.readFileSync(filePath, "utf8");
      const settings = JSON.parse(data);
      return settings && settings.lazyLoadBackend === true;
    }
    return true;
  } catch (error) {
    console.error(`检查后置启动设置失败:`, error);
    return true;
  }
}

// 这段程序将会在 Electron 结束初始化
// 和创建浏览器窗口的时候调用
// 部分 API 在 ready 事件触发后才能使用
app.whenReady().then(async () => {
  // 加载设置，包括模型参数
  await loadSettings();

  // 检查是否需要后置启动
  const lazyLoad = await shouldLazyLoadBackend();

  if (!lazyLoad) {
    // 如果不是后置启动，则立即启动服务
    console.log("正常启动 Python 服务...");
    await startPythonService();
    console.log("Python 服务已启动");
  } else {
    console.log("后置启动模式，暂不启动 Python 服务");
  }

  // 创建窗口
  createWindow();

  app.on("activate", function () {
    // 在 macOS 上，当点击 dock 图标并且没有其他窗口打开时，
    // 通常在应用程序中重新创建一个窗口
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

// 除了 macOS 外，当所有窗口都被关闭的时候退出程序
app.on("window-all-closed", function () {
  if (process.platform !== "darwin") app.quit();
});

// 应用退出前停止 Python 服务
app.on("will-quit", async (event) => {
  if (pythonService.isServiceRunning()) {
    event.preventDefault();
    await pythonService.stop();
    app.quit();
  }
});

// IPC 通信处理

// 获取 API 基础 URL
ipcMain.handle("get-api-base-url", async () => {
  console.log("调用 get-api-base-url，当前 apiBaseUrl:", apiBaseUrl);
  if (!apiBaseUrl) {
    await startPythonService();
  }
  return apiBaseUrl;
});

// 检查 Python 服务状态
ipcMain.handle("check-python-service", async () => {
  return {
    running: pythonService.isServiceRunning(),
    url: apiBaseUrl,
  };
});

// 获取服务状态
ipcMain.handle("get-service-status", () => {
  // 返回当前服务状态
  return {
    apiBaseUrl: apiBaseUrl,
    isServiceRunning: pythonService ? pythonService.isServiceRunning() : false,
  };
});

// 重启 Python 服务
ipcMain.handle("restart-python-service", async () => {
  if (pythonService && pythonService.isServiceRunning()) {
    await pythonService.stop();
  }
  return await startPythonService();
});

// 切换窗口置顶状态
ipcMain.handle("toggle-always-on-top", () => {
  if (mainWindow) {
    isAlwaysOnTop = !isAlwaysOnTop;
    mainWindow.setAlwaysOnTop(isAlwaysOnTop);
    return isAlwaysOnTop;
  }
  return false;
});

// 获取窗口置顶状态
ipcMain.handle("get-always-on-top-state", () => {
  return isAlwaysOnTop;
});

// 切换Debug模式状态
ipcMain.handle("toggle-debug-mode", () => {
  isDebugMode = !isDebugMode;

  // 根据Debug模式状态打开或关闭开发工具
  if (mainWindow) {
    if (isDebugMode) {
      mainWindow.webContents.openDevTools();
    } else {
      mainWindow.webContents.closeDevTools();
    }
  }

  return isDebugMode;
});

// 获取Debug模式状态
ipcMain.handle("get-debug-mode-state", () => {
  return isDebugMode;
});

// 切换浮动球模式
ipcMain.handle("toggle-floating-mode", () => {
  if (mainWindow) {
    isFloatingMode = !isFloatingMode;

    // 保存当前窗口状态，以便在模式切换时使用
    if (!isFloatingMode) {
      // 从浮动球模式切换到正常模式
      console.log("切换到正常模式");

      // 恢复到正常大小和标题栏
      mainWindow.setResizable(true);

      // 设置窗口属性（有标题栏）
      mainWindow.frame = true; // 隐藏标题栏

      // 恢复窗口大小和位置
      if (windowPosition.x !== 0 && windowPosition.y !== 0) {
        mainWindow.setBounds({
          width: windowSize.width,
          height: windowSize.height,
          x: windowPosition.x,
          y: windowPosition.y,
        });
      } else {
        mainWindow.setSize(windowSize.width, windowSize.height);
      }

      // 设置透明度为不透明
      mainWindow.setOpacity(1.0);

      // 通知渲染进程模式已切换
      mainWindow.webContents.send("floating-mode-changed", isFloatingMode);
    } else {
      // 从正常模式切换到浮动球模式
      console.log("切换到浮动球模式");

      // 保存当前窗口大小和位置，以便恢复时使用
      const [width, height] = mainWindow.getSize();
      windowSize = { width, height };

      const [x, y] = mainWindow.getPosition();
      windowPosition = { x, y };

      // 设置窗口属性（无标题栏）
      mainWindow.setResizable(false);
      mainWindow.frame = false; // 隐藏标题栏

      // 设置透明背景
      mainWindow.setBackgroundColor("#00000000");
      mainWindow.setOpacity(0.95);

      // 调整大小为浮动球大小
      mainWindow.setSize(200, 220);

      // 移动到屏幕右上角
      const { width: screenWidth } =
        require("electron").screen.getPrimaryDisplay().workAreaSize;
      mainWindow.setPosition(screenWidth - 220, 100);

      // 通知渲染进程模式已切换
      mainWindow.webContents.send("floating-mode-changed", isFloatingMode);
    }

    return isFloatingMode;
  }
  return false;
});

// 获取浮动球模式状态
ipcMain.handle("get-floating-mode-state", () => {
  return isFloatingMode;
});

// 保存窗口位置和大小
ipcMain.handle("save-window-state", () => {
  if (mainWindow) {
    const [width, height] = mainWindow.getSize();
    const [x, y] = mainWindow.getPosition();

    windowSize = { width, height };
    windowPosition = { x, y };

    return { windowSize, windowPosition };
  }
  return null;
});

// 移动浮动球窗口
ipcMain.handle("move-floating-window", (event, dx, dy) => {
  if (mainWindow && isFloatingMode) {
    const [x, y] = mainWindow.getPosition();
    mainWindow.setPosition(x + dx, y + dy);
    return true;
  }
  return false;
});

// 设置模型参数
ipcMain.handle("set-model-params", async (event, params) => {
  // console.log("set-model-params:", modelParams, params);
  modelParams = { ...modelParams, ...params };

  // 同时更新设置文件中的模型参数
  // try {
  //   const settingsPath = path.join(storageDir, "settings.json");
  //   if (fs.existsSync(settingsPath)) {
  //     const settingsData = fs.readFileSync(settingsPath, "utf8");
  //     const settings = JSON.parse(settingsData);

  //     // 更新设置中的模型参数
  //     settings.modelParams = modelParams;

  //     // 保存更新后的设置
  //     fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 2));
  //     console.log("已更新设置文件中的模型参数");
  //   }
  // } catch (error) {
  //   console.error("更新设置文件中的模型参数失败:", error);
  // }

  // if (!pythonService) {
  //   return null;
  // }

  // // 重启 Python 服务以应用新参数
  // if (pythonService.isServiceRunning()) {
  //   await pythonService.stop();
  // }

  // // 将模型参数传递给 Python 服务
  // pythonService.setModelParams(modelParams);

  // // 重新启动服务
  // return await startPythonService();
});

// 设置数据存储目录
ipcMain.handle("set-data-storage-path", (event, path) => {
  dataStoragePath = path;
  console.log("设置数据存储目录:", dataStoragePath);

  // 如果Python服务已经启动，更新数据存储目录
  if (pythonService) {
    pythonService.setDataStoragePath(dataStoragePath);
  }

  return true;
});

// 获取模型参数
ipcMain.handle("get-model-params", () => {
  return modelParams;
});

// 保存数据到本地存储
ipcMain.handle("save-to-storage", (event, key, data) => {
  try {
    const filePath = path.join(storageDir, `${key}.json`);
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
    return true;
  } catch (error) {
    console.error(`保存数据失败 (${key}):`, error);
    return false;
  }
});

// 从本地存储加载数据
ipcMain.handle("load-from-storage", (event, key) => {
  try {
    const filePath = path.join(storageDir, `${key}.json`);
    if (fs.existsSync(filePath)) {
      const data = fs.readFileSync(filePath, "utf8");
      return JSON.parse(data);
    }
    return null;
  } catch (error) {
    console.error(`加载数据失败 (${key}):`, error);
    return null;
  }
});
