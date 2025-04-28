// 声明 Vue 文件模块
declare module '*.vue' {
  import { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

// 扩展 Window 接口，添加 electron 属性
interface Window {
  electron: {
    ipcRenderer: {
      invoke(channel: string, ...args: any[]): Promise<any>;
      on(channel: string, func: (...args: any[]) => void): void;
      once(channel: string, func: (...args: any[]) => void): void;
    };
    platform: string;
  };
}
