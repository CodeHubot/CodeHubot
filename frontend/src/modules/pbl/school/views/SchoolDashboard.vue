<template>
  <div class="school-dashboard">
    <!-- 学校管理员视图 -->
    <template v-if="authStore.isSchoolAdmin">
      <el-row :gutter="20" v-loading="loading">
        <!-- 数据卡片 -->
        <el-col :xs="24" :sm="12" :lg="6">
          <el-card class="stat-card teachers-card">
            <div class="stat-content">
              <el-icon :size="48" class="stat-icon"><User /></el-icon>
              <div class="stat-info">
                <div class="stat-value">{{ statistics.teacherCount || 0 }}</div>
                <div class="stat-label">教师总数</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :xs="24" :sm="12" :lg="6">
          <el-card class="stat-card students-card">
            <div class="stat-content">
              <el-icon :size="48" class="stat-icon"><UserFilled /></el-icon>
              <div class="stat-info">
                <div class="stat-value">{{ statistics.studentCount || 0 }}</div>
                <div class="stat-label">学生总数</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :xs="24" :sm="12" :lg="6">
          <el-card class="stat-card classes-card">
            <div class="stat-content">
              <el-icon :size="48" class="stat-icon"><Notebook /></el-icon>
              <div class="stat-info">
                <div class="stat-value">{{ statistics.classCount || 0 }}</div>
                <div class="stat-label">班级总数</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :xs="24" :sm="12" :lg="6">
          <el-card class="stat-card courses-card">
            <div class="stat-content">
              <el-icon :size="48" class="stat-icon"><Reading /></el-icon>
              <div class="stat-info">
                <div class="stat-value">{{ statistics.courseCount || 0 }}</div>
                <div class="stat-label">进行中课程</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      
      <!-- 快捷操作 -->
      <el-card style="margin-top: 20px">
        <template #header>
          <span>快捷操作</span>
        </template>
        <div class="quick-actions">
          <el-button type="primary" @click="goTo('/pbl/school/users')">
            <el-icon><Plus /></el-icon> 用户管理
          </el-button>
          <el-button type="success" @click="goTo('/pbl/school/classes')">
            <el-icon><Plus /></el-icon> 班级管理
          </el-button>
          <el-button type="info" @click="goTo('/pbl/school/available-templates')">
            <el-icon><Document /></el-icon> 浏览模板
          </el-button>
        </div>
      </el-card>
    </template>
    
    <!-- 教师视图 -->
    <template v-else-if="authStore.isTeacher">
      <div class="teacher-dashboard">
        <!-- 欢迎卡片 -->
        <el-card class="welcome-header" shadow="never" v-loading="loading">
          <div class="welcome-banner">
            <div class="banner-icon">
              <el-icon :size="80"><Reading /></el-icon>
            </div>
            <div class="banner-info">
              <h1 class="welcome-title">欢迎，{{ authStore.userInfo?.username || '教师' }}</h1>
              <p class="welcome-subtitle">
                <span v-if="authStore.userInfo?.school_name" class="school-name">{{ authStore.userInfo.school_name }}</span>
                <span class="separator" v-if="authStore.userInfo?.school_name">·</span>
                您可以在这里管理课程、学生和教学活动
              </p>
            </div>
          </div>
        </el-card>

        <!-- 权限功能卡片 -->
        <div class="permissions-grid">
          <!-- 普通权限卡片 -->
          <el-card class="permission-card" shadow="hover">
            <div class="card-icon primary">
              <el-icon><Reading /></el-icon>
            </div>
            <h3>课程管理</h3>
            <p>创建和管理课程内容</p>
          </el-card>

          <el-card class="permission-card" shadow="hover">
            <div class="card-icon success">
              <el-icon><UserFilled /></el-icon>
            </div>
            <h3>学生管理</h3>
            <p>查看和管理班级学生</p>
          </el-card>

          <!-- 重点功能卡片 - 重置密码 -->
          <el-card class="permission-card featured" shadow="hover">
            <div class="featured-badge">
              <el-icon><Star /></el-icon>
              重点功能
            </div>
            <div class="card-icon orange">
              <el-icon><Key /></el-icon>
            </div>
            <h3>重置学生密码</h3>
            <p>在用户管理页面重置密码</p>
          </el-card>

          <el-card class="permission-card" shadow="hover">
            <div class="card-icon info">
              <el-icon><Grid /></el-icon>
            </div>
            <h3>小组管理</h3>
            <p>管理学习小组和分组</p>
          </el-card>

          <el-card class="permission-card" shadow="hover">
            <div class="card-icon primary">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <h3>学习进度</h3>
            <p>查看学生学习进度</p>
          </el-card>
        </div>

        <!-- 提示信息 -->
        <el-alert
          type="info"
          :closable="false"
          show-icon
          class="info-alert"
        >
          <template #title>
            <span class="alert-title">使用提示</span>
          </template>
          在 <strong>用户管理</strong> 页面中，您可以为学生重置密码。重置后学生需要使用新密码登录。
        </el-alert>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { User, UserFilled, Notebook, Reading, Plus, Document, EditPen, Check, Key, InfoFilled, Star, TrendCharts, Grid } from '@element-plus/icons-vue'
import request from '@/utils/request'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)

// 学校管理员统计数据
const statistics = ref({
  teacherCount: 0,
  studentCount: 0,
  classCount: 0,
  courseCount: 0
})

onMounted(() => {
  if (authStore.isSchoolAdmin) {
    loadAdminStatistics()
  }
})

