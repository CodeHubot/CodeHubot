<template>
  <div class="admin-dashboard-content">
    <el-row :gutter="20">
      <el-col :span="24">
        <h2>管理控制台</h2>
        <p class="subtitle">欢迎使用 PBL 平台管理系统</p>
      </el-col>
    </el-row>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card school-card">
          <div class="stat-icon">
            <el-icon :size="40"><School /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.totalSchools }}</div>
            <div class="stat-label">学校总数</div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card user-card">
          <div class="stat-icon">
            <el-icon :size="40"><User /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.totalUsers }}</div>
            <div class="stat-label">用户总数</div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card course-card">
          <div class="stat-icon">
            <el-icon :size="40"><Reading /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.totalCourses }}</div>
            <div class="stat-label">课程总数</div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card template-card">
          <div class="stat-icon">
            <el-icon :size="40"><Document /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.totalTemplates }}</div>
            <div class="stat-label">课程模板</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快捷操作 -->
    <el-row :gutter="20" class="quick-actions">
      <el-col :span="24">
        <h3>快捷操作</h3>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="action-card" @click="goToSchools" shadow="hover">
          <el-icon :size="30"><School /></el-icon>
          <div class="action-label">学校管理</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="action-card" @click="goToTemplates" shadow="hover">
          <el-icon :size="30"><Document /></el-icon>
          <div class="action-label">课程模板</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="action-card" @click="goToChannels" shadow="hover">
          <el-icon :size="30"><Connection /></el-icon>
          <div class="action-label">渠道管理</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="action-card" @click="goToClasses" shadow="hover">
          <el-icon :size="30"><Grid /></el-icon>
          <div class="action-label">班级管理</div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { School, User, Reading, Document, Connection, Grid } from '@element-plus/icons-vue'

const router = useRouter()

const stats = ref({
  totalSchools: 0,
  totalUsers: 0,
  totalCourses: 0,
  totalTemplates: 0
})

onMounted(() => {
  loadStats()
})

async function loadStats() {
  // TODO: 从API加载统计数据
  stats.value = {
    totalSchools: 156,
    totalUsers: 2840,
    totalCourses: 428,
    totalTemplates: 89
  }
}

function goToSchools() {
  router.push('/pbl/admin/schools')
}

function goToTemplates() {
  router.push('/pbl/admin/course-templates')
}

function goToChannels() {
  router.push('/pbl/admin/channel/partners')
}

function goToClasses() {
  router.push('/pbl/admin/classes')
}
</script>

<style scoped lang="scss">
.admin-dashboard-content {
  padding: 20px;

  h2 {
    font-size: 28px;
    color: #2c3e50;
    margin-bottom: 8px;
  }

  .subtitle {
    color: #666;
    font-size: 14px;
    margin-bottom: 30px;
  }

  h3 {
    font-size: 20px;
    color: #2c3e50;
    margin-bottom: 20px;
  }
}

.stats-row {
  margin-bottom: 30px;

  .stat-card {
    display: flex;
    align-items: center;
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 20px;
    transition: all 0.3s;

    &:hover {
      transform: translateY(-5px);
      box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
    }

    .stat-icon {
      width: 60px;
      height: 60px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-right: 15px;
    }

    .stat-info {
      flex: 1;

      .stat-value {
        font-size: 32px;
        font-weight: bold;
        color: #2c3e50;
        line-height: 1;
        margin-bottom: 5px;
      }

      .stat-label {
        font-size: 14px;
        color: #666;
      }
    }
  }

  .school-card .stat-icon {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
  }

  .user-card .stat-icon {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: white;
  }

  .course-card .stat-icon {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    color: white;
  }

  .template-card .stat-icon {
    background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
    color: white;
  }
}

.quick-actions {
  .action-card {
    text-align: center;
    padding: 30px 20px;
    cursor: pointer;
    transition: all 0.3s;
    border-radius: 12px;

    &:hover {
      transform: translateY(-5px);
      box-shadow: 0 8px 20px rgba(59, 130, 246, 0.2);
      border-color: #3b82f6;
    }

    .el-icon {
      color: #3b82f6;
      margin-bottom: 10px;
    }

    .action-label {
      font-size: 16px;
      color: #2c3e50;
      font-weight: 500;
    }
  }
}

@media (max-width: 768px) {
  .admin-dashboard-content {
    padding: 15px;

    h2 {
      font-size: 24px;
    }
  }

  .stats-row .stat-card {
    margin-bottom: 15px;
  }
}
</style>

