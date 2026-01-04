<template>
  <div class="channel-schools">
    <el-card class="header-card" shadow="never">
      <div class="header-content">
        <div>
          <h2 class="page-title">合作学校管理</h2>
          <p class="page-description">查看和管理您负责的合作学校</p>
        </div>
        <div class="header-stats">
          <el-statistic title="合作学校数" :value="schools.length" />
        </div>
      </div>
    </el-card>

    <el-card class="content-card" shadow="never" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span class="card-title">学校列表</span>
          <el-input
            v-model="searchText"
            placeholder="搜索学校名称"
            style="width: 300px"
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
      </template>

      <el-table
        :data="filteredSchools"
        style="width: 100%"
        :default-sort="{ prop: 'school_name', order: 'ascending' }"
      >
        <el-table-column prop="school_name" label="学校名称" min-width="200">
          <template #default="{ row }">
            <div class="school-name">
              <el-icon color="#409eff"><OfficeBuilding /></el-icon>
              <span>{{ row.school_name }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="total_courses" label="课程总数" width="120" align="center">
          <template #default="{ row }">
            <el-tag>{{ row.total_courses || 0 }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="total_students" label="学生总数" width="120" align="center">
          <template #default="{ row }">
            <el-tag type="success">{{ row.total_students || 0 }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="total_teachers" label="教师总数" width="120" align="center">
          <template #default="{ row }">
            <el-tag type="warning">{{ row.total_teachers || 0 }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '正常' : '已停用' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="150" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="viewSchoolCourses(row)"
              :icon="Reading"
            >
              查看课程
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="filteredSchools.length === 0 && !loading" class="empty-state">
        <el-empty description="暂无合作学校数据" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, OfficeBuilding, Reading } from '@element-plus/icons-vue'
import { getChannelSchools } from '../api'

const router = useRouter()

const loading = ref(false)
const schools = ref([])
const searchText = ref('')

const filteredSchools = computed(() => {
  if (!searchText.value) return schools.value
  return schools.value.filter(school => 
    school.school_name.toLowerCase().includes(searchText.value.toLowerCase())
  )
})

async function fetchSchools() {
  loading.value = true
  try {
    const response = await getChannelSchools()
    schools.value = response.data || []
  } catch (error) {
    console.error('获取学校列表失败:', error)
    ElMessage.error(error.message || '获取学校列表失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  // 搜索逻辑已通过computed实现
}

function viewSchoolCourses(school) {
  router.push({
    name: 'ChannelSchoolCourses',
    params: { schoolId: school.uuid }
  })
}

onMounted(() => {
  fetchSchools()
})
</script>

<style scoped lang="scss">
.channel-schools {
  .header-card {
    margin-bottom: 20px;
    
    .header-content {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .page-title {
        font-size: 24px;
        font-weight: 600;
        color: #2c3e50;
        margin: 0 0 8px 0;
      }
      
      .page-description {
        color: #909399;
        margin: 0;
      }
      
      .header-stats {
        display: flex;
        gap: 40px;
      }
    }
  }
  
  .content-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .card-title {
        font-size: 16px;
        font-weight: 600;
        color: #2c3e50;
      }
    }
    
    .school-name {
      display: flex;
      align-items: center;
      gap: 8px;
      
      span {
        font-weight: 500;
      }
    }
    
    .empty-state {
      padding: 40px 0;
    }
  }
}
</style>
