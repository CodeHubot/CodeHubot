<template>
  <div class="admin-dashboard">
    <el-container>
      <!-- 侧边栏 -->
      <el-aside :width="isCollapse ? '64px' : '250px'" class="admin-sidebar">
        <div class="admin-logo">
          <transition name="fade">
            <h2 v-if="!isCollapse">PBL管理后台</h2>
            <h2 v-else class="logo-mini">PBL</h2>
          </transition>
        </div>
        
        <el-menu
          :default-active="activeMenu"
          :collapse="isCollapse"
          :collapse-transition="false"
          router
          class="admin-menu"
          @select="handleMenuSelect"
        >
          <!-- 平台管理员菜单 -->
          <template v-if="isPlatformAdmin">
            <!-- 学校管理 -->
            <el-menu-item index="/pbl/admin/schools">
              <el-icon><OfficeBuilding /></el-icon>
              <template #title>学校管理</template>
            </el-menu-item>
            
            <!-- 课程管理 -->
            <el-sub-menu index="course-management">
              <template #title>
                <el-icon><Reading /></el-icon>
                <span>课程管理</span>
              </template>
              <el-menu-item index="/pbl/admin/courses">
                <el-icon><Document /></el-icon>
                <span>课程列表</span>
              </el-menu-item>
              <el-menu-item index="/pbl/admin/units">
                <el-icon><Collection /></el-icon>
                <span>学习单元</span>
              </el-menu-item>
              <el-menu-item index="/pbl/admin/resources">
                <el-icon><FolderOpened /></el-icon>
                <span>资料管理</span>
              </el-menu-item>
              <el-menu-item index="/pbl/admin/tasks">
                <el-icon><Tickets /></el-icon>
                <span>任务管理</span>
              </el-menu-item>
            </el-sub-menu>
            
          </template>
          
          <!-- 学校管理员菜单 -->
          <template v-else-if="isSchoolAdmin">
            <!-- 用户管理 -->
            <el-menu-item index="/pbl/admin/school-user-management">
              <el-icon><UserFilled /></el-icon>
              <template #title>用户管理</template>
            </el-menu-item>
            
            <!-- 班级管理 -->
            <el-menu-item index="/pbl/admin/classes">
              <el-icon><School /></el-icon>
              <template #title>班级管理</template>
            </el-menu-item>
            
            <!-- 课程模板库 - 仅学校管理员 -->
            <el-menu-item index="/pbl/admin/available-templates" v-if="!isPlatformAdmin">
              <el-icon><Files /></el-icon>
              <template #title>课程模板库</template>
            </el-menu-item>
          </template>
          
          <!-- 模板库管理 - 仅平台管理员 -->
          <template v-if="isPlatformAdmin">
            <el-sub-menu index="template-management">
              <template #title>
                <el-icon><Collection /></el-icon>
                <span>模板库管理</span>
              </template>
              <el-menu-item index="/pbl/admin/course-templates">
                <el-icon><Document /></el-icon>
                <span>课程模板管理</span>
              </el-menu-item>
              <el-menu-item index="/pbl/admin/template-permissions">
                <el-icon><Key /></el-icon>
                <span>课程模板授权</span>
              </el-menu-item>
            </el-sub-menu>
          </template>
          
          <!-- 渠道管理 - 平台管理员和渠道管理员 -->
          <template v-if="isPlatformAdmin || isChannelManager">
            <el-sub-menu index="channel-management">
              <template #title>
                <el-icon><Connection /></el-icon>
                <span>渠道管理</span>
              </template>
              <el-menu-item index="/pbl/admin/channel/partners">
                <el-icon><UserFilled /></el-icon>
                <span>渠道商管理</span>
              </el-menu-item>
              <el-menu-item index="/pbl/admin/channel/school-assignment">
                <el-icon><OfficeBuilding /></el-icon>
                <span>学校分配</span>
              </el-menu-item>
              <el-menu-item index="/pbl/admin/channel/statistics">
                <el-icon><DataAnalysis /></el-icon>
                <span>渠道统计</span>
              </el-menu-item>
            </el-sub-menu>
          </template>
          
          <!-- 教师菜单 -->
          <template v-else-if="isTeacher">
            <el-menu-item index="/pbl/admin/my-classes">
              <el-icon><School /></el-icon>
              <template #title>我的班级</template>
            </el-menu-item>
            
            <!-- 课程模板库 - 教师可查看 -->
            <el-menu-item index="/pbl/admin/available-templates">
              <el-icon><Files /></el-icon>
              <template #title>课程模板库</template>
            </el-menu-item>
          </template>
        </el-menu>
      </el-aside>

      <!-- 主内容区 -->
      <el-container>
        <el-header class="admin-header" :style="{ marginLeft: isCollapse ? '64px' : '250px' }">
          <div class="header-left">
            <el-button 
              :icon="isCollapse ? Expand : Fold" 
              circle 
              @click="toggleCollapse"
              class="collapse-btn"
            />
            <h3>{{ pageTitle }}</h3>
          </div>
          <div class="header-right">
            <!-- 个人信息下拉菜单 -->
            <el-dropdown @command="handleCommand" :hide-on-click="true">
              <div class="admin-user-info">
                <el-avatar :size="36" style="background-color: #409eff;">
                  <el-icon><User /></el-icon>
                </el-avatar>
                <div class="admin-user-details">
                  <div class="admin-user-name">
                    {{ adminInfo?.full_name || adminInfo?.username || '管理员' }}
                  </div>
                  <div class="admin-user-role">{{ userRoleText }}</div>
                </div>
                <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
              </div>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">
                    <el-icon><User /></el-icon>
                    个人信息
                  </el-dropdown-item>
                  <el-dropdown-item command="logout" divided>
                    <el-icon><SwitchButton /></el-icon>
                    退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>
        <el-main class="admin-main" :style="{ marginLeft: isCollapse ? '64px' : '250px' }">
          <router-view />
        </el-main>
      </el-container>
    </el-container>

    <!-- 个人信息对话框 -->
    <el-dialog
      v-model="profileDialogVisible"
      title="个人信息"
      width="500px"
      :close-on-click-modal="false"
    >
      <div class="profile-content">
        <div class="profile-avatar-section">
          <el-avatar :size="80" style="background-color: #409eff;">
            <el-icon :size="40"><User /></el-icon>
          </el-avatar>
        </div>
        
        <el-descriptions :column="1" border class="profile-descriptions">
          <el-descriptions-item label="用户名">
            <el-tag type="primary">{{ adminInfo?.username || '-' }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="姓名">
            {{ adminInfo?.full_name || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="邮箱">
            <el-icon style="margin-right: 4px;"><Message /></el-icon>
            {{ adminInfo?.email || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="电话">
            <el-icon style="margin-right: 4px;"><Phone /></el-icon>
            {{ adminInfo?.phone || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="角色">
            <el-tag type="success">{{ userRoleText }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="账号状态">
            <el-tag :type="adminInfo?.is_active ? 'success' : 'danger'">
              {{ adminInfo?.is_active ? '正常' : '已禁用' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ adminInfo?.created_at ? new Date(adminInfo.created_at).toLocaleString('zh-CN') : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="最后登录">
            {{ adminInfo?.last_login ? new Date(adminInfo.last_login).toLocaleString('zh-CN') : '-' }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
      
      <template #footer>
        <el-button @click="profileDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { 
  HomeFilled, 
  Document, 
  FolderOpened, 
  User, 
  DataAnalysis,
  Reading,
  Collection,
  Tickets,
  Avatar,
  School,
  Notebook,
  TrendCharts,
  Fold,
  Expand,
  SwitchButton,
  Operation,
  Files,
  Briefcase,
  Stamp,
  Edit,
  DocumentChecked,
  DocumentCopy,
  Box,
  Coin,
  MagicStick,
  View,
  Memo,
  ChatDotRound,
  MapLocation,
  ArrowDown,
  Message,
  Phone,
  VideoPlay,
  OfficeBuilding,
  UserFilled,
  Setting,
  Key,
  Connection
} from '@element-plus/icons-vue'
import { getCurrentAdmin } from '@/api/admin'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const adminInfo = ref(null)
const isCollapse = ref(false)
const activeMenu = computed(() => route.path)

// 判断管理员角色
const isPlatformAdmin = computed(() => {
  return adminInfo.value?.role === 'platform_admin'
})

const isSchoolAdmin = computed(() => {
  return adminInfo.value?.role === 'school_admin'
})

const isTeacher = computed(() => {
  return adminInfo.value?.role === 'teacher'
})

const isChannelManager = computed(() => {
  return adminInfo.value?.role === 'channel_manager'
})

const userRoleText = computed(() => {
  if (isPlatformAdmin.value) return '平台管理员'
  if (isSchoolAdmin.value) return '学校管理员'
  if (isTeacher.value) return '教师'
  if (isChannelManager.value) return '渠道管理员'
  return '管理员'
})

const pageTitle = computed(() => {
  // 根据角色和路径返回不同的标题
  if (route.path === '/pbl/admin/classes' && isTeacher.value) {
    return '我的班级课程'
  }
  
  const titles = {
    '/pbl/admin': '管理后台',
    '/pbl/admin/schools': '学校管理',
    '/pbl/admin/courses': '课程管理',
    '/pbl/admin/course-templates': '课程模板管理',
    '/pbl/admin/template-permissions': '课程模板授权',
    '/pbl/admin/available-templates': '课程模板库',
    '/pbl/admin/template-detail': '课程模板详情',
    '/pbl/admin/units': '学习单元',
    '/pbl/admin/resources': '资料管理',
    '/pbl/admin/tasks': '任务管理',
    '/pbl/admin/school-user-management': '用户管理',
    '/pbl/admin/classes': '项目式课程管理',
    '/pbl/admin/channel/partners': '渠道商管理',
    '/pbl/admin/channel/school-assignment': '学校分配',
    '/pbl/admin/channel/statistics': '渠道统计'
  }
  
  // 处理渠道商详情页面
  if (route.path.startsWith('/pbl/admin/channel/partners/')) {
    return '渠道商详情'
  }
  
  return titles[route.path] || '管理后台'
})

const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
  // 保存折叠状态
  localStorage.setItem('admin_sidebar_collapse', isCollapse.value)
}

const handleMenuSelect = (index) => {
  // 确保路由正确导航
  if (index && index !== route.path) {
    router.push(index)
  }
}

const profileDialogVisible = ref(false)

const handleCommand = (command) => {
  if (command === 'logout') {
    // 使用 authStore 的 logout 方法清除所有认证信息
    authStore.logout()
    ElMessage.success('已退出登录')
    // 使用 router.replace 而不是 push，避免可以通过后退按钮返回
    router.replace('/login')
  } else if (command === 'profile') {
    profileDialogVisible.value = true
  }
}

onMounted(async () => {
  try {
    const admin = await getCurrentAdmin()
    adminInfo.value = admin
    
    // 保存管理员信息到 localStorage，供路由守卫使用
    localStorage.setItem('admin_info', JSON.stringify(admin))
    
    // 恢复折叠状态
    const savedCollapse = localStorage.getItem('admin_sidebar_collapse')
    if (savedCollapse !== null) {
      isCollapse.value = savedCollapse === 'true'
    }
  } catch (error) {
    console.error('获取管理员信息失败:', error)
  }
})
</script>

<style scoped>
.admin-dashboard {
  height: 100vh;
  overflow: hidden;
}

.admin-sidebar {
  background: linear-gradient(180deg, #1f2937 0%, #111827 100%);
  color: white;
  height: 100vh;
  position: fixed;
  left: 0;
  top: 0;
  overflow-y: auto;
  overflow-x: hidden;
  transition: width 0.3s ease;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
  z-index: 1000;
}

.admin-sidebar::-webkit-scrollbar {
  width: 6px;
}

.admin-sidebar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}

.admin-sidebar::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}

.admin-logo {
  padding: 24px 20px;
  text-align: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.05);
}

.admin-logo h2 {
  margin: 0;
  color: white;
  font-size: 20px;
  font-weight: 600;
  letter-spacing: 1px;
}

.admin-logo .logo-mini {
  font-size: 16px;
}

.admin-menu {
  border: none;
  background: transparent;
  padding: 10px 0;
}

.admin-menu :deep(.el-menu-item) {
  color: rgba(255, 255, 255, 0.75);
  margin: 4px 12px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.admin-menu :deep(.el-menu-item:hover) {
  background: rgba(64, 158, 255, 0.15);
  color: #409eff;
}

.admin-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, #409eff 0%, #66b1ff 100%);
  color: white;
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}

.admin-menu :deep(.el-sub-menu__title) {
  color: rgba(255, 255, 255, 0.75);
  margin: 4px 12px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.admin-menu :deep(.el-sub-menu__title:hover) {
  background: rgba(255, 255, 255, 0.08);
  color: white;
}

.admin-menu :deep(.el-sub-menu.is-active > .el-sub-menu__title) {
  color: #409eff;
}

.admin-menu :deep(.el-menu--inline) {
  background: rgba(0, 0, 0, 0.1);
}

.admin-menu :deep(.el-menu--inline .el-menu-item) {
  padding-left: 56px !important;
  min-width: auto;
  background: transparent;
}

.admin-menu :deep(.el-menu--inline .el-menu-item:hover) {
  background: rgba(64, 158, 255, 0.12);
}

.admin-menu :deep(.el-menu--inline .el-menu-item.is-active) {
  background: rgba(64, 158, 255, 0.2);
  color: #66b1ff;
  box-shadow: none;
}

/* 折叠状态样式 */
.admin-menu.el-menu--collapse {
  width: 64px;
}

.admin-menu.el-menu--collapse :deep(.el-menu-item),
.admin-menu.el-menu--collapse :deep(.el-sub-menu__title) {
  margin: 4px 8px;
  justify-content: center;
}

.admin-user {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(0, 0, 0, 0.2);
}

.admin-user-info {
  color: rgba(255, 255, 255, 0.85);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.admin-user-info:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.admin-user-name {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.admin-header {
  background: white;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  position: fixed;
  right: 0;
  top: 0;
  left: 0;
  height: 60px;
  z-index: 999;
  transition: margin-left 0.3s ease;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.collapse-btn {
  border: none;
  background: #f5f7fa;
  color: #606266;
  transition: all 0.3s ease;
}

.collapse-btn:hover {
  background: #409eff;
  color: white;
}

.admin-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.admin-main {
  padding: 24px;
  background: #f5f7fa;
  height: calc(100vh - 60px);
  position: fixed;
  right: 0;
  top: 60px;
  left: 0;
  overflow-y: auto;
  transition: margin-left 0.3s ease;
}

/* 淡入淡出动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 个人信息样式 */
.admin-user-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
  line-height: 1.4;
}

.admin-user-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.admin-user-role {
  font-size: 12px;
  color: #909399;
}

.dropdown-icon {
  margin-left: 4px;
  transition: transform 0.3s ease;
  color: #909399;
}

.admin-user-info:hover .dropdown-icon {
  transform: translateY(2px);
  color: #409eff;
}

/* 个人信息对话框样式 */
.profile-content {
  padding: 10px 0;
}

.profile-avatar-section {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 24px;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
}

.profile-descriptions {
  margin-top: 16px;
}

.profile-descriptions :deep(.el-descriptions__label) {
  width: 100px;
  font-weight: 500;
  color: #606266;
}

.profile-descriptions :deep(.el-descriptions__content) {
  color: #303133;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .admin-sidebar {
    width: 64px !important;
  }
  
  .admin-header {
    margin-left: 64px !important;
  }
  
  .admin-main {
    margin-left: 64px !important;
  }
  
  .collapse-btn {
    display: none;
  }
  
  .admin-user-details {
    display: none;
  }
}
</style>
