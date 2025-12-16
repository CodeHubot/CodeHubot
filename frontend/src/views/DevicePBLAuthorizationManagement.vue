<template>
  <div class="device-pbl-authorization-management">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon size="28" style="margin-right: 12px; vertical-align: middle;"><List /></el-icon>
        授权记录管理
      </h1>
      <p class="page-subtitle">查看和管理所有设备的PBL授权记录</p>
    </div>

    <!-- 搜索筛选 -->
    <el-card class="search-card" shadow="never">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="设备">
          <el-select
            v-model="searchForm.device_uuid"
            placeholder="选择设备"
            filterable
            clearable
            style="width: 300px"
            @change="handleSearch"
          >
            <el-option
              v-for="device in myDevices"
              :key="device.uuid"
              :label="`${device.name} (${device.uuid})`"
              :value="device.uuid"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select
            v-model="searchForm.status"
            placeholder="全部"
            clearable
            style="width: 150px"
            @change="handleSearch"
          >
            <el-option label="有效" value="active" />
            <el-option label="已过期" value="expired" />
            <el-option label="已停用" value="inactive" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 授权记录列表 -->
    <el-card class="table-card" shadow="never">
      <el-table
        :data="authorizations"
        v-loading="loading"
        style="width: 100%"
      >
        <el-table-column prop="device_name" label="设备名称" min-width="150">
          <template #default="{ row }">
            <div>
              <div style="font-weight: 500;">{{ row.device_name }}</div>
              <div style="font-size: 12px; color: #909399;">{{ row.device_uuid }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="group_name" label="小组名称" min-width="120" />
        <el-table-column prop="course_name" label="所属课程" min-width="150" />
        <el-table-column prop="class_name" label="所属班级" min-width="150" />
        <el-table-column prop="authorized_by_name" label="授权人" width="120" />
        <el-table-column prop="authorized_at" label="授权时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.authorized_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="expires_at" label="过期时间" width="180">
          <template #default="{ row }">
            <span v-if="row.expires_at">{{ formatDate(row.expires_at) }}</span>
            <el-tag v-else type="success" size="small">永久有效</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_expired" type="danger" size="small">已过期</el-tag>
            <el-tag v-else-if="row.is_active" type="success" size="small">有效</el-tag>
            <el-tag v-else type="info" size="small">已停用</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="notes" label="备注" min-width="150" show-overflow-tooltip />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              type="danger"
              link
              size="small"
              @click="handleRevoke(row)"
            >
              <el-icon><Delete /></el-icon>
              撤销
            </el-button>
            <el-button
              type="primary"
              link
              size="small"
              @click="viewDevice(row)"
            >
              <el-icon><View /></el-icon>
              查看设备
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadAuthorizations"
          @current-change="loadAuthorizations"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { List, Search, Delete, View } from '@element-plus/icons-vue'
import { getDevices } from '@/api/device'
import {
  getPBLDeviceAuthorizations,
  revokePBLDeviceAuthorization
} from '@/api/devicePBLAuthorizations'
import { useUserStore } from '@/store/user'

const router = useRouter()
const userStore = useUserStore()

// 数据
const myDevices = ref([])
const authorizations = ref([])
const loading = ref(false)

// 搜索表单
const searchForm = reactive({
  device_uuid: '',
  status: ''
})

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 加载我的设备列表
const loadMyDevices = async () => {
  try {
    const response = await getDevices({ page: 1, page_size: 1000 })
    const devices = response.data || response || []
    myDevices.value = Array.isArray(devices) ? devices.filter(device => device.user_id === userStore.user?.id) : []
  } catch (error) {
    console.error('加载设备列表失败:', error)
    ElMessage.error('加载设备列表失败')
  }
}

// 加载授权记录
const loadAuthorizations = async () => {
  if (!searchForm.device_uuid) {
    // 如果没有选择设备，显示所有设备的授权记录
    // 需要遍历所有设备获取授权记录
    authorizations.value = []
    pagination.total = 0
    ElMessage.warning('请先选择设备')
    return
  }

  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size
    }

    if (searchForm.status === 'active') {
      params.is_active = true
    } else if (searchForm.status === 'inactive') {
      params.is_active = false
    }

    const response = await getPBLDeviceAuthorizations(searchForm.device_uuid, params)
    const data = response.data || response
    
    authorizations.value = data.authorizations || []
    pagination.total = data.total || 0

    // 根据状态筛选
    if (searchForm.status === 'expired') {
      authorizations.value = authorizations.value.filter(auth => auth.is_expired)
    }
  } catch (error) {
    console.error('加载授权记录失败:', error)
    ElMessage.error('加载授权记录失败')
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  loadAuthorizations()
}

// 重置
const handleReset = () => {
  searchForm.device_uuid = ''
  searchForm.status = ''
  pagination.page = 1
  authorizations.value = []
  pagination.total = 0
}

// 撤销授权
const handleRevoke = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要撤销对"${row.group_name}"的授权吗？撤销后该小组的学生将无法再使用该设备。`,
      '确认撤销',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await revokePBLDeviceAuthorization(row.device_uuid || searchForm.device_uuid, row.id)
    ElMessage.success('授权已撤销')

    // 重新加载
    await loadAuthorizations()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('撤销授权失败:', error)
      ElMessage.error(error.response?.data?.detail || error.message || '撤销授权失败')
    }
  }
}

// 查看设备
const viewDevice = (row) => {
  router.push(`/device/${row.device_uuid}`)
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 初始化
onMounted(async () => {
  await loadMyDevices()
})
</script>

<style scoped lang="scss">
.device-pbl-authorization-management {
  padding: 20px;
  background: #f5f7fa;
  min-height: calc(100vh - 60px);

  .page-header {
    margin-bottom: 20px;

    .page-title {
      font-size: 24px;
      font-weight: 600;
      color: #303133;
      margin: 0 0 8px 0;
      display: flex;
      align-items: center;
    }

    .page-subtitle {
      font-size: 14px;
      color: #909399;
      margin: 0;
    }
  }

  .search-card,
  .table-card {
    background: #fff;
    border-radius: 8px;
    margin-bottom: 20px;
  }

  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
}
</style>
