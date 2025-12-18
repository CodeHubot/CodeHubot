<template>
  <div class="available-templates">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>可用课程模板库</span>
          <el-tag type="info" size="large">
            可用模板：{{ pagination.total }} 个
          </el-tag>
        </div>
      </template>

      <!-- 筛选条件 -->
      <el-form :inline="true" class="filter-form">
        <el-form-item label="搜索">
          <el-input 
            v-model="filters.search" 
            placeholder="模板名称" 
            clearable
            style="width: 250px"
            @keyup.enter="handleFilter"
          />
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
        <el-form-item label="类别">
          <el-select 
            v-model="filters.category" 
            placeholder="请选择类别" 
            clearable 
            style="width: 150px"
          >
            <el-option label="AI" value="AI" />
            <el-option label="编程" value="Programming" />
            <el-option label="机器人" value="Robot" />
            <el-option label="其他" value="Other" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleFilter">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="resetFilters">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 模板卡片列表 -->
      <el-row :gutter="24" v-loading="loading">
        <el-col 
          v-for="template in templates" 
          :key="template.id" 
          :xs="24" 
          :sm="12" 
          :md="8" 
          :lg="8"
          :xl="8"
          style="margin-bottom: 24px"
        >
          <el-card shadow="hover" class="template-card">
            <template #header>
              <div class="template-header">
                <span class="template-title">{{ template.title }}</span>
                <el-tag :type="getDifficultyType(template.difficulty)" size="small">
                  {{ getDifficultyText(template.difficulty) }}
                </el-tag>
              </div>
            </template>
            
            <div class="template-cover" v-if="template.cover_image">
              <el-image 
                :src="template.cover_image" 
                fit="cover"
                style="width: 100%; height: 180px"
              >
                <template #error>
                  <div class="image-slot">
                    <el-icon><Picture /></el-icon>
                  </div>
                </template>
              </el-image>
            </div>
            
            <div class="template-info">
              <p class="template-description">
                {{ template.description || '暂无描述' }}
              </p>
              
              <div class="template-meta">
                <div class="meta-item">
                  <el-icon><Clock /></el-icon>
                  <span>{{ template.duration || '待定' }}</span>
                </div>
                <div class="meta-item">
                  <el-icon><Document /></el-icon>
                  <span>v{{ template.version }}</span>
                </div>
              </div>
              
              <div class="template-permission" v-if="template.permission">
                <el-divider />
                <div class="permission-info">
                  <div class="permission-item">
                    <span class="label">已创建：</span>
                    <span class="value">
                      {{ template.permission.current_instances }}
                      <template v-if="template.permission.max_instances">
                        / {{ template.permission.max_instances }}
                      </template>
                      个实例
                    </span>
                  </div>
                  <div class="permission-item" v-if="template.permission.can_customize">
                    <el-tag type="success" size="small">允许自定义</el-tag>
                  </div>
                  <div class="permission-item" v-if="template.permission.valid_until">
                    <span class="label">有效至：</span>
                    <span class="value">{{ formatDate(template.permission.valid_until) }}</span>
                  </div>
                </div>
              </div>
            </div>
            
            <template #footer>
              <div class="template-actions">
                <el-button size="small" @click="handleViewDetails(template)">
                  <el-icon><View /></el-icon>
                  查看详情
                </el-button>
              </div>
            </template>
          </el-card>
        </el-col>
      </el-row>

      <!-- 空状态 -->
      <el-empty 
        v-if="!loading && templates.length === 0" 
        description="暂无可用的课程模板"
      >
        <template #extra>
          <el-text type="info">
            请联系平台管理员开放课程模板
          </el-text>
        </template>
      </el-empty>

      <!-- 分页 -->
      <div class="pagination-container" v-if="templates.length > 0">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[9, 18, 30]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadTemplates"
          @current-change="loadTemplates"
        />
      </div>
    </el-card>

    <!-- 创建课程对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="基于模板创建课程"
      width="600px"
      :close-on-click-modal="false"
    >
      <div v-if="currentTemplate">
        <el-alert
          :title="`模板：${currentTemplate.name}`"
          type="info"
          :closable="false"
          style="margin-bottom: 20px"
        />
        
        <el-form
          ref="courseFormRef"
          :model="courseForm"
          :rules="courseRules"
          label-width="100px"
        >
          <el-form-item label="课程名称" prop="title">
            <el-input 
              v-model="courseForm.title" 
              placeholder="请输入课程名称（默认使用模板名称）"
            />
          </el-form-item>
          
          <el-form-item label="课程描述">
            <el-input 
              v-model="courseForm.description" 
              type="textarea"
              :rows="3"
              placeholder="请输入课程描述（默认使用模板描述）"
            />
          </el-form-item>
          
          <el-form-item label="关联班级">
            <el-select 
              v-model="courseForm.class_id" 
              placeholder="请选择班级（可选）"
              clearable
              style="width: 100%"
            >
              <el-option 
                v-for="cls in classes" 
                :key="cls.id" 
                :label="cls.name" 
                :value="cls.id" 
              />
            </el-select>
            <el-text type="info" size="small">
              选择班级后，课程将自动分配给班级成员
            </el-text>
          </el-form-item>
        </el-form>
      </div>
      
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="handleCreateSubmit" 
          :loading="submitting"
        >
          确定创建
        </el-button>
      </template>
    </el-dialog>

    <!-- 模板详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="课程模板详情"
      width="900px"
    >
      <div v-if="currentTemplate">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="模板名称">{{ currentTemplate.name }}</el-descriptions-item>
          <el-descriptions-item label="版本">v{{ currentTemplate.version }}</el-descriptions-item>
          <el-descriptions-item label="难度">
            <el-tag :type="getDifficultyType(currentTemplate.difficulty)" size="small">
              {{ getDifficultyText(currentTemplate.difficulty) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="类别">{{ currentTemplate.category || '-' }}</el-descriptions-item>
          <el-descriptions-item label="时长">{{ currentTemplate.duration || '-' }}</el-descriptions-item>
          <el-descriptions-item label="使用次数">{{ currentTemplate.usage_count || 0 }}</el-descriptions-item>
          
          <el-descriptions-item label="权限信息" :span="2">
            <div v-if="currentTemplate.permission">
              <el-tag type="success" size="small" v-if="currentTemplate.permission.can_customize">
                允许自定义
              </el-tag>
              <el-tag type="warning" size="small" v-else>
                不允许自定义
              </el-tag>
              <span style="margin-left: 10px">
                已创建实例：{{ currentTemplate.permission.current_instances }}
                <template v-if="currentTemplate.permission.max_instances">
                  / {{ currentTemplate.permission.max_instances }}
                </template>
              </span>
            </div>
          </el-descriptions-item>
          
          <el-descriptions-item label="模板描述" :span="2">
            {{ currentTemplate.description || '-' }}
          </el-descriptions-item>
          
          <el-descriptions-item label="备注说明" :span="2" v-if="currentTemplate.permission?.remarks">
            {{ currentTemplate.permission.remarks }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button 
          type="primary" 
          @click="() => { detailDialogVisible = false; handleCreateCourse(currentTemplate) }"
          :disabled="!currentTemplate?.permission?.can_create_instance"
        >
          创建课程
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Refresh, Plus, View, Clock, Document, Picture } from '@element-plus/icons-vue'
import { 
  getAvailableTemplatesList, 
  getClubClasses 
} from '@pbl/admin/api/club'

const router = useRouter()

const loading = ref(false)
const submitting = ref(false)
const createDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const courseFormRef = ref(null)

const templates = ref([])
const classes = ref([])
const currentTemplate = ref(null)

const filters = reactive({
  search: '',
  difficulty: '',
  category: ''
})

const pagination = reactive({
  page: 1,
  page_size: 9,
  total: 0
})

const courseForm = reactive({
  title: '',
  description: '',
  class_id: null
})

const courseRules = {
  title: [{ required: true, message: '请输入课程名称', trigger: 'blur' }]
}

// 加载可用模板
const loadTemplates = async () => {
  try {
    loading.value = true
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      ...(filters.search && { search: filters.search }),
      ...(filters.difficulty && { difficulty: filters.difficulty }),
      ...(filters.category && { category: filters.category })
    }
    
    const response = await getAvailableTemplatesList(params)
    
    // 简化处理：如果 getAvailableTemplatesList 使用了 request 工具
    // response 已经是标准格式：{ success: true, data: {...} }
    const data = response.data
    templates.value = data.items || []
    pagination.total = data.total || 0
    
  } catch (error) {
    console.error('加载模板失败:', error)
  } finally {
    loading.value = false
  }
}

// 加载班级列表
const loadClasses = async () => {
  try {
    const response = await getClubClasses()
    
    if (response.data) {
      classes.value = response.data.data || []
    }
  } catch (error) {
    console.error('加载班级列表失败:', error)
  }
}

// 筛选处理
const handleFilter = () => {
  pagination.page = 1
  loadTemplates()
}

// 重置筛选
const resetFilters = () => {
  filters.search = ''
  filters.difficulty = ''
  filters.category = ''
  pagination.page = 1
  loadTemplates()
}

// 打开创建课程对话框
const handleCreateCourse = (template) => {
  if (!template.permission?.can_create_instance) {
    ElMessage.warning('已达到创建限制或模板不可用')
    return
  }
  
  currentTemplate.value = template
  courseForm.title = template.title
  courseForm.description = template.description
  courseForm.class_id = null
  createDialogVisible.value = true
}

// 提交创建课程
const handleCreateSubmit = async () => {
  if (!courseFormRef.value) return
  
  await courseFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    try {
      submitting.value = true
      
      // 注意：这个功能暂时不通过API调用，而是通过创建班级时指定template_id来实现
      // 或者可以直接跳转到创建课程页面
      ElMessage.info('请在创建班级时选择该模板，系统会自动创建课程')
      createDialogVisible.value = false
      
      // 可选：跳转到班级管理页面
      router.push('/pbl/admin/classes')
      
    } catch (error) {
      console.error('创建失败:', error)
      ElMessage.error(error.message || '创建失败')
    } finally {
      submitting.value = false
    }
  })
}