// 加载学校管理员统计数据
async function loadAdminStatistics() {
  try {
    loading.value = true
    
    // 使用便捷API，无需传递 school_uuid，更安全
    const response = await request.get('/pbl/admin/schools/my-school/statistics')
    
    if (response.success) {
      const data = response.data
      statistics.value = {
        teacherCount: data.teacher_count || 0,
        studentCount: data.student_count || 0,
        classCount: 0, // 暂时设为0，班级统计需要单独接口
        courseCount: 0  // 暂时设为0，课程统计需要单独接口
      }
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

function goTo(path) {
  router.push(path)
}
</script>

<style scoped lang="scss">
.school-dashboard {
  .stat-card {
    border-radius: 8px;
    transition: all 0.3s;
    cursor: default;
    
    &:hover {
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    .stat-content {
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 8px 0;
      
      .stat-icon {
        opacity: 0.9;
      }
      
      .stat-info {
        flex: 1;
        
        .stat-value {
          font-size: 28px;
          font-weight: 600;
          line-height: 1.2;
          margin-bottom: 4px;
        }
        
        .stat-label {
          font-size: 13px;
          color: #909399;
        }
      }
    }
    
    &.teachers-card {
      border-left: 3px solid #409eff;
      .stat-icon { color: #409eff; }
      .stat-value { color: #409eff; }
    }
    
    &.students-card {
      border-left: 3px solid #67c23a;
      .stat-icon { color: #67c23a; }
      .stat-value { color: #67c23a; }
    }
    
    &.classes-card {
      border-left: 3px solid #e6a23c;
      .stat-icon { color: #e6a23c; }
      .stat-value { color: #e6a23c; }
    }
    
    &.courses-card {
      border-left: 3px solid #f56c6c;
      .stat-icon { color: #f56c6c; }
      .stat-value { color: #f56c6c; }
    }
    
    &.pending-card {
      border-left: 3px solid #e6a23c;
      .stat-icon { color: #e6a23c; }
      .stat-value { color: #e6a23c; }
    }
  }
  
  .quick-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
  }
  
  // 教师工作台
  .teacher-dashboard {
    // 欢迎横幅
    .welcome-header {
      margin-bottom: 24px;
      border-radius: 16px;
      border: none;
      overflow: hidden;
      
      :deep(.el-card__body) {
        padding: 0;
      }
      
      .welcome-banner {
        display: flex;
        align-items: center;
        gap: 24px;
        padding: 32px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        
        .banner-icon {
          flex-shrink: 0;
          width: 100px;
          height: 100px;
          background: rgba(255, 255, 255, 0.2);
          border-radius: 20px;
          display: flex;
          align-items: center;
          justify-content: center;
          backdrop-filter: blur(10px);
          
          .el-icon {
            font-size: 80px;
          }
        }
        
        .banner-info {
          flex: 1;
          
          .welcome-title {
            margin: 0 0 12px 0;
            font-size: 32px;
            font-weight: 600;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
          }
          
          .welcome-subtitle {
            margin: 0;
            font-size: 16px;
            opacity: 0.95;
            line-height: 1.6;
            
            .school-name {
              font-weight: 600;
              font-size: 18px;
              background: rgba(255, 255, 255, 0.25);
              padding: 4px 12px;
              border-radius: 6px;
              margin-right: 8px;
              display: inline-block;
            }
            
            .separator {
              margin: 0 8px;
              opacity: 0.7;
            }
          }
        }
      }
    }
    
    // 权限卡片网格
    .permissions-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 20px;
      margin-bottom: 24px;
      
      .permission-card {
        border-radius: 12px;
        transition: all 0.3s ease;
        position: relative;
        cursor: default;
        border: 2px solid transparent;
        
        &:hover {
          transform: translateY(-4px);
          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
        }
        
        :deep(.el-card__body) {
          padding: 24px;
          text-align: center;
        }
        
        .card-icon {
          width: 64px;
          height: 64px;
          margin: 0 auto 16px;
          border-radius: 16px;
          display: flex;
          align-items: center;
          justify-content: center;
          
          .el-icon {
            font-size: 32px;
            color: white;
          }
          
          &.primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          }
          
          &.success {
            background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
          }
          
          &.warning {
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
          }
          
          &.info {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
          }
          
          &.orange {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
          }
        }
        
        h3 {
          margin: 0 0 8px 0;
          font-size: 18px;
          font-weight: 600;
          color: #303133;
        }
        
        p {
          margin: 0;
          font-size: 14px;
          color: #909399;
          line-height: 1.6;
        }
        
        // 特色卡片（重置密码）
        &.featured {
          border: 2px solid #ff9800;
          background: linear-gradient(135deg, #fff9f0 0%, #fff3e0 100%);
          
          &:hover {
            box-shadow: 0 8px 24px rgba(255, 152, 0, 0.3);
          }
          
          .featured-badge {
            position: absolute;
            top: -1px;
            right: -1px;
            background: linear-gradient(135deg, #ff9800 0%, #ff6b00 100%);
            color: white;
            padding: 4px 12px;
            border-radius: 0 10px 0 10px;
            font-size: 12px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 4px;
            box-shadow: 0 2px 8px rgba(255, 152, 0, 0.3);
            
            .el-icon {
              font-size: 14px;
            }
          }
          
          h3 {
            color: #e65100;
            font-size: 20px;
          }
          
          p {
            color: #f57c00;
            font-weight: 500;
          }
        }
      }
    }
    
    // 提示信息
    .info-alert {
      border-radius: 12px;
      border: none;
      
      :deep(.el-alert__content) {
        .alert-title {
          font-size: 16px;
          font-weight: 600;
        }
        
        strong {
          color: #409eff;
        }
      }
    }
  }
}
</style>
