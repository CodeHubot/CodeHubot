/**
 * 认证相关的 Composable
 * 确保用户信息正确加载
 */
import { ref, computed, onMounted, nextTick } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { usePlatformStore } from '@/stores/platform'

/**
 * 使用认证状态
 * 自动处理用户信息加载和响应式更新
 */
export function useAuth() {
  const authStore = useAuthStore()
  const platformStore = usePlatformStore()
  const loading = ref(true)

  onMounted(async () => {
    // 路由守卫已经确保了 authStore 初始化完成
    // 这里等待响应式更新
    await nextTick()
    
    // 加载平台配置
    if (!platformStore.isLoaded) {
      await platformStore.loadConfig()
    }
    
    // 如果 userInfo 还是 null，尝试重新获取
    if (authStore.isAuthenticated && !authStore.userInfo) {
      await authStore.refreshUserInfo()
    }
    
    loading.value = false
  })

  return {
    authStore,
    platformStore,
    loading,
    // 用户信息
    userInfo: computed(() => authStore.userInfo),
    userName: computed(() => authStore.userName),
    userRole: computed(() => authStore.userRole),
    userEmail: computed(() => authStore.userEmail),
    // 认证状态
    isAuthenticated: computed(() => authStore.isAuthenticated),
    // 角色判断
    isStudent: computed(() => authStore.isStudent),
    isTeacher: computed(() => authStore.isTeacher),
    isTeamAdmin: computed(() => authStore.isTeamAdmin),
    isAdmin: computed(() => authStore.isAdmin),
    isChannelPartner: computed(() => authStore.isChannelPartner),
    isChannelManager: computed(() => authStore.isChannelManager),
    // 平台配置
    platformName: computed(() => platformStore.platformName),
    platformDescription: computed(() => platformStore.platformDescription),
    // 方法
    login: authStore.login,
    logout: authStore.logout,
    refreshUserInfo: authStore.refreshUserInfo
  }
}

/**
 * 获取角色显示文本
 */
export function getRoleText(role) {
  const roleMap = {
    student: '学生',
    teacher: '教师',
    admin: '管理员',
    super_admin: '超级管理员',
    team_admin: '学校管理员',
    platform_admin: '平台管理员',
    channel_manager: '渠道管理员',
    channel_partner: '渠道商',
    individual: '个人用户'
  }
  return roleMap[role] || role
}