// 查看模板详情
const handleViewDetails = (template) => {
  router.push(`/pbl/admin/template-detail/${template.uuid}`)
}

// 获取难度类型
const getDifficultyType = (difficulty) => {
  const types = {
    beginner: 'success',
    intermediate: 'warning',
    advanced: 'danger'
  }
  return types[difficulty] || 'info'
}

// 获取难度文本
const getDifficultyText = (difficulty) => {
  const texts = {
    beginner: '初级',
    intermediate: '中级',
    advanced: '高级'
  }
  return texts[difficulty] || difficulty
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleDateString('zh-CN')
}

// 初始化
onMounted(() => {
  loadTemplates()
  loadClasses()
})
</script>

<style scoped>
.available-templates {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.filter-form {
  margin-bottom: 24px;
  padding: 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.template-card {
  height: 100%;
  min-height: 480px;
  display: flex;
  flex-direction: column;
  border-radius: 16px;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid #e4e7ed;
  background: #ffffff;
}

.template-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 24px rgba(64, 158, 255, 0.15);
  border-color: #409eff;
}

.template-card :deep(.el-card__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 16px 20px;
  border-bottom: none;
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.template-title {
  font-weight: 600;
  font-size: 16px;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #ffffff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.template-card :deep(.el-card__body) {
  padding: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.template-cover {
  position: relative;
  overflow: hidden;
}

.template-cover :deep(.el-image) {
  transition: transform 0.3s ease;
}

.template-card:hover .template-cover :deep(.el-image) {
  transform: scale(1.05);
}

.template-info {
  flex: 1;
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.template-description {
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
  margin: 0 0 16px 0;
  height: 66px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.template-meta {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 10px;
  margin-bottom: 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #606266;
  font-size: 13px;
  font-weight: 500;
}

.meta-item .el-icon {
  font-size: 16px;
  color: #909399;
}

.template-permission {
  margin-top: auto;
}

.template-permission :deep(.el-divider) {
  margin: 12px 0;
}

.permission-info {
  font-size: 13px;
  color: #606266;
  background: #f5f7fa;
  padding: 12px;
  border-radius: 8px;
}

.permission-item {
  margin: 6px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.permission-item .label {
  color: #909399;
  font-size: 12px;
}

.permission-item .value {
  font-weight: 600;
  color: #303133;
}

.template-card :deep(.el-card__footer) {
  padding: 16px 20px;
  background: linear-gradient(to top, #f8f9fa 0%, #ffffff 100%);
  border-top: 1px solid #f0f2f5;
}

.template-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.template-actions .el-button {
  flex: 1;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.template-actions .el-button--primary {
  background: linear-gradient(135deg, #409eff 0%, #3a8ee6 100%);
  border: none;
}

.template-actions .el-button--primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(64, 158, 255, 0.4);
}

.template-actions .el-button:not(.el-button--primary) {
  background: #ffffff;
  border: 1px solid #dcdfe6;
  color: #606266;
}

.template-actions .el-button:not(.el-button--primary):hover {
  border-color: #409eff;
  color: #409eff;
  background: #ecf5ff;
}

.image-slot {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #e3f2fd 0%, #f5f7fa 100%);
  color: #b0bec5;
  font-size: 48px;
}

.pagination-container {
  margin-top: 32px;
  display: flex;
  justify-content: center;
  padding: 20px;
  background: linear-gradient(135deg, #ffffff 0%, #f5f7fa 100%);
  border-radius: 12px;
}

/* 难度标签美化 */
.template-header :deep(.el-tag) {
  background: rgba(255, 255, 255, 0.25);
  border: 1px solid rgba(255, 255, 255, 0.4);
  color: #ffffff;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 20px;
  backdrop-filter: blur(10px);
}

/* 动画效果 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.template-card {
  animation: fadeInUp 0.5s ease-out;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .template-actions {
    flex-direction: column;
  }
  
  .template-actions .el-button {
    width: 100%;
  }
}
</style>
