<template>
  <el-container class="pbl-layout pbl-school-layout">
    <el-aside width="240px" class="layout-aside">
      <div class="logo-container">
        <el-icon :size="28" color="#fcb69f"><School /></el-icon>
        <span class="logo-text">学校管理平台</span>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        :router="true"
        class="layout-menu"
      >
        <el-menu-item index="/pbl/school/dashboard">
          <el-icon><HomeFilled /></el-icon>
          <span>管理概览</span>
        </el-menu-item>
        
        <!-- 学校管理员功能 -->
        <template v-if="authStore.isSchoolAdmin">
          <el-menu-item index="/pbl/school/teachers">
            <el-icon><User /></el-icon>
            <span>教师管理</span>
          </el-menu-item>
          
          <el-menu-item index="/pbl/school/students">
            <el-icon><UserFilled /></el-icon>
            <span>学生管理</span>
          </el-menu-item>
          
          <el-menu-item index="/pbl/school/classes">
            <el-icon><Notebook /></el-icon>
            <span>班级管理</span>
          </el-menu-item>
          
          <el-menu-item index="/pbl/school/available-templates">
            <el-icon><Document /></el-icon>
            <span>课程模板库</span>
          </el-menu-item>
          
          <el-menu-item index="/pbl/school/statistics">
            <el-icon><TrendCharts /></el-icon>
            <span>数据统计</span>
          </el-menu-item>
        </template>
        
        <!-- 教师功能（受限） -->
        <template v-if="authStore.isTeacher && !authStore.isSchoolAdmin">
          <el-menu-item index="/pbl/school/my-classes">
            <el-icon><Notebook /></el-icon>
            <span>我的班级</span>
          </el-menu-item>
          
          <el-menu-item index="/pbl/school/available-templates">
            <el-icon><Document /></el-icon>
            <span>课程模板库</span>
          </el-menu-item>
        </template>
      </el-menu>
    </el-aside>
    
    <el-container>
      <el-header class="layout-header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>学校管理平台</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="header-right">
          <el-button text @click="backToPortal">
            <el-icon><Grid /></el-icon> 切换系统
          </el-button>
          
          <el-dropdown @command="handleCommand">
            <span class="user-dropdown">
              <el-avatar :size="32" :style="{ background: '#fcb69f' }">
                {{ authStore.userName?.charAt(0) || 'U' }}
              </el-avatar>
              <span class="user-name">{{ authStore.userName }}</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <el-main class="layout-main">
        <router-view v-slot="{ Component }">
          <transition name="fade-transform" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  School, HomeFilled, User, UserFilled, Notebook, Document, TrendCharts, Grid
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)

function backToPortal() {
  router.push('/')
}

function handleCommand(command) {
  if (command === 'logout') {
    ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(() => {
      authStore.logout()
      router.push('/login')
      ElMessage.success('已退出登录')
    })
  } else if (command === 'profile') {
    ElMessage.info('个人中心功能开发中...')
  }
}
</script>

<style scoped lang="scss">
.pbl-school-layout {
  height: 100vh;
  
  .layout-aside {
    background: linear-gradient(180deg, #ffecd2 0%, #fcb69f 100%);
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
    
    .logo-container {
      height: 60px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 12px;
      padding: 0 20px;
      background: rgba(255, 255, 255, 0.2);
      backdrop-filter: blur(10px);
      
      .logo-text {
        font-size: 18px;
        font-weight: 600;
        color: #d35400;
      }
    }
    
    .layout-menu {
      border: none;
      background: transparent;
      padding: 10px;
      
      :deep(.el-menu-item) {
        border-radius: 8px;
        margin-bottom: 6px;
        color: #8b5a3c;
        transition: all 0.3s;
        
        &:hover {
          background: rgba(255, 255, 255, 0.3);
          color: #d35400;
        }
        
        &.is-active {
          background: rgba(255, 255, 255, 0.5);
          color: #d35400;
          font-weight: 600;
        }
      }
    }
  }
  
  .layout-header {
    height: 60px;
    background: white;
    border-bottom: 1px solid #f0f0f0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 24px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    
    .header-left {
      :deep(.el-breadcrumb__item) {
        .el-breadcrumb__inner {
          color: #606266;
          font-weight: 500;
          
          &:hover {
            color: #fcb69f;
          }
        }
        
        &:last-child .el-breadcrumb__inner {
          color: #303133;
        }
      }
    }
    
    .header-right {
      display: flex;
      align-items: center;
      gap: 20px;
      
      .user-dropdown {
        display: flex;
        align-items: center;
        gap: 8px;
        cursor: pointer;
        padding: 6px 12px;
        border-radius: 20px;
        transition: background 0.3s;
        
        &:hover {
          background: #f5f5f5;
        }
        
        .user-name {
          font-size: 14px;
          color: #303133;
          font-weight: 500;
        }
      }
    }
  }
  
  .layout-main {
    background: #f5f7fa;
    padding: 20px;
    overflow-y: auto;
  }
}

.fade-transform-leave-active,
.fade-transform-enter-active {
  transition: all 0.3s;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
</style>
