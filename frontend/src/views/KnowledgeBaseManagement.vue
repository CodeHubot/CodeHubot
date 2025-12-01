<template>
  <div class="knowledge-base-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span><el-icon><Collection /></el-icon> 知识库管理</span>
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>
            创建知识库
          </el-button>
        </div>
      </template>

      <!-- 搜索筛选 -->
      <div class="search-bar">
        <el-input
          v-model="searchParams.keyword"
          placeholder="搜索知识库..."
          clearable
          style="width: 300px"
          @change="loadKnowledgeBases"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-select
          v-model="searchParams.scope_type"
          placeholder="作用域类型"
          clearable
          style="width: 150px; margin-left: 10px"
          @change="loadKnowledgeBases"
        >
          <el-option label="全部" value="" />
          <el-option label="系统级" value="system" />
          <el-option label="学校级" value="school" />
          <el-option label="课程级" value="course" />
          <el-option label="智能体级" value="agent" />
        </el-select>
      </div>

      <!-- 知识库列表（卡片视图） -->
      <div v-loading="loading" class="kb-grid">
        <el-card
          v-for="kb in knowledgeBases"
          :key="kb.uuid"
          class="kb-card"
          shadow="hover"
          @click="viewKnowledgeBase(kb)"
        >
          <div class="kb-card-header">
            <el-icon :size="40" color="#409EFF">
              <component :is="getScopeIcon(kb.scope_type)" />
            </el-icon>
            <el-tag :type="getScopeTagType(kb.scope_type)" size="small">
              {{ getScopeLabel(kb.scope_type) }}
            </el-tag>
          </div>

          <h3 class="kb-title">{{ kb.name }}</h3>
          <p class="kb-description">{{ kb.description || '暂无描述' }}</p>

          <div class="kb-stats">
            <el-statistic title="文档" :value="kb.document_count || 0" />
            <el-statistic title="文本块" :value="kb.chunk_count || 0" />
            <div class="stat-item">
              <span class="stat-title">大小</span>
              <span class="stat-value">{{ formatSize(kb.total_size) }}</span>
            </div>
          </div>

          <div class="kb-footer">
            <span class="kb-owner">{{ kb.owner_name }}</span>
            <span class="kb-time">{{ formatTime(kb.created_at) }}</span>
          </div>

          <div class="kb-actions" @click.stop>
            <el-button size="small" type="primary" link @click="viewKnowledgeBase(kb)">
              查看
            </el-button>
            <el-button size="small" type="info" link @click="editKnowledgeBase(kb)">
              编辑
            </el-button>
            <el-button size="small" type="danger" link @click="confirmDelete(kb)">
              删除
            </el-button>
          </div>
        </el-card>
      </div>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[12, 24, 48]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadKnowledgeBases"
        @current-change="loadKnowledgeBases"
      />
    </el-card>

    <!-- 创建/编辑对话框（简化版） -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingKb ? '编辑知识库' : '创建知识库'"
      width="600px"
    >
      <el-form :model="formData" label-width="100px">
        <el-form-item label="名称" required>
          <el-input v-model="formData.name" placeholder="请输入知识库名称" />
        </el-form-item>

        <el-form-item label="描述">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入知识库描述"
          />
        </el-form-item>

        <el-form-item label="作用域类型" required>
          <el-select 
            v-model="formData.scope_type" 
            placeholder="请选择" 
            style="width: 100%"
            @change="handleScopeTypeChange"
          >
            <el-option label="系统级" value="system" v-if="userRole === 'platform_admin'" />
            <el-option label="学校级" value="school" v-if="['platform_admin', 'school_admin'].includes(userRole)" />
            <el-option label="课程级" value="course" v-if="['platform_admin', 'school_admin', 'teacher'].includes(userRole)" />
            <!-- 暂时隐藏智能体级，未来如有多智能体需求再开放 -->
            <!-- <el-option label="智能体级" value="agent" /> -->
            <el-option label="个人级" value="personal" />
          </el-select>
        </el-form-item>

        <el-form-item label="可见范围">
          <el-alert :title="getScopeHint()" type="info" :closable="false" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Collection,
  Plus,
  Search,
  Document,
  School,
  Grid,
  User
} from '@element-plus/icons-vue'
import {
  getKnowledgeBases,
  createKnowledgeBase,
  updateKnowledgeBase,
  deleteKnowledgeBase
} from '@/api/knowledgeBases'
import { useUserStore } from '@/store/user'

