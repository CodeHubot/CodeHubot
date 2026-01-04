<template>
  <div class="admin-users-content">
    <h2>用户管理</h2>
    <p class="subtitle">管理平台所有用户</p>

    <!-- 搜索和筛选 -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true">
        <el-form-item label="搜索用户">
          <el-input
            v-model="searchQuery"
            placeholder="输入用户名、邮箱搜索"
            clearable
            style="width: 250px"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="roleFilter" placeholder="全部角色" clearable style="width: 150px">
            <el-option label="全部" value="" />
            <el-option label="学生" value="student" />
            <el-option label="教师" value="teacher" />
            <el-option label="学校管理员" value="school_admin" />
            <el-option label="平台管理员" value="platform_admin" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon> 搜索
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 用户表格 -->
    <el-card class="table-card" shadow="never">
      <el-table :data="users" style="width: 100%" v-loading="loading">
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="email" label="邮箱" width="200" />
        <el-table-column prop="full_name" label="姓名" width="120" />
        <el-table-column label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="getRoleTagType(row.role)">
              {{ getRoleText(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="school_name" label="所属学校" width="180" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="150">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleView(row)">
              查看
            </el-button>
            <el-button link type="primary" size="small" @click="handleEdit(row)">
              编辑
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSearch"
        @current-change="handleSearch"
        class="pagination"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const searchQuery = ref('')
const roleFilter = ref('')

const users = ref([])
const pagination = ref({
  page: 1,
  pageSize: 20,
  total: 0
})

onMounted(() => {
  loadUsers()
})

async function loadUsers() {
  loading.value = true
  try {
    // TODO: 调用真实API
    // 模拟数据
    users.value = [
      {
        id: 1,
        username: 'admin',
        email: 'admin@example.com',
        full_name: '系统管理员',
        role: 'platform_admin',
        school_name: '-',
        is_active: true,
        created_at: '2024-01-01T00:00:00'
      }
    ]
    pagination.value.total = 100
  } catch (error) {
    ElMessage.error('加载用户列表失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.value.page = 1
  loadUsers()
}

function handleReset() {
  searchQuery.value = ''
  roleFilter.value = ''
  handleSearch()
}

function handleView(row) {
  ElMessage.info(`查看用户: ${row.username}`)
}

function handleEdit(row) {
  ElMessage.info(`编辑用户: ${row.username}`)
}

function getRoleText(role) {
  const roleMap = {
    student: '学生',
    teacher: '教师',
    school_admin: '学校管理员',
    platform_admin: '平台管理员',
    channel_partner: '渠道商'
  }
  return roleMap[role] || role
}

function getRoleTagType(role) {
  const typeMap = {
    student: '',
    teacher: 'success',
    school_admin: 'warning',
    platform_admin: 'danger',
    channel_partner: 'info'
  }
  return typeMap[role] || ''
}

function formatDate(dateString) {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}
</script>

<style scoped lang="scss">
.admin-users-content {
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

  .filter-card {
    margin-bottom: 20px;
  }

  .table-card {
    .pagination {
      margin-top: 20px;
      display: flex;
      justify-content: flex-end;
    }
  }
}
</style>

