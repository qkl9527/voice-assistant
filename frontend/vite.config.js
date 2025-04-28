import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import electron from "vite-plugin-electron";
import { resolve } from "path";

// https://vitejs.dev/config/
export default defineConfig(({ command }) => ({
  plugins: [
    vue(),
    command === "serve" &&
      electron({
        main: {
          entry: "electron/main.js",
        },
        preload: {
          input: "electron/preload.js",
        },
      }),
  ],
  resolve: {
    alias: {
      "@": resolve(__dirname, "src"),
    },
  },

  // build: {
  //   outDir: "dist/frontend", // 前端构建输出目录
  //   assetsDir: "assets", // 静态资源子目录
  //   emptyOutDir: true, // 构建前清空目录
  //   rollupOptions: {
  //     output: {
  //       // 确保资源文件路径正确
  //       assetFileNames: "assets/[name].[hash][extname]",
  //       chunkFileNames: "assets/[name].[hash].js",
  //       entryFileNames: "assets/[name].[hash].js",
  //     },
  //   },
  // },

  base: "./", // 关键！确保资源路径是相对路径
}));
