<template>
  <div class="school-dashboard">
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
    <el-card style="margin-top: 20px" v-if="authStore.isSchoolAdmin">
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { User, UserFilled, Notebook, Reading, Plus, Document } from '@element-plus/icons-vue'
import { getCurrentAdmin } from '@/api/admin'
import request from '@/utils/request'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const statistics = ref({
  teacherCount: 0,
  studentCount: 0,
  classCount: 0,
  courseCount: 0
})

onMounted(() => {
  loadStatistics()
})

async function loadStatistics() {
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
  }
  
  .quick-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
  }
}
</style>
