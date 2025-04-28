const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");
const os = require("os");

class PythonService {
  constructor(port) {
    this.pythonProcess = null;
    this.port = port;
    this.isRunning = false;
    this.startupTimeout = null;
    this.pythonPath = this.getPythonPath();
    this.backendPath = this.getBackendPath();
    this.pythonEnv = this.getPythonEnv();
    this.maxRetries = 3;
    this.retryCount = 0;
    this.retryDelay = 2000; // 2秒
    this.startupTimeoutDuration = 60000; // 增加到60秒
    this.modelParams = {
      model: "paraformer-zh", // paraformer-zh-streaming
      vadModel: "fsmn-vad", // fsmn-vad
      puncModel: "", // ct-punc
      spkModel: "", // cam++
      disableUpdate: true,
      device: "cuda", // cuda 或 cpu
      ngpu: 0, // GPU 设备 ID
      hotwords: "", // 热词列表
    };
    this.dataStoragePath = ""; // 数据存储目录
  }

  // 设置模型参数
  setModelParams(params) {
    this.modelParams = { ...this.modelParams, ...params };
    console.log("设置模型参数:", this.modelParams);
  }

  // 设置数据存储目录
  setDataStoragePath(path) {
    this.dataStoragePath = path;
    console.log("设置数据存储目录:", this.dataStoragePath);
  }

  // 获取 Python 可执行文件路径
  getPythonPath() {
    // 如果设置了环境变量，优先使用环境变量中的 Python 路径
    if (process.env.ASR_PYTHON_PATH) {
      console.log(
        `使用环境变量指定的 Python 路径: ${process.env.ASR_PYTHON_PATH}`
      );
      return process.env.ASR_PYTHON_PATH;
    }

    // 尝试使用虚拟环境中的 Python
    const rootDir = path.join(__dirname, "..", "..");
    const platform = process.platform;
    let venvPythonPath;

    if (platform === "win32") {
      venvPythonPath = path.join(rootDir, ".venv", "Scripts", "python.exe");
    } else {
      venvPythonPath = path.join(rootDir, ".venv", "bin", "python");
    }

    // 检查虚拟环境 Python 是否存在
    if (fs.existsSync(venvPythonPath)) {
      console.log(`使用虚拟环境 Python: ${venvPythonPath}`);
      return venvPythonPath;
    }

    // 如果虚拟环境不存在，回退到系统 Python
    console.log("虚拟环境不存在，使用系统 Python");
    return platform === "win32" ? "python" : "python3";
  }

  // 获取 Python 环境变量
  getPythonEnv() {
    const env = { ...process.env };

    // 设置 PYTHONPATH 以确保能找到所有依赖
    const rootDir = path.join(__dirname, "..", "..");
    const venvDir = path.join(rootDir, ".venv");

    // 根据平台确定 site-packages 路径
    let sitePkgPath;
    if (process.platform === "win32") {
      sitePkgPath = path.join(venvDir, "Lib", "site-packages");
    } else {
      // 查找 Python 版本目录
      try {
        const pythonDirs = fs
          .readdirSync(path.join(venvDir, "lib"))
          .filter((dir) => dir.startsWith("python"));

        if (pythonDirs.length > 0) {
          sitePkgPath = path.join(
            venvDir,
            "lib",
            pythonDirs[0],
            "site-packages"
          );
        } else {
          // 如果找不到特定版本，使用通用路径
          sitePkgPath = path.join(venvDir, "lib", "python3", "site-packages");
        }
      } catch (err) {
        console.error(`查找 site-packages 目录失败: ${err.message}`);
        // 使用通用路径作为回退
        sitePkgPath = path.join(venvDir, "lib", "python3", "site-packages");
      }
    }

    // 设置 PYTHONPATH
    if (fs.existsSync(sitePkgPath)) {
      env.PYTHONPATH =
        sitePkgPath + (env.PYTHONPATH ? path.delimiter + env.PYTHONPATH : "");
    }

    // 设置 VIRTUAL_ENV
    env.VIRTUAL_ENV = venvDir;

    // 在 PATH 前面添加虚拟环境的 bin 目录
    const binDir =
      process.platform === "win32"
        ? path.join(venvDir, "Scripts")
        : path.join(venvDir, "bin");

    if (fs.existsSync(binDir)) {
      env.PATH = binDir + path.delimiter + env.PATH;
    }

    // 禁用 Python 的 __pycache__ 目录，避免权限问题
    env.PYTHONDONTWRITEBYTECODE = "1";

    // 设置 Python 不使用缓冲输出，确保日志实时显示
    env.PYTHONUNBUFFERED = "1";

    console.log("Python 环境变量设置完成");
    return env;
  }

