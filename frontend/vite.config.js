import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  base: '/',  // 部署到根目录，确保资源路径正确
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: process.env.VITE_DEV_PORT ? parseInt(process.env.VITE_DEV_PORT) : 3001,
    proxy: {
      '/api': {
        target: process.env.VITE_DEV_PROXY_TARGET || 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  build: {
    // 生产环境移除console和debugger
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,  // 移除所有console
        drop_debugger: true,  // 移除debugger
        pure_funcs: ['console.log', 'console.debug']  // 额外确保移除
      }
    },
    // 生成source map（调试用，生产环境可关闭）
    sourcemap: false,
    // 优化chunk分割
    rollupOptions: {
      output: {
        // 使用函数形式分割代码，避免循环依赖
        manualChunks(id) {
          // Element Plus 单独打包
          if (id.includes('node_modules/element-plus')) {
            return 'element-plus'
          }
          // Element Plus 图标单独打包
          if (id.includes('node_modules/@element-plus/icons-vue')) {
            return 'element-icons'
          }
          // Vue 核心库单独打包
          if (id.includes('node_modules/vue/') || 
              id.includes('node_modules/@vue/') ||
              id.includes('node_modules/vue-router/') || 
              id.includes('node_modules/pinia/')) {
            return 'vue-vendor'
          }
          // ECharts 单独打包
          if (id.includes('node_modules/echarts')) {
            return 'echarts'
          }
          // 其他第三方库
          if (id.includes('node_modules')) {
            return 'vendor'
          }
        }
      }
    }
  }
})
