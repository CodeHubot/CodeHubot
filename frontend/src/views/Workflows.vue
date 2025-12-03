<template>
  <div class="workflows-container">
    <div class="page-header">
      <h2>工作流管理</h2>
    </div>

    <!-- 搜索和筛选 -->
    <div class="filter-section">
      <el-row :gutter="16">
        <el-col :span="10">
          <el-input
            v-model="searchQuery"
            placeholder="搜索工作流名称"
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="6">
          <el-select v-model="filterStatus" placeholder="状态筛选" clearable @change="loadWorkflows" style="width: 100%;">
            <el-option label="激活" :value="1" />
            <el-option label="禁用" :value="0" />
          </el-select>
        </el-col>
        <el-col :span="8" style="text-align: right;">
          <el-button @click="resetFilters">重置筛选</el-button>
          <el-button type="primary" icon="Plus" @click="createWorkflow">创建工作流</el-button>
        </el-col>
      </el-row>
    </div>

    <!-- 工作流列表 -->
    <div v-loading="loading" class="workflows-table">
      <el-table :data="workflows" style="width: 100%">
        <el-table-column prop="name" label="工作流名称" min-width="200" />
        <el-table-column prop="description" label="描述" min-width="250" show-overflow-tooltip />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active === 1 ? 'success' : 'info'" size="small">
              {{ row.is_active === 1 ? '激活' : '禁用' }}
            </el-tag>
            <el-tag v-if="row.is_public === 1" type="warning" size="small" style="margin-left: 5px;">公开</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="执行统计" width="150">
          <template #default="{ row }">
            <span>执行: {{ row.execution_count }}</span>
            <span style="margin-left: 10px; color: #67c23a;">成功: {{ row.success_count }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="editWorkflow(row)">编辑</el-button>
            <el-button type="success" size="small" @click="executeWorkflow(row)">执行</el-button>
            <el-button type="info" size="small" @click="viewExecutions(row)">执行历史</el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页 -->
    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :page-sizes="[10, 20, 50, 100]"
      :total="total"
      layout="total, sizes, prev, pager, next, jumper"
      @size-change="loadWorkflows"
      @current-change="loadWorkflows"
      style="margin-top: 20px; justify-content: flex-end;"
    />

    <!-- 执行对话框 -->
    <el-dialog
      v-model="executeDialogVisible"
      title="执行工作流"
      width="500px"
    >
      <el-form :model="executeForm" label-width="100px">
        <el-form-item label="输入参数">
          <el-input
            v-model="executeForm.inputJson"
            type="textarea"
            :rows="6"
            placeholder='请输入JSON格式的输入参数，例如：{"query": "你好"}'
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="executeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmExecute" :loading="executing">执行</el-button>
      </template>
    </el-dialog>

    <!-- 执行历史对话框 -->
    <el-dialog
      v-model="executionsDialogVisible"
      title="执行历史"
      width="80%"
    >
      <el-table :data="executions" style="width: 100%">
        <el-table-column prop="execution_id" label="执行ID" width="200" />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="execution_time" label="执行时间(ms)" width="150" />
        <el-table-column prop="started_at" label="开始时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.started_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="completed_at" label="完成时间" width="180">
          <template #default="{ row }">
            {{ row.completed_at ? formatDate(row.completed_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="viewExecutionDetail(row)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 执行详情对话框 -->
    <el-dialog
      v-model="executionDetailVisible"
      title="执行详情"
      width="70%"
    >
      <div v-if="executionDetail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="执行ID">{{ executionDetail.execution_id }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(executionDetail.status)" size="small">
              {{ getStatusText(executionDetail.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="执行时间">{{ executionDetail.execution_time }}ms</el-descriptions-item>
          <el-descriptions-item label="开始时间">{{ formatDate(executionDetail.started_at) }}</el-descriptions-item>
          <el-descriptions-item label="完成时间" :span="2">
            {{ executionDetail.completed_at ? formatDate(executionDetail.completed_at) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="输入参数" :span="2">
            <pre>{{ JSON.stringify(executionDetail.input, null, 2) }}</pre>
          </el-descriptions-item>
          <el-descriptions-item label="输出结果" :span="2">
            <pre>{{ JSON.stringify(executionDetail.output, null, 2) }}</pre>
          </el-descriptions-item>
          <el-descriptions-item v-if="executionDetail.error_message" label="错误信息" :span="2">
            <el-alert type="error" :closable="false">{{ executionDetail.error_message }}</el-alert>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus } from '@element-plus/icons-vue'
import {
  getWorkflows,
  deleteWorkflow,
  executeWorkflow as executeWorkflowAPI,
  getExecutions,
  getExecution
} from '@/api/workflow'

const router = useRouter()

// 数据
const loading = ref(false)
const workflows = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchQuery = ref('')
const filterStatus = ref(null)

// 执行相关
const executeDialogVisible = ref(false)
const executeForm = ref({
  inputJson: '{}'
})
const executing = ref(false)
const currentWorkflow = ref(null)

// 执行历史
const executionsDialogVisible = ref(false)
const executions = ref([])
const executionDetailVisible = ref(false)
const executionDetail = ref(null)

// 加载工作流列表
const loadWorkflows = async () => {
  loading.value = true
  try {
    const params = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value
    }
    if (searchQuery.value) {
      params.search = searchQuery.value
    }
    if (filterStatus.value !== null) {
      params.is_active = filterStatus.value
    }
    
    const response = await getWorkflows(params)
    workflows.value = response.data.items || []
    total.value = response.data.total || 0
  } catch (error) {
    ElMessage.error('加载工作流列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  currentPage.value = 1
  loadWorkflows()
}

// 重置筛选
const resetFilters = () => {
  searchQuery.value = ''
  filterStatus.value = null
  currentPage.value = 1
  loadWorkflows()
}

// 创建工作流
const createWorkflow = () => {
  router.push('/workflows/editor')
}

// 编辑工作流
const editWorkflow = (workflow) => {
  router.push(`/workflows/editor/${workflow.uuid}`)
}

// 执行工作流
const executeWorkflow = (workflow) => {
  currentWorkflow.value = workflow
  executeForm.value.inputJson = '{}'
  executeDialogVisible.value = true
}

// 确认执行
const confirmExecute = async () => {
  try {
    const input = JSON.parse(executeForm.value.inputJson)
    executing.value = true
    
    const response = await executeWorkflowAPI(currentWorkflow.value.uuid, {
      input,
      async_execution: true
    })
    
    ElMessage.success('工作流执行已提交')
    executeDialogVisible.value = false
    
    // 跳转到执行详情页面或显示执行状态
    if (response.data.execution_id) {
      viewExecutionDetail({ execution_id: response.data.execution_id })
    }
  } catch (error) {
    if (error.message.includes('JSON')) {
      ElMessage.error('输入参数格式错误，请输入有效的JSON')
    } else {
      ElMessage.error('执行工作流失败: ' + (error.response?.data?.message || error.message))
    }
  } finally {
    executing.value = false
  }
}

// 查看执行历史
const viewExecutions = async (workflow) => {
  executionsDialogVisible.value = true
  try {
    const response = await getExecutions({
      workflow_uuid: workflow.uuid,
      limit: 50
    })
    executions.value = response.data.items || []
  } catch (error) {
    ElMessage.error('加载执行历史失败')
    console.error(error)
  }
}

// 查看执行详情
const viewExecutionDetail = async (execution) => {
  try {
    const response = await getExecution(execution.execution_id)
    executionDetail.value = response.data
    executionDetailVisible.value = true
  } catch (error) {
    ElMessage.error('加载执行详情失败')
    console.error(error)
  }
}

// 删除工作流
const handleDelete = async (workflow) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除工作流 "${workflow.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await deleteWorkflow(workflow.uuid)
    ElMessage.success('删除成功')
    loadWorkflows()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + (error.response?.data?.message || error.message))
    }
  }
}

// 格式化日期
const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}

// 获取状态类型
const getStatusType = (status) => {
  const types = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return types[status] || 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  const texts = {
    pending: '等待中',
    running: '执行中',
    completed: '已完成',
    failed: '失败'
  }
  return texts[status] || status
}

onMounted(() => {
  loadWorkflows()
})
</script>

<style scoped>
.workflows-container {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 500;
}

.filter-section {
  margin-bottom: 20px;
}

.workflows-table {
  margin-bottom: 20px;
}
</style>