  // 获取后端路径
  getBackendPath() {
    return path.join(__dirname, "..", "..", "backend");
  }

  // 启动 Python 服务
  start() {
    if (this.isRunning) {
      console.log("Python 服务已经在运行");
      return Promise.resolve(this.port);
    }

    return new Promise((resolve, reject) => {
      console.log(`启动 Python 服务，路径: ${this.backendPath}`);
      console.log(`Python 可执行文件: ${this.pythonPath}`);

      // 检查 app.py 是否存在
      const appPath = path.join(this.backendPath, "app.py");
      if (!fs.existsSync(appPath)) {
        return reject(new Error(`找不到 Python 后端文件: ${appPath}`));
      }

      // 准备命令行参数
      const args = [appPath, this.port.toString()];

      // 添加模型参数
      if (this.modelParams) {
        args.push("--model", this.modelParams.model);

        if (this.modelParams.vadModel) {
          args.push("--vad-model", this.modelParams.vadModel);
        }

        if (this.modelParams.puncModel) {
          args.push("--punc-model", this.modelParams.puncModel);
        }
        if (this.modelParams.spkModel) {
          args.push("--spk-model", this.modelParams.spkModel);
        }

        if (this.modelParams.disableUpdate) {
          args.push("--disable-update");
        }

        // 添加设备类型参数
        args.push("--device", this.modelParams.device);

        // 添加 GPU 设备 ID 参数
        args.push("--ngpu", this.modelParams.ngpu.toString());

        // 添加热词参数
        if (this.modelParams.hotwords) {
          args.push("--hotwords", this.modelParams.hotwords);
        }
      }

      // 添加数据存储目录参数
      if (this.dataStoragePath) {
        args.push("--data-storage-path", this.dataStoragePath);
      }

      console.log("启动 Python 进程参数:", args);

      // 启动 Python 进程
      this.pythonProcess = spawn(this.pythonPath, args, {
        cwd: this.backendPath,
        stdio: ["pipe", "pipe", "pipe"],
        env: this.pythonEnv,
        // 确保子进程在父进程退出时也退出
        detached: false,
      });

      // 设置超时
      this.startupTimeout = setTimeout(() => {
        if (!this.isRunning) {
          console.log(
            `启动 Python 服务超时（${
              this.startupTimeoutDuration / 1000
            }秒），尝试重启...`
          );
          this.stop().then(() => {
            if (this.retryCount < this.maxRetries) {
              this.retryCount++;
              setTimeout(() => {
                this.start().then(resolve).catch(reject);
              }, this.retryDelay);
            } else {
              reject(
                new Error(`启动 Python 服务失败，已重试 ${this.maxRetries} 次`)
              );
            }
          });
        }
      }, this.startupTimeoutDuration); // 60 秒超时

      // 处理标准输出
      this.pythonProcess.stdout.on("data", (data) => {
        const output = data.toString();
        console.log(`Python 输出: ${output}`);

        // 检查服务是否已启动
        if (output.includes("Running on")) {
          clearTimeout(this.startupTimeout);
          this.isRunning = true;
          this.retryCount = 0; // 重置重试计数
          resolve(this.port);
        }
      });

      // 处理标准错误
      this.pythonProcess.stderr.on("data", (data) => {
        console.error(`Python 错误: ${data.toString()}`);
      });

      // 处理进程退出
      this.pythonProcess.on("close", (code) => {
        console.log(`Python 进程退出，代码: ${code}`);
        clearTimeout(this.startupTimeout);

        // 只有在服务已经标记为运行时才尝试重启
        if (this.isRunning) {
          this.isRunning = false;
          this.pythonProcess = null;

          // 尝试重启服务
          if (this.retryCount < this.maxRetries) {
            console.log(
              `Python 服务意外退出，尝试重启 (${this.retryCount + 1}/${
                this.maxRetries
              })...`
            );
            this.retryCount++;
            setTimeout(() => {
              this.start().catch((err) => {
                console.error(`重启 Python 服务失败: ${err.message}`);
              });
            }, this.retryDelay);
          } else {
            console.error(
              `Python 服务已重试 ${this.maxRetries} 次，不再尝试重启`
            );
          }
        } else {
          this.pythonProcess = null;
        }
      });

      // 处理错误
      this.pythonProcess.on("error", (err) => {
        console.error(`启动 Python 进程错误: ${err.message}`);
        clearTimeout(this.startupTimeout);
        this.isRunning = false;
        this.pythonProcess = null;
        reject(err);
      });

      // 尝试通过 HTTP 请求检查服务是否启动
      this.checkServiceHealth();
    });
  }

