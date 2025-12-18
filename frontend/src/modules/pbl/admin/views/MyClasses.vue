<template>
  <div class="my-classes">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>我的班级</span>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="班级名称">
          <el-input v-model="searchForm.name" placeholder="请输入班级名称" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 班级卡片列表 -->
      <el-row :gutter="24" v-loading="loading">
        <el-col 
          v-for="cls in classes" 
          :key="cls.id" 
          :xs="24" 
          :sm="12" 
          :md="8" 
          :lg="8"
          :xl="6"
          style="margin-bottom: 24px"
        >
          <el-card shadow="hover" class="class-card" @click="handleViewClass(cls)">
            <div class="class-header">
              <el-tag :type="getClassTypeTag(cls.class_type)" effect="dark">
                {{ getClassTypeName(cls.class_type) }}
              </el-tag>
            </div>
            <h3 class="class-name">{{ cls.name }}</h3>
            <p class="class-description">{{ cls.description || '暂无描述' }}</p>
            <div class="class-stats">
              <div class="stat-item">
                <el-icon><UserFilled /></el-icon>
                <span>{{ cls.current_members || 0 }} 人</span>
              </div>
              <div class="stat-item">
                <el-icon><Reading /></el-icon>
                <span>{{ cls.course_count || 0 }} 课程</span>
              </div>
            </div>
            <div class="class-footer">
              <el-button type="primary" text @click.stop="handleManage(cls)">
                管理班级
                <el-icon><ArrowRight /></el-icon>
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 空状态 -->
      <el-empty 
        v-if="!loading && classes.length === 0" 
        description="暂无班级数据"
      />

      <!-- 分页 -->
      <el-pagination
        v-if="classes.length > 0"
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[8, 16, 24, 32]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        style="margin-top: 20px; justify-content: flex-end;"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { UserFilled, Reading, ArrowRight } from '@element-plus/icons-vue'

const router = useRouter()

// 搜索表单
const searchForm = reactive({
  name: ''
})

// 表格数据
const classes = ref([])
const loading = ref(false)

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 8,
  total: 0
})

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    // TODO: 调用 API 获取数据
    classes.value = []
    pagination.total = 0
  } catch (error) {
    ElMessage.error('加载数据失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  loadData()
}

// 重置
const handleReset = () => {
  searchForm.name = ''
  handleSearch()
}

// 查看班级详情
const handleViewClass = (cls) => {
  router.push(`/pbl/admin/classes/${cls.uuid}`)
}

// 管理班级
const handleManage = (cls) => {
  router.push(`/pbl/admin/classes/${cls.uuid}/manage`)
}

// 分页改变
const handleSizeChange = (val) => {
  pagination.pageSize = val
  loadData()
}

const handleCurrentChange = (val) => {
  pagination.page = val
  loadData()
}

// 获取班级类型名称
const getClassTypeName = (type) => {
  const map = {
    regular: '普通班',
    project: '项目班',
    club: '社团班',
    interest: '兴趣班',
    competition: '竞赛班'
  }
  return map[type] || type
}

// 获取班级类型标签
const getClassTypeTag = (type) => {
  const map = {
    regular: 'info',
    project: 'success',
    club: 'primary',
    interest: 'warning',
    competition: 'danger'
  }
  return map[type] || 'info'
}

// 初始化
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.my-classes {
  padding: 0;
}

.card-header {
  font-size: 18px;
  font-weight: 600;
}

.search-form {
  margin-bottom: 24px;
}

.class-card {
  height: 280px;
  cursor: pointer;
  transition: all 0.3s;
  border-radius: 12px;
}

.class-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
}

.class-header {
  margin-bottom: 16px;
}

.class-name {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 12px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.class-description {
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
  margin: 0 0 16px 0;
  height: 44px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.class-stats {
  display: flex;
  gap: 20px;
  padding: 12px 0;
  border-top: 1px solid #f0f0f0;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #606266;
  font-size: 14px;
}

.class-footer {
  display: flex;
  justify-content: flex-end;
}
</style>


