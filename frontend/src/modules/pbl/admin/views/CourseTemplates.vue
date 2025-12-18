<template>
  <div class="course-templates">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>课程模板管理</span>
          <el-button type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            新建模板
          </el-button>
        </div>
      </template>

      <!-- 筛选条件 -->
      <el-form :inline="true" class="filter-form">
        <el-form-item label="搜索">
          <el-input 
            v-model="filters.search" 
            placeholder="模板名称或编码" 
            clearable
            style="width: 250px"
            @keyup.enter="loadTemplates"
          />
        </el-form-item>
        <el-form-item label="分类">
          <el-select 
            v-model="filters.category" 
            placeholder="请选择分类" 
            clearable 
            style="width: 150px"
          >
            <el-option label="人工智能" value="人工智能" />
            <el-option label="机器学习" value="机器学习" />
            <el-option label="数据科学" value="数据科学" />
            <el-option label="物联网" value="物联网" />
            <el-option label="机器人" value="机器人" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="难度">
          <el-select 
            v-model="filters.difficulty" 
            placeholder="请选择难度" 
            clearable 
            style="width: 150px"
          >
            <el-option label="初级" value="beginner" />
            <el-option label="中级" value="intermediate" />
            <el-option label="高级" value="advanced" />
          </el-select>
        </el-form-item>
        <el-form-item label="公开状态">
          <el-select 
            v-model="filters.is_public" 
            placeholder="请选择状态" 
            clearable 
            style="width: 150px"
          >
            <el-option label="公开" :value="1" />
            <el-option label="私有" :value="0" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadTemplates">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="resetFilters">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 模板列表表格 -->
      <el-table
        :data="templates"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="template_code" label="模板编码" width="150" />
        <el-table-column prop="title" label="模板名称" width="200" />
        <el-table-column prop="category" label="分类" width="120" />
        <el-table-column label="难度" width="100">
          <template #default="{ row }">
            <el-tag 
              :type="row.difficulty === 'beginner' ? 'success' : row.difficulty === 'intermediate' ? 'warning' : 'danger'"
              size="small"
            >
              {{ difficultyMap[row.difficulty] || row.difficulty }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="公开状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_public ? 'success' : 'info'" size="small">
              {{ row.is_public ? '公开' : '私有' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="usage_count" label="使用次数" width="100" />
        <el-table-column prop="version" label="版本" width="100" />
        <el-table-column prop="duration" label="课时" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <el-button type="success" size="small" @click="handleManageContent(row)">
              <el-icon><FolderOpened /></el-icon>
              管理内容
            </el-button>
            <el-button type="primary" size="small" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-popconfirm
              title="确定删除此模板吗？"
              @confirm="handleDelete(row)"
            >
              <template #reference>
                <el-button type="danger" size="small">
                  删除
                </el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadTemplates"
          @current-change="loadTemplates"
        />
      </div>
    </el-card>

    <!-- 创建/编辑模板对话框 -->
    <el-dialog
      v-model="templateDialogVisible"
      :title="editingTemplate ? '编辑课程模板' : '新建课程模板'"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="templateFormRef"
        :model="templateForm"
        :rules="templateRules"
        label-width="120px"
      >
        <el-form-item label="模板编码" prop="template_code">
          <el-input 
            v-model="templateForm.template_code" 
            placeholder="请输入模板编码，如：AI-ML-001"
            :disabled="!!editingTemplate"
          />
        </el-form-item>
        
        <el-form-item label="模板名称" prop="title">
          <el-input 
            v-model="templateForm.title" 
            placeholder="请输入模板名称"
          />
        </el-form-item>
        
        <el-form-item label="分类" prop="category">
          <el-select 
            v-model="templateForm.category" 
            placeholder="请选择分类" 
            style="width: 100%"
          >
            <el-option label="人工智能" value="人工智能" />
            <el-option label="机器学习" value="机器学习" />
            <el-option label="数据科学" value="数据科学" />
            <el-option label="物联网" value="物联网" />
            <el-option label="机器人" value="机器人" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="难度等级" prop="difficulty">
          <el-radio-group v-model="templateForm.difficulty">
            <el-radio label="beginner">初级</el-radio>
            <el-radio label="intermediate">中级</el-radio>
            <el-radio label="advanced">高级</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="课时" prop="duration">
          <el-input 
            v-model="templateForm.duration" 
            placeholder="如：12周、24课时等"
          />
        </el-form-item>
        
        <el-form-item label="版本号" prop="version">
          <el-input 
            v-model="templateForm.version" 
            placeholder="如：1.0.0"
          />
        </el-form-item>
        
        <el-form-item label="封面图片">
          <el-input 
            v-model="templateForm.cover_image" 
            placeholder="请输入图片URL"
          />
        </el-form-item>
        
        <el-form-item label="公开状态" prop="is_public">
          <el-radio-group v-model="templateForm.is_public">
            <el-radio :label="1">公开</el-radio>
            <el-radio :label="0">私有</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="模板描述">
          <el-input 
            v-model="templateForm.description" 
            type="textarea" 
            :rows="4"
            placeholder="请输入模板描述"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="templateDialogVisible = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="handleTemplateSubmit" 
          :loading="submitting"
        >
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Refresh, Plus, FolderOpened } from '@element-plus/icons-vue'
import request from '@/utils/request'

const router = useRouter()

const loading = ref(false)
const submitting = ref(false)
const templateDialogVisible = ref(false)
const editingTemplate = ref(null)
const templateFormRef = ref(null)

const templates = ref([])

const filters = reactive({
  search: '',
  category: null,
  difficulty: null,
  is_public: null
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const templateForm = reactive({
  template_code: '',
  title: '',
  description: '',
  cover_image: '',
  duration: '',
  difficulty: 'beginner',
  category: '',
  version: '1.0.0',
  is_public: 1
})

const templateRules = {
  template_code: [
    { required: true, message: '请输入模板编码', trigger: 'blur' },
    { pattern: /^[A-Z0-9-]+$/, message: '模板编码只能包含大写字母、数字和连字符', trigger: 'blur' }
  ],
  title: [{ required: true, message: '请输入模板名称', trigger: 'blur' }],
  category: [{ required: true, message: '请选择分类', trigger: 'change' }],
  difficulty: [{ required: true, message: '请选择难度等级', trigger: 'change' }],
  is_public: [{ required: true, message: '请选择公开状态', trigger: 'change' }]
}

const difficultyMap = {
  'beginner': '初级',
  'intermediate': '中级',
  'advanced': '高级'
}

// 加载模板列表
const loadTemplates = async () => {
  try {
    loading.value = true
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      ...(filters.search && { search: filters.search }),
      ...(filters.category && { category: filters.category }),
      ...(filters.is_public !== null && { is_public: filters.is_public })
    }
    
    // 使用 request 工具
    const response = await request.get('/pbl/admin/courses/templates', {
      params
    })
    
    // 简化响应处理
    const data = response.data
    templates.value = data.items || []
    pagination.total = data.total || 0
    
  } catch (error) {
    console.error('加载模板列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 重置筛选
const resetFilters = () => {
  filters.search = ''
  filters.category = null
  filters.difficulty = null
  filters.is_public = null
  pagination.page = 1
  loadTemplates()
}

// 管理内容 - 跳转到详情页
const handleManageContent = (template) => {
  router.push(`/pbl/admin/course-templates/${template.uuid}`)
}

// 打开创建对话框
const handleCreate = () => {
  editingTemplate.value = null
  Object.assign(templateForm, {
    template_code: '',
    title: '',
    description: '',
    cover_image: '',
    duration: '',
    difficulty: 'beginner',
    category: '',
    version: '1.0.0',
    is_public: 1
  })
  templateDialogVisible.value = true
}

// 编辑模板
const handleEdit = (template) => {
  editingTemplate.value = template
  Object.assign(templateForm, {
    template_code: template.template_code,
    title: template.title,
    description: template.description || '',
    cover_image: template.cover_image || '',
    duration: template.duration || '',
    difficulty: template.difficulty || 'beginner',
    category: template.category || '',
    version: template.version || '1.0.0',
    is_public: template.is_public
  })
  templateDialogVisible.value = true
}

// 提交模板
const handleTemplateSubmit = async () => {
  if (!templateFormRef.value) return
  
  await templateFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    try {
      submitting.value = true
      
      const data = {
        template_code: templateForm.template_code,
        title: templateForm.title,
        description: templateForm.description,
        cover_image: templateForm.cover_image,
        duration: templateForm.duration,
        difficulty: templateForm.difficulty,
        category: templateForm.category,
        version: templateForm.version,
        is_public: templateForm.is_public
      }
      
      if (editingTemplate.value) {
        // 更新
        await request.put(
          `/pbl/admin/courses/templates/${editingTemplate.value.uuid}`,
          data
        )
        ElMessage.success('模板更新成功')
      } else {
        // 新建
        await request.post('/pbl/admin/courses/templates', data)
        ElMessage.success('模板创建成功')
      }
      
      templateDialogVisible.value = false
      loadTemplates()
    } catch (error) {
      console.error('操作失败:', error)
    } finally {
      submitting.value = false
    }
  })
}

// 删除模板
const handleDelete = async (template) => {
  try {
    await request.delete(`/pbl/admin/courses/templates/${template.uuid}`)
    ElMessage.success('模板删除成功')
    loadTemplates()
  } catch (error) {
    console.error('删除失败:', error)
  }
}

// 格式化日期时间
const formatDateTime = (dateString) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 初始化
onMounted(() => {
  loadTemplates()
})
</script>

<style scoped>
.course-templates {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-form {
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