  // 通过 HTTP 请求检查服务是否启动
  checkServiceHealth() {
    // 每秒检查一次，直到服务启动或超时
    const healthCheckInterval = setInterval(() => {
      if (this.isRunning) {
        clearInterval(healthCheckInterval);
        return;
      }

      const http = require("http");
      const options = {
        hostname: "127.0.0.1",
        port: this.port,
        path: "/",
        method: "GET",
        timeout: 1000, // 1秒超时
      };

      const req = http.request(options, (res) => {
        if (res.statusCode === 200) {
          console.log("服务健康检查成功，服务已启动");
          clearTimeout(this.startupTimeout);
          clearInterval(healthCheckInterval);
          this.isRunning = true;
        }
      });

      req.on("error", (e) => {
        // 忽略错误，继续等待
      });

      req.end();
    }, 1000); // 每秒检查一次

    // 确保在超时后清除间隔
    setTimeout(() => {
      clearInterval(healthCheckInterval);
    }, this.startupTimeoutDuration);
  }

  // 停止 Python 服务
  stop() {
    if (!this.pythonProcess) {
      console.log("Python 服务未运行");
      return Promise.resolve();
    }

    return new Promise((resolve) => {
      console.log("停止 Python 服务");

      // 清理
      clearTimeout(this.startupTimeout);
      this.isRunning = false;

      // 给进程一个优雅退出的机会
      const killTimeout = setTimeout(() => {
        console.log("Python 服务未能优雅退出，强制终止");
        if (this.pythonProcess) {
          // 在 Windows 上使用 taskkill 强制终止进程
          if (process.platform === "win32") {
            spawn("taskkill", ["/pid", this.pythonProcess.pid, "/f", "/t"]);
          } else {
            // 在 Unix 系统上发送 SIGKILL 信号
            this.pythonProcess.kill("SIGKILL");
          }
        }
      }, 5000); // 5秒后强制终止

      // 尝试优雅退出
      if (this.pythonProcess) {
        // 在 Windows 上使用 CTRL+C 信号
        if (process.platform === "win32") {
          this.pythonProcess.kill("SIGINT");
        } else {
          // 在 Unix 系统上发送 SIGTERM 信号
          this.pythonProcess.kill("SIGTERM");
        }

        // 监听进程退出
        this.pythonProcess.once("close", () => {
          clearTimeout(killTimeout);
          this.pythonProcess = null;
          resolve();
        });
      } else {
        clearTimeout(killTimeout);
        resolve();
      }
    });
  }

  // 获取服务 URL
  getUrl() {
    return `http://localhost:${this.port}`;
  }

  // 检查服务状态
  isServiceRunning() {
    return this.isRunning;
  }
}

module.exports = PythonService;
