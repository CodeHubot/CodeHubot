<template>
  <!-- 这是一个无界面的监控组件 -->
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../store/user'
import { ElMessage } from 'element-plus'
import logger from '@/utils/logger'

const router = useRouter()
const userStore = useUserStore()
let checkInterval = null

// 定期检查token状态（仅作为兜底机制）
// 注意：token刷新主要由请求拦截器和响应拦截器处理
// 这里只检查refresh token是否过期，如果过期则登出
const startTokenMonitoring = () => {
  logger.debug('TokenMonitor: 开始token监控（兜底检查）')
  // 每5分钟检查一次refresh token状态（降低频率，减少不必要的检查）
  checkInterval = setInterval(() => {
    if (userStore.token || userStore.refreshToken) {
      // 只检查 refresh token 是否过期（作为兜底机制）
      // token刷新由请求拦截器和响应拦截器自动处理
      if (userStore.isRefreshTokenExpired) {
        logger.warn('TokenMonitor: Refresh token已过期，执行登出')
        ElMessage.warning('登录已过期，请重新登录')
        userStore.logout('Refresh token已过期')
        if (router.currentRoute.value.path !== '/login') {
          logger.info('TokenMonitor: 重定向到登录页')
          router.push('/login')
        }
      }
    }
  }, 300000) // 每5分钟检查一次（降低频率）
}

const stopTokenMonitoring = () => {
  logger.debug('TokenMonitor: 停止token监控')
  if (checkInterval) {
    clearInterval(checkInterval)
    checkInterval = null
  }
}

onMounted(() => {
  startTokenMonitoring()
})

onUnmounted(() => {
  stopTokenMonitoring()
})
</script>