const router = useRouter()
const userStore = useUserStore()

// 用户信息
const userRole = computed(() => userStore.userInfo?.role || '')
const userId = computed(() => userStore.userInfo?.id || null)
const schoolId = computed(() => userStore.userInfo?.school_id || null)

// 数据
const loading = ref(false)
const knowledgeBases = ref([])
const showCreateDialog = ref(false)
const editingKb = ref(null)

const searchParams = reactive({
  keyword: '',
  scope_type: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 12,
  total: 0
})

const formData = reactive({
  name: '',
  description: '',
  scope_type: 'personal',  // 默认个人级
  scope_id: null,
  // access_level 移除，由后端根据 scope_type 自动设置
  chunk_size: 500,          // 系统默认值
  chunk_overlap: 50,        // 系统默认值
  tags: []
})

// 初始化默认scope_type
const initDefaultScopeType = () => {
  if (userRole.value === 'platform_admin') {
    formData.scope_type = 'system'
  } else if (userRole.value === 'school_admin') {
    formData.scope_type = 'school'
    formData.scope_id = schoolId.value
  } else if (userRole.value === 'teacher') {
    formData.scope_type = 'personal'
    formData.scope_id = userId.value
  } else {
    formData.scope_type = 'personal'
    formData.scope_id = userId.value
  }
}

// 方法
const loadKnowledgeBases = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...searchParams
    }

    const response = await getKnowledgeBases(params)
    const data = response.data || response

    knowledgeBases.value = data.knowledge_bases || []
    pagination.total = data.total || 0
  } catch (error) {
    ElMessage.error('加载知识库列表失败')
  } finally {
    loading.value = false
  }
}

const getScopeIcon = (scopeType) => {
  const iconMap = {
    system: Grid,
    school: School,
    course: Document,
    agent: User
  }
  return iconMap[scopeType] || Document
}

const getScopeTagType = (scopeType) => {
  const typeMap = {
    system: 'danger',
    school: 'warning',
    course: 'success',
    agent: 'info'
  }
  return typeMap[scopeType] || 'info'
}

const getScopeLabel = (scopeType) => {
  const labelMap = {
    system: '系统',
    school: '学校',
    course: '课程',
    agent: '智能体'
  }
  return labelMap[scopeType] || scopeType
}

const formatSize = (bytes) => {
  if (!bytes) return '0B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + sizes[i]
}

const formatTime = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

const handleScopeTypeChange = (scopeType) => {
  // 根据scope_type自动设置scope_id
  switch (scopeType) {
    case 'system':
      formData.scope_id = null
      break
    case 'school':
      formData.scope_id = schoolId.value
      break
    case 'personal':
      formData.scope_id = userId.value
      break
    case 'course':
    case 'agent':
      // 这些需要用户后续选择，暂时设为null
      formData.scope_id = null
      break
  }
}

const getScopeHint = () => {
  const hints = {
    system: '✅ 所有人可见 | 仅平台管理员可创建',
    school: `✅ 本校师生可见${schoolId.value ? ' | 自动关联到您所在的学校' : ''}`,
    course: '✅ 课程师生可见 | 需要选择具体课程',
    personal: '✅ 仅您本人可见 | 其他人无法访问'
  }
  return hints[formData.scope_type] || '请选择作用域类型'
}

const viewKnowledgeBase = (kb) => {
  router.push(`/knowledge-bases/${kb.uuid}`)
}

