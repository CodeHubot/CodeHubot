<template>
  <el-menu
    :default-active="$route.path"
    class="sidebar-menu"
    router
    :collapse="isCollapsed"
    background-color="transparent"
    text-color="#374151"
    active-text-color="#3b82f6"
  >
    <el-menu-item index="/pbl/student/courses" class="menu-item">
      <el-icon><Reading /></el-icon>
      <template #title>我的课程</template>
    </el-menu-item>
    
    <el-menu-item index="/pbl/student/tasks" class="menu-item">
      <el-icon><Document /></el-icon>
      <template #title>我的任务</template>
    </el-menu-item>
    
    <el-menu-item index="/pbl/student/learning-assistant" class="menu-item">
      <el-icon><ChatDotRound /></el-icon>
      <template #title>AI学习助手</template>
    </el-menu-item>
    
    <el-menu-item index="/pbl/student/portfolio" class="menu-item">
      <el-icon><Collection /></el-icon>
      <template #title>学习档案</template>
    </el-menu-item>
  </el-menu>
</template>

<script setup>
import { Reading, Document, Collection, ChatDotRound } from '@element-plus/icons-vue'

defineProps({
  isCollapsed: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped lang="scss">
.sidebar-menu {
  border: none;
  flex: 1;
  overflow-y: auto;
  background: transparent !important;
}

:deep(.menu-item) {
  margin: 4px 12px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

:deep(.menu-item:hover) {
  background: rgba(59, 130, 246, 0.08) !important;
  transform: translateX(4px);
}

:deep(.menu-item.is-active) {
  background: linear-gradient(90deg, rgba(59, 130, 246, 0.15), rgba(59, 130, 246, 0.08)) !important;
  color: #3b82f6 !important;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
  border-left: 3px solid #3b82f6;
}

:deep(.menu-item.is-active .el-icon) {
  color: #3b82f6;
}

.sidebar-menu::-webkit-scrollbar {
  width: 6px;
}

.sidebar-menu::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

.sidebar-menu::-webkit-scrollbar-thumb:hover {
  background: rgba(59, 130, 246, 0.3);
}
</style>

