<template>
  <div class="admin-analytics-content">
    <h2>数据统计</h2>
    <p class="subtitle">平台数据分析与统计</p>

    <!-- 时间范围选择 -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true">
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 300px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleQuery">
            <el-icon><Search /></el-icon> 查询
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-header">
            <span>今日新增用户</span>
            <el-icon color="#3b82f6"><User /></el-icon>
          </div>
          <div class="stat-value">{{ stats.newUsersToday }}</div>
          <div class="stat-trend">
            <el-icon color="#67c23a"><CaretTop /></el-icon>
            <span class="trend-up">较昨日 +12%</span>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-header">
            <span>活跃学校</span>
            <el-icon color="#f56c6c"><School /></el-icon>
          </div>
          <div class="stat-value">{{ stats.activeSchools }}</div>
          <div class="stat-trend">
            <el-icon color="#67c23a"><CaretTop /></el-icon>
            <span class="trend-up">较昨日 +5%</span>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-header">
            <span>课程完成率</span>
            <el-icon color="#e6a23c"><Reading /></el-icon>
          </div>
          <div class="stat-value">{{ stats.courseCompletionRate }}%</div>
          <div class="stat-trend">
            <el-icon color="#f56c6c"><CaretBottom /></el-icon>
            <span class="trend-down">较昨日 -2%</span>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-header">
            <span>系统在线人数</span>
            <el-icon color="#909399"><UserFilled /></el-icon>
          </div>
          <div class="stat-value">{{ stats.onlineUsers }}</div>
          <div class="stat-trend">
            <span class="trend-stable">实时数据</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card class="chart-card">
          <div class="chart-header">
            <h3>用户增长趋势</h3>
            <el-radio-group v-model="timeRange" size="small">
              <el-radio-button label="week">近7天</el-radio-button>
              <el-radio-button label="month">近30天</el-radio-button>
              <el-radio-button label="year">近一年</el-radio-button>
            </el-radio-group>
          </div>
          <div class="chart-placeholder">
            <el-empty description="图表数据加载中..." />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :xs="24" :md="12">
        <el-card class="chart-card">
          <h3>用户角色分布</h3>
          <div class="chart-placeholder">
            <el-empty description="图表数据加载中..." />
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="12">
        <el-card class="chart-card">
          <h3>课程类型分布</h3>
          <div class="chart-placeholder">
            <el-empty description="图表数据加载中..." />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Search, User, School, Reading, UserFilled, CaretTop, CaretBottom } from '@element-plus/icons-vue'

const dateRange = ref([])
const timeRange = ref('week')

const stats = ref({
  newUsersToday: 0,
  activeSchools: 0,
  courseCompletionRate: 0,
  onlineUsers: 0
})

onMounted(() => {
  loadStats()
})

async function loadStats() {
  // TODO: 从API加载统计数据
  stats.value = {
    newUsersToday: 248,
    activeSchools: 89,
    courseCompletionRate: 76.5,
    onlineUsers: 1523
  }
}

function handleQuery() {
  loadStats()
}
</script>

<style scoped lang="scss">
.admin-analytics-content {
  padding: 20px;

  h2 {
    font-size: 28px;
    color: #2c3e50;
    margin-bottom: 8px;
  }

  .subtitle {
    color: #666;
    font-size: 14px;
    margin-bottom: 20px;
  }

  h3 {
    font-size: 18px;
    color: #2c3e50;
    margin-bottom: 15px;
  }

  .filter-card {
    margin-bottom: 20px;
  }

  .stats-row {
    margin-bottom: 20px;

    .stat-card {
      padding: 20px;
      margin-bottom: 20px;

      .stat-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
        font-size: 14px;
        color: #666;

        .el-icon {
          font-size: 24px;
        }
      }

      .stat-value {
        font-size: 32px;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 10px;
      }

      .stat-trend {
        display: flex;
        align-items: center;
        gap: 5px;
        font-size: 12px;

        .trend-up {
          color: #67c23a;
        }

        .trend-down {
          color: #f56c6c;
        }

        .trend-stable {
          color: #909399;
        }
      }
    }
  }

  .chart-card {
    padding: 20px;
    margin-bottom: 20px;

    .chart-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
    }

    .chart-placeholder {
      height: 300px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #f5f7fa;
      border-radius: 8px;
    }
  }
}
</style>

