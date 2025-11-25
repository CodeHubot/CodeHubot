<template>
  <div class="agents-container">
    <div class="page-header">
      <h2>智能体管理</h2>
    </div>

    <!-- 搜索和筛选 -->
    <div class="filter-section">
      <el-row :gutter="16">
        <el-col :span="10">
          <el-input
            v-model="searchQuery"
            placeholder="搜索智能体名称"
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="6">
          <el-select v-model="filterStatus" placeholder="状态筛选" clearable @change="loadAgents" style="width: 100%;">
            <el-option label="激活" :value="1" />
            <el-option label="禁用" :value="0" />
          </el-select>
        </el-col>
        <el-col :span="8" style="text-align: right;">
          <el-button @click="resetFilters">重置筛选</el-button>
          <el-button type="primary" icon="Plus" @click="addAgent">添加智能体</el-button>
        </el-col>
      </el-row>
    </div>

    <!-- 智能体列表 -->
    <el-table
      v-loading="loading"
      :data="agents"
      style="width: 100%"
    >
      <el-table-column prop="name" label="智能体名称" min-width="200" />
      <el-table-column prop="description" label="描述" min-width="250" show-overflow-tooltip />
      <el-table-column label="插件数量" width="120">
        <template #default="scope">
          <el-tag>{{ scope.row.plugin_ids?.length || 0 }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="80">
        <template #default="scope">
          <el-tag :type="scope.row.is_active === 1 ? 'success' : 'danger'">
            {{ scope.row.is_active === 1 ? '激活' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="160">
        <template #default="scope">
          {{ formatDate(scope.row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="类型" width="120">
        <template #default="scope">
          <el-tag :type="scope.row.is_system === 1 ? 'warning' : 'info'" size="small">
            {{ scope.row.is_system === 1 ? '系统内置' : '用户创建' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="scope">
          <el-button size="small" type="primary" @click="editAgent(scope.row)">编排</el-button>
          <el-button size="small" @click="quickEdit(scope.row)">快速编辑</el-button>
          <el-button
            size="small"
            type="danger"
            @click="handleDelete(scope.row)"
            :disabled="scope.row.is_system === 1"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :page-sizes="[10, 20, 50, 100]"
      :total="total"
      layout="total, sizes, prev, pager, next, jumper"
      @size-change="loadAgents"
      @current-change="loadAgents"
      style="margin-top: 20px; justify-content: flex-end;"
    />

    <!-- 快速添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
      @close="resetForm"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="智能体名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入智能体名称" />
        </el-form-item>
        <el-form-item label="简介" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="4"
            placeholder="请简要描述智能体的功能和用途"
          />
        </el-form-item>
        <el-alert
          v-if="!form.id"
          title="提示"
          type="info"
          :closable="false"
          show-icon
          style="margin-top: 10px;"
        >
          创建后可以在"编排"页面配置系统提示词和插件
        </el-alert>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ form.id ? '保存' : '创建并编排' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus } from '@element-plus/icons-vue'
import { getAgents, createAgent, updateAgent, deleteAgent } from '../api/agent'

const router = useRouter()

const loading = ref(false)
const searchQuery = ref('')
const filterStatus = ref(null)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const agents = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('添加智能体')
const submitting = ref(false)
const formRef = ref(null)

const form = reactive({
  id: null,
  name: '',
  description: ''
})

const rules = {
  name: [
    { required: true, message: '请输入智能体名称', trigger: 'blur' },
    { min: 1, max: 100, message: '长度在 1 到 100 个字符', trigger: 'blur' }
  ],
  description: [
    { max: 500, message: '描述最多500个字符', trigger: 'blur' }
  ]
}

// 加载智能体列表
const loadAgents = async () => {
  loading.value = true
  try {
    const params = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
      search: searchQuery.value || undefined,
      is_active: filterStatus.value !== null ? filterStatus.value : undefined
    }
    const response = await getAgents(params)
    agents.value = response.data.items || []
    total.value = response.data.total || 0
  } catch (error) {
    ElMessage.error('加载智能体列表失败')
  } finally {
    loading.value = false
  }
}

// 加载可用插件列表
const loadPlugins = async () => {
  try {
    const response = await getPlugins({ limit: 1000, is_active: 1 })
    availablePlugins.value = response.data.items || []
  } catch (error) {
    console.error('加载插件列表失败', error)
  }
}

// 搜索
const handleSearch = () => {
  currentPage.value = 1
  loadAgents()
}

// 重置筛选
const resetFilters = () => {
  searchQuery.value = ''
  filterStatus.value = null
  currentPage.value = 1
  loadAgents()
}

// 添加智能体（快速创建）
const addAgent = () => {
  dialogTitle.value = '添加智能体'
  resetForm()
  dialogVisible.value = true
}

// 跳转到编排页面
const editAgent = (row) => {
  router.push(`/agents/${row.id}/edit`)
}

// 快速编辑（名称和描述）
const quickEdit = (row) => {
  dialogTitle.value = '快速编辑'
  form.id = row.id
  form.name = row.name
  form.description = row.description || ''
  dialogVisible.value = true
}

// 删除智能体
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除智能体 "${row.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await deleteAgent(row.id)
    ElMessage.success('删除成功')
    loadAgents()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  
  submitting.value = true
  try {
    if (form.id) {
      // 快速编辑
      await updateAgent(form.id, {
        name: form.name,
        description: form.description
      })
      ElMessage.success('更新成功')
      dialogVisible.value = false
      loadAgents()
    } else {
      // 创建并跳转到编排页面
      const response = await createAgent({
        name: form.name,
        description: form.description
      })
      const newAgentId = response.data.id
      ElMessage.success('创建成功，正在跳转到编排页面...')
      dialogVisible.value = false
      // 跳转到编排页面
      router.push(`/agents/${newAgentId}/edit`)
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
    console.error(error)
  } finally {
    submitting.value = false
  }
}

// 重置表单
const resetForm = () => {
  form.id = null
  form.name = ''
  form.description = ''
  if (formRef.value) {
    formRef.value.clearValidate()
  }
}

// 格式化日期
const formatDate = (date) => {
  if (!date) return ''
  return new Date(date).toLocaleString('zh-CN')
}

onMounted(() => {
  loadAgents()
})
</script>

<style scoped>
.agents-container {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.filter-section {
  margin-bottom: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 4px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>

