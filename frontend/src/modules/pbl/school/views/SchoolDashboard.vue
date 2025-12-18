<template>
  <div class="school-dashboard">
    <el-row :gutter="20">
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
    
    <el-row :gutter="20" style="margin-top: 20px">
      <!-- 快捷操作 -->
      <el-col :xs="24" :sm="24" :lg="12">
        <el-card>
          <template #header>
            <span>快捷操作</span>
          </template>
          <div class="quick-actions">
            <el-button type="primary" @click="goTo('/pbl/school/teachers')" v-if="authStore.isSchoolAdmin">
              <el-icon><Plus /></el-icon> 添加教师
            </el-button>
            <el-button type="success" @click="goTo('/pbl/school/students')" v-if="authStore.isSchoolAdmin">
              <el-icon><Plus /></el-icon> 添加学生
            </el-button>
            <el-button type="warning" @click="goTo('/pbl/school/classes')" v-if="authStore.isSchoolAdmin">
              <el-icon><Plus /></el-icon> 创建班级
            </el-button>
            <el-button type="info" @click="goTo('/pbl/school/available-templates')">
              <el-icon><Document /></el-icon> 浏览模板
            </el-button>
          </div>
        </el-card>
      </el-col>
      
      <!-- 最近活动 -->
      <el-col :xs="24" :sm="24" :lg="12">
        <el-card>
          <template #header>
            <span>最近活动</span>
          </template>
          <el-empty v-if="!activities.length" description="暂无活动记录" :image-size="100" />
          <el-timeline v-else>
            <el-timeline-item
              v-for="(activity, index) in activities"
              :key="index"
              :timestamp="activity.timestamp"
              placement="top"
            >
              {{ activity.content }}
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { User, UserFilled, Notebook, Reading, Plus, Document } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const statistics = ref({
  teacherCount: 0,
  studentCount: 0,
  classCount: 0,
  courseCount: 0
})

const activities = ref([])

onMounted(() => {
  loadStatistics()
  loadActivities()
})

function loadStatistics() {
  // TODO: 从后端API加载统计数据
  statistics.value = {
    teacherCount: 25,
    studentCount: 480,
    classCount: 12,
    courseCount: 8
  }
}

function loadActivities() {
  // TODO: 从后端API加载活动记录
  activities.value = [
    { timestamp: '2024-01-18 10:30', content: '张老师创建了新班级"AI实验班"' },
    { timestamp: '2024-01-18 09:15', content: '导入了30名新学生' },
    { timestamp: '2024-01-17 16:20', content: '李老师开始了课程"Python基础"' }
  ]
}

function goTo(path) {
  router.push(path)
}
</script>

<style scoped lang="scss">
.school-dashboard {
  .stat-card {
    border-radius: 12px;
    transition: all 0.3s;
    
    &:hover {
      transform: translateY(-5px);
      box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
    }
    
    .stat-content {
      display: flex;
      align-items: center;
      gap: 20px;
      
      .stat-icon {
        opacity: 0.8;
      }
      
      .stat-info {
        flex: 1;
        
        .stat-value {
          font-size: 32px;
          font-weight: bold;
          line-height: 1;
          margin-bottom: 8px;
        }
        
        .stat-label {
          font-size: 14px;
          color: #909399;
        }
      }
    }
    
    &.teachers-card {
      border-top: 4px solid #409eff;
      .stat-icon { color: #409eff; }
      .stat-value { color: #409eff; }
    }
    
    &.students-card {
      border-top: 4px solid #67c23a;
      .stat-icon { color: #67c23a; }
      .stat-value { color: #67c23a; }
    }
    
    &.classes-card {
      border-top: 4px solid #e6a23c;
      .stat-icon { color: #e6a23c; }
      .stat-value { color: #e6a23c; }
    }
    
    &.courses-card {
      border-top: 4px solid #f56c6c;
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