const editKnowledgeBase = (kb) => {
  editingKb.value = kb
  Object.assign(formData, {
    name: kb.name,
    description: kb.description,
    scope_type: kb.scope_type,
    scope_id: kb.scope_id,
    access_level: kb.access_level
  })
  showCreateDialog.value = true
}

const handleSubmit = async () => {
  if (!formData.name) {
    ElMessage.warning('请输入知识库名称')
    return
  }

  // 自动设置scope_id（根据scope_type）
  const submitData = { ...formData }
  
  switch (submitData.scope_type) {
    case 'system':
      submitData.scope_id = null
      break
    case 'school':
      submitData.scope_id = schoolId.value
      if (!submitData.scope_id) {
        ElMessage.warning('您未归属任何学校，无法创建学校级知识库')
        return
      }
      break
    case 'personal':
      submitData.scope_id = userId.value
      break
    case 'course':
    case 'agent':
      if (!submitData.scope_id) {
        ElMessage.warning(`请选择具体的${submitData.scope_type === 'course' ? '课程' : '智能体'}`)
        return
      }
      break
  }

  try {
    if (editingKb.value) {
      await updateKnowledgeBase(editingKb.value.uuid, submitData)
      ElMessage.success('知识库更新成功')
    } else {
      await createKnowledgeBase(submitData)
      ElMessage.success('知识库创建成功')
    }

    showCreateDialog.value = false
    editingKb.value = null
    loadKnowledgeBases()
  } catch (error) {
    ElMessage.error(editingKb.value ? '更新失败' : '创建失败')
  }
}

const confirmDelete = (kb) => {
  // 检查是否为系统知识库
  if (kb.is_system) {
    ElMessage.warning('系统内置知识库不能删除')
    return
  }

  ElMessageBox.confirm(
    `确定要删除知识库"${kb.name}"吗？`, 
    '确认删除', 
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
      dangerouslyUseHTMLString: true,
      message: `
        <div>
          <p><strong>知识库：</strong>${kb.name}</p>
          <p><strong>文档数：</strong>${kb.document_count || 0}</p>
          <p><strong>文本块数：</strong>${kb.chunk_count || 0}</p>
          <p style="color: #E6A23C; margin-top: 10px">
            ⚠️ 注意：删除知识库不会删除其中的文档数据
          </p>
        </div>
      `
    }
  ).then(async () => {
    try {
      console.log('[知识库删除] 开始删除:', kb.uuid)
      await deleteKnowledgeBase(kb.uuid, false)
      ElMessage.success('知识库已删除')
      console.log('[知识库删除] 删除成功，重新加载列表')
      await loadKnowledgeBases()
    } catch (error) {
      console.error('[知识库删除] 删除失败:', error)
      const errorMsg = error.response?.data?.message || error.message || '删除失败，请稍后重试'
      ElMessage.error(`删除失败：${errorMsg}`)
    }
  }).catch(() => {
    // 用户点击取消或关闭，不做任何操作
    console.log('[知识库删除] 用户取消删除')
  })
}

onMounted(() => {
  initDefaultScopeType()
  loadKnowledgeBases()
})
</script>

<style scoped>
.knowledge-base-management {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-bar {
  margin-bottom: 20px;
}

.kb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin: 20px 0;
}

.kb-card {
  cursor: pointer;
  transition: all 0.3s;
}

.kb-card:hover {
  transform: translateY(-5px);
}

.kb-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.kb-title {
  font-size: 18px;
  font-weight: bold;
  margin: 10px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.kb-description {
  color: #666;
  font-size: 14px;
  height: 40px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.kb-stats {
  display: flex;
  justify-content: space-around;
  margin: 15px 0;
  padding: 15px 0;
  border-top: 1px solid #eee;
  border-bottom: 1px solid #eee;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.stat-title {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin-bottom: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  line-height: 32px;
}

.kb-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #999;
  margin-top: 10px;
}

.kb-actions {
  display: flex;
  justify-content: space-around;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #eee;
}

.el-pagination {
  margin-top: 20px;
  justify-content: center;
}
</style>

