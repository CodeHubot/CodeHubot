<template>
  <div class="class-progress-container">
    <!-- 返回按钮 -->
    <div class="page-header">
      <el-button @click="goBack" text>
        <el-icon><ArrowLeft /></el-icon>
        返回班级详情
      </el-button>
    </div>

    <!-- 页面标题 -->
    <el-card shadow="never" class="header-card">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">学习进度</h1>
          <p class="page-subtitle">{{ className }}</p>
        </div>
      </div>
    </el-card>

    <!-- 单元列表 -->
    <el-card shadow="never" class="units-card">
      <template #header>
        <div class="card-header">
          <span>学习单元列表</span>
          <span class="unit-count">共 {{ unitList.length }} 个单元</span>
        </div>
      </template>
      
      <div v-loading="loading" class="units-grid">
        <div 
          v-for="unit in unitList" 
          :key="unit.id" 
          class="unit-card"
          @click="viewUnitDetail(unit)"
        >
          <div class="unit-header">
            <h3>{{ unit.title }}</h3>
            <el-tag size="large">{{ unit.task_count }} 个任务</el-tag>
          </div>
          <div class="unit-order">
            <el-tag type="info" size="small">单元 {{ unit.order }}</el-tag>
          </div>
          <div class="unit-description">
            {{ unit.description || '暂无描述' }}
          </div>
          <div class="unit-footer">
            <el-button type="primary" link>
              查看详情
              <el-icon><ArrowRight /></el-icon>
            </el-button>
          </div>
        </div>
        
        <el-empty 
          v-if="!loading && unitList.length === 0" 
          description="暂无学习单元"
          style="grid-column: 1 / -1;"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import { getClubClassDetail } from '@pbl/admin/api/club'
import request from '@/utils/request'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const unitList = ref([])
const className = ref('')

// 加载班级名称
const loadClassName = async () => {
  try {
    const res = await getClubClassDetail(route.params.uuid)
    className.value = res.data.data.name
  } catch (error) {
    console.error('加载班级名称失败:', error)
  }
}

// 加载单元列表（极速）
const loadUnitList = async () => {
  loading.value = true
  try {
    const res = await request({
      url: `/admin/club/classes/${route.params.uuid}/progress/units`,
      method: 'get'
    })
    unitList.value = res.data.data || []
  } catch (error) {
    ElMessage.error(error.message || '加载单元列表失败')
  } finally {
    loading.value = false
  }
}

// 查看单元详情
const viewUnitDetail = (unit) => {
  router.push(`/pbl/admin/classes/${route.params.uuid}/progress/units/${unit.id}`)
}

const goBack = () => {
  router.push(`/pbl/admin/classes/${route.params.uuid}`)
}

onMounted(async () => {
  await loadClassName()
  await loadUnitList()
})
</script>

<style scoped lang="scss">
.class-progress-container {
  padding: 24px;
  background: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.page-header {
  margin-bottom: 24px;
}

.header-card {
  margin-bottom: 24px;
  border-radius: 12px;
  
  .header-content {
    .header-left {
      .page-title {
        margin: 0 0 8px 0;
        font-size: 24px;
        font-weight: 600;
        color: #303133;
      }
      
      .page-subtitle {
        margin: 0;
        font-size: 14px;
        color: #909399;
      }
    }
  }
}

.units-card {
  border-radius: 12px;
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 16px;
    font-weight: 600;
    
    .unit-count {
      font-size: 14px;
      color: #909399;
      font-weight: normal;
    }
  }
}

.units-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
  padding: 20px 0;
}

.unit-card {
  border: 2px solid #e4e7ed;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #fff;
  
  &:hover {
    border-color: #409eff;
    box-shadow: 0 4px 16px 0 rgba(64, 158, 255, 0.25);
    transform: translateY(-4px);
  }
  
  .unit-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 8px;
    
    h3 {
      margin: 0;
      font-size: 18px;
      font-weight: 600;
      color: #303133;
      flex: 1;
      margin-right: 12px;
    }
  }
  
  .unit-order {
    margin-bottom: 12px;
  }
  
  .unit-description {
    font-size: 14px;
    color: #606266;
    line-height: 1.6;
    min-height: 44px;
    margin-bottom: 16px;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }
  
  .unit-footer {
    border-top: 1px solid #f0f0f0;
    padding-top: 12px;
    text-align: right;
  }
}
</style>
