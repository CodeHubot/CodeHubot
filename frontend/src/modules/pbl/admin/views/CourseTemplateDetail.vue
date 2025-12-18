<template>
  <div class="course-template-detail">
    <el-page-header @back="handleBack" :icon="ArrowLeft">
      <template #content>
        <div class="page-header-content">
          <h2>{{ templateInfo?.title || '课程模板详情' }}</h2>
          <el-tag v-if="templateInfo" :type="templateInfo.is_public ? 'success' : 'info'" size="large">
            {{ templateInfo.is_public ? '公开' : '私有' }}
          </el-tag>
        </div>
      </template>
    </el-page-header>

    <el-card class="template-info-card" v-if="templateInfo">
      <div class="template-basic-info">
        <div class="info-item">
          <span class="label">模板编码：</span>
          <span class="value">{{ templateInfo.template_code }}</span>
        </div>
        <div class="info-item">
          <span class="label">分类：</span>
          <span class="value">{{ templateInfo.category || '-' }}</span>
        </div>
        <div class="info-item">
          <span class="label">难度：</span>
          <el-tag :type="difficultyType(templateInfo.difficulty)" size="small">
            {{ difficultyMap[templateInfo.difficulty] }}
          </el-tag>
        </div>
        <div class="info-item">
          <span class="label">课时：</span>
          <span class="value">{{ templateInfo.duration || '-' }}</span>
        </div>
        <div class="info-item">
          <span class="label">版本：</span>
          <span class="value">{{ templateInfo.version }}</span>
        </div>
        <div class="info-item">
          <span class="label">使用次数：</span>
          <span class="value">{{ templateInfo.usage_count }}</span>
        </div>
      </div>
      <div class="template-description" v-if="templateInfo.description">
        <span class="label">描述：</span>
        <p>{{ templateInfo.description }}</p>
      </div>
    </el-card>

    <el-card class="content-card">
      <template #header>
        <div class="card-header">
          <h3>课程内容</h3>
          <el-button type="primary" @click="handleAddUnit">
            <el-icon><Plus /></el-icon>
            添加单元
          </el-button>
        </div>
      </template>

      <div v-loading="loading" class="units-container">
        <el-empty v-if="!units.length" description="暂无单元内容，请添加单元" />

        <div v-for="(unit, index) in units" :key="unit.uuid" class="unit-item">
          <el-card class="unit-card">
            <template #header>
              <div class="unit-header">
                <div class="unit-title-section">
                  <el-tag type="info" size="large">单元 {{ unit.order }}</el-tag>
                  <h3>{{ unit.title }}</h3>
                </div>
                <div class="unit-actions">
                  <el-button size="small" @click="handleEditUnit(unit)">
                    <el-icon><Edit /></el-icon>
                    编辑
                  </el-button>
                  <el-popconfirm
                    title="确定删除此单元吗？将同时删除单元下的所有资源和任务"
                    @confirm="handleDeleteUnit(unit)"
                  >
                    <template #reference>
                      <el-button size="small" type="danger">
                        <el-icon><Delete /></el-icon>
                        删除
                      </el-button>
                    </template>
                  </el-popconfirm>
                </div>
              </div>
            </template>

            <div class="unit-content">
              <div class="unit-description" v-if="unit.description">
                <p>{{ unit.description }}</p>
              </div>
              <div class="unit-meta" v-if="unit.estimated_duration">
                <el-icon><Clock /></el-icon>
                预计时长：{{ unit.estimated_duration }}
              </div>

              <!-- 资源列表 -->
              <div class="resources-section">
                <div class="section-header">
                  <h4><el-icon><FolderOpened /></el-icon> 学习资源</h4>
                  <el-button size="small" type="primary" @click="handleAddResource(unit)">
                    <el-icon><Plus /></el-icon>
                    添加资源
                  </el-button>
                </div>

                <el-table :data="unit.resources" stripe border size="small" class="resource-table">
                  <el-table-column prop="order" label="顺序" width="80" align="center" />
                  <el-table-column prop="title" label="资源名称" min-width="200" />
                  <el-table-column label="类型" width="120" align="center">
                    <template #default="{ row }">
                      <el-tag size="small">{{ resourceTypeMap[row.type] || row.type }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
                  <el-table-column label="操作" width="280" align="center" fixed="right">
                    <template #default="{ row }">
                      <el-button 
                        v-if="row.type === 'document'" 
                        size="small" 
                        type="primary"
                        @click="handleEditResourceContent(unit, row)"
                      >
                        <el-icon><EditPen /></el-icon>
                        编辑内容
                      </el-button>
                      <el-button size="small" @click="handleEditResource(unit, row)">
                        编辑
                      </el-button>
                      <el-popconfirm
                        title="确定删除此资源吗？"
                        @confirm="handleDeleteResource(unit, row)"
                      >
                        <template #reference>
                          <el-button size="small" type="danger">
                            删除
                          </el-button>
                        </template>
                      </el-popconfirm>
                    </template>
                  </el-table-column>
                </el-table>

                <el-empty v-if="!unit.resources?.length" description="暂无资源" :image-size="60" />
              </div>

              <!-- 任务列表 -->
              <div class="tasks-section">
                <div class="section-header">
                  <h4><el-icon><Tickets /></el-icon> 学习任务</h4>
                  <el-button size="small" type="primary" @click="handleAddTask(unit)">
                    <el-icon><Plus /></el-icon>
                    添加任务
                  </el-button>
                </div>

                <el-table :data="unit.tasks" stripe border size="small" class="task-table">
                  <el-table-column prop="order" label="顺序" width="80" align="center" />
                  <el-table-column prop="title" label="任务名称" min-width="200" />
                  <el-table-column label="类型" width="120" align="center">
                    <template #default="{ row }">
                      <el-tag size="small">{{ taskTypeMap[row.type] || row.type }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column label="难度" width="100" align="center">
                    <template #default="{ row }">
                      <el-tag 
                        :type="row.difficulty === 'easy' ? 'success' : row.difficulty === 'medium' ? 'warning' : 'danger'"
                        size="small"
                      >
                        {{ taskDifficultyMap[row.difficulty] }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="estimated_time" label="预计时长" width="120" align="center" />
                  <el-table-column label="操作" width="180" align="center" fixed="right">
                    <template #default="{ row }">
                      <el-button size="small" @click="handleEditTask(unit, row)">
                        编辑
                      </el-button>
                      <el-popconfirm
                        title="确定删除此任务吗？"
                        @confirm="handleDeleteTask(unit, row)"
                      >
                        <template #reference>
                          <el-button size="small" type="danger">
                            删除
                          </el-button>
                        </template>
                      </el-popconfirm>
                    </template>
                  </el-table-column>
                </el-table>

                <el-empty v-if="!unit.tasks?.length" description="暂无任务" :image-size="60" />
              </div>
            </div>
          </el-card>
        </div>
      </div>
    </el-card>

    <!-- 单元编辑对话框 -->
    <el-dialog
      v-model="unitDialogVisible"
      :title="editingUnit ? '编辑单元' : '新建单元'"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="unitFormRef"
        :model="unitForm"
        :rules="unitRules"
        label-width="120px"
      >
        <el-form-item label="单元编码" prop="template_code">
          <el-input 
            v-model="unitForm.template_code" 
            placeholder="如：UNIT-001"
            :disabled="!!editingUnit"
          />
        </el-form-item>
        <el-form-item label="单元名称" prop="title">
          <el-input v-model="unitForm.title" placeholder="请输入单元名称" />
        </el-form-item>
        <el-form-item label="顺序" prop="order">
          <el-input-number v-model="unitForm.order" :min="0" :max="100" />
        </el-form-item>
        <el-form-item label="预计时长">
          <el-input v-model="unitForm.estimated_duration" placeholder="如：2周、4课时" />
        </el-form-item>
        <el-form-item label="单元描述">
          <el-input 
            v-model="unitForm.description" 
            type="textarea" 
            :rows="4"
            placeholder="请输入单元描述"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="unitDialogVisible = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="handleUnitSubmit" 
          :loading="submitting"
        >
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 资源编辑对话框 -->
    <el-dialog
      v-model="resourceDialogVisible"
      :title="editingResource ? '编辑资源' : '新建资源'"
      width="800px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="resourceFormRef"
        :model="resourceForm"
        :rules="resourceRules"
        label-width="120px"
      >
        <el-form-item label="资源编码" prop="template_code">
          <el-input 
            v-model="resourceForm.template_code" 
            placeholder="如：RES-001"
            :disabled="!!editingResource"
          />
        </el-form-item>
        <el-form-item label="资源类型" prop="type">
          <el-select v-model="resourceForm.type" placeholder="请选择类型" style="width: 100%">
            <el-option label="视频" value="video" />
            <el-option label="文档" value="document" />
            <el-option label="链接" value="link" />
            <el-option label="交互式" value="interactive" />
            <el-option label="测验" value="quiz" />
          </el-select>
        </el-form-item>
        <el-form-item label="资源名称" prop="title">
          <el-input v-model="resourceForm.title" placeholder="请输入资源名称" />
        </el-form-item>
        <el-form-item label="顺序" prop="order">
          <el-input-number v-model="resourceForm.order" :min="0" :max="100" />
        </el-form-item>
        <el-form-item label="资源URL">
          <el-input v-model="resourceForm.url" placeholder="资源链接地址" />
        </el-form-item>
        <el-form-item label="视频ID" v-if="resourceForm.type === 'video'">
          <el-input v-model="resourceForm.video_id" placeholder="阿里云VOD视频ID" />
        </el-form-item>
        <el-form-item label="视频封面" v-if="resourceForm.type === 'video'">
          <el-input v-model="resourceForm.video_cover_url" placeholder="视频封面URL" />
        </el-form-item>
        <el-form-item label="时长(秒)" v-if="resourceForm.type === 'video'">
          <el-input-number v-model="resourceForm.duration" :min="0" placeholder="视频时长" />
        </el-form-item>
        <el-form-item label="资源描述">
          <el-input 
            v-model="resourceForm.description" 
            type="textarea" 
            :rows="4"
            placeholder="请输入资源描述"
          />
        </el-form-item>
        <el-form-item label="文本内容" v-if="resourceForm.type === 'document'">
          <el-input 
            v-model="resourceForm.content" 
            type="textarea" 
            :rows="6"
            placeholder="文档内容（支持Markdown）"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="resourceDialogVisible = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="handleResourceSubmit" 
          :loading="submitting"
        >
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 任务编辑对话框 -->
    <el-dialog
      v-model="taskDialogVisible"
      :title="editingTask ? '编辑任务' : '新建任务'"
      width="800px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="taskFormRef"
        :model="taskForm"
        :rules="taskRules"
        label-width="120px"
      >
        <el-form-item label="任务编码" prop="template_code">
          <el-input 
            v-model="taskForm.template_code" 
            placeholder="如：TASK-001"
            :disabled="!!editingTask"
          />
        </el-form-item>
        <el-form-item label="任务名称" prop="title">
          <el-input v-model="taskForm.title" placeholder="请输入任务名称" />
        </el-form-item>
        <el-form-item label="任务类型" prop="type">
          <el-select v-model="taskForm.type" placeholder="请选择类型" style="width: 100%">
            <el-option label="分析" value="analysis" />
            <el-option label="编程" value="coding" />
            <el-option label="设计" value="design" />
            <el-option label="部署" value="deployment" />
            <el-option label="研究" value="research" />
            <el-option label="展示" value="presentation" />
          </el-select>
        </el-form-item>
        <el-form-item label="难度" prop="difficulty">
          <el-radio-group v-model="taskForm.difficulty">
            <el-radio label="easy">简单</el-radio>
            <el-radio label="medium">中等</el-radio>
            <el-radio label="hard">困难</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="顺序" prop="order">
          <el-input-number v-model="taskForm.order" :min="0" :max="100" />
        </el-form-item>
        <el-form-item label="预计时长">
          <el-input v-model="taskForm.estimated_time" placeholder="如：2小时、1周" />
        </el-form-item>
        <el-form-item label="预计工时">
          <el-input-number v-model="taskForm.estimated_hours" :min="0" placeholder="预计完成小时数" />
        </el-form-item>
        <el-form-item label="任务描述">
          <el-input 
            v-model="taskForm.description" 
            type="textarea" 
            :rows="4"
            placeholder="请输入任务描述"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="taskDialogVisible = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="handleTaskSubmit" 
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
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  ArrowLeft, Plus, Edit, Delete, FolderOpened, Tickets, Clock, EditPen
} from '@element-plus/icons-vue'
import request from '@/utils/request'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const submitting = ref(false)
const templateInfo = ref(null)
const units = ref([])

// 单元管理
const unitDialogVisible = ref(false)
const editingUnit = ref(null)
const unitFormRef = ref(null)

// 资源管理
const resourceDialogVisible = ref(false)
const editingResource = ref(null)
const resourceFormRef = ref(null)
const currentResourceUnit = ref(null)

// 任务管理
const taskDialogVisible = ref(false)
const editingTask = ref(null)
const taskFormRef = ref(null)
const currentTaskUnit = ref(null)

const difficultyMap = {
  'beginner': '初级',
  'intermediate': '中级',
  'advanced': '高级'
}

const resourceTypeMap = {
  'video': '视频',
  'document': '文档',
  'link': '链接',
  'interactive': '交互式',
  'quiz': '测验'
}

const taskTypeMap = {
  'analysis': '分析',
  'coding': '编程',
  'design': '设计',
  'deployment': '部署',
  'research': '研究',
  'presentation': '展示'
}

const taskDifficultyMap = {
  'easy': '简单',
  'medium': '中等',
  'hard': '困难'
}

// 单元表单
const unitForm = reactive({
  template_code: '',
  title: '',
  description: '',
  order: 0,
  estimated_duration: '',
  course_template_uuid: ''
})

const unitRules = {
  template_code: [{ required: true, message: '请输入单元编码', trigger: 'blur' }],
  title: [{ required: true, message: '请输入单元名称', trigger: 'blur' }],
  order: [{ required: true, message: '请输入顺序', trigger: 'blur' }]
}

// 资源表单
const resourceForm = reactive({
  template_code: '',
  type: 'video',
  title: '',
  description: '',
  order: 0,
  url: '',
  video_id: '',
  video_cover_url: '',
  duration: null,
  content: '',
  unit_template_uuid: ''
})

const resourceRules = {
  template_code: [{ required: true, message: '请输入资源编码', trigger: 'blur' }],
  type: [{ required: true, message: '请选择资源类型', trigger: 'change' }],
  title: [{ required: true, message: '请输入资源名称', trigger: 'blur' }],
  order: [{ required: true, message: '请输入顺序', trigger: 'blur' }]
}

// 任务表单
const taskForm = reactive({
  template_code: '',
  title: '',
  description: '',
  type: 'analysis',
  difficulty: 'easy',
  order: 0,
  estimated_time: '',
  estimated_hours: null,
  unit_template_uuid: ''
})

const taskRules = {
  template_code: [{ required: true, message: '请输入任务编码', trigger: 'blur' }],
  title: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择任务类型', trigger: 'change' }],
  difficulty: [{ required: true, message: '请选择难度', trigger: 'change' }],
  order: [{ required: true, message: '请输入顺序', trigger: 'blur' }]
}

// 返回列表
const handleBack = () => {
  router.push('/pbl/admin/course-templates')
}

// 难度标签类型
const difficultyType = (difficulty) => {
  const map = {
    'beginner': 'success',
    'intermediate': 'warning',
    'advanced': 'danger'
  }
  return map[difficulty] || ''
}

// 加载模板详情
const loadTemplateDetail = async () => {
  try {
    loading.value = true
    const templateUuid = route.params.uuid
    
    // 使用 request 工具
    const response = await request.get(
      `/pbl/admin/courses/templates/${templateUuid}/full-detail`
    )
    
    // 简化响应处理
    const data = response.data
    
    templateInfo.value = {
      id: data.id,
      uuid: data.uuid,
      template_code: data.template_code,
      title: data.title,
      description: data.description,
      category: data.category,
      difficulty: data.difficulty,
      duration: data.duration,
      version: data.version,
      is_public: data.is_public,
      usage_count: data.usage_count
    }
    units.value = data.units || []
    
  } catch (error) {
    console.error('加载模板详情失败:', error)
  } finally {
    loading.value = false
  }
}

// ==================== 单元管理 ====================

// 添加单元
const handleAddUnit = () => {
  editingUnit.value = null
  Object.assign(unitForm, {
    template_code: '',
    title: '',
    description: '',
    order: units.value.length,
    estimated_duration: '',
    course_template_uuid: templateInfo.value.uuid
  })
  unitDialogVisible.value = true
}

// 编辑单元
const handleEditUnit = (unit) => {
  editingUnit.value = unit
  Object.assign(unitForm, {
    template_code: unit.template_code,
    title: unit.title,
    description: unit.description || '',
    order: unit.order,
    estimated_duration: unit.estimated_duration || '',
    course_template_uuid: templateInfo.value.uuid
  })
  unitDialogVisible.value = true
}

// 提交单元
const handleUnitSubmit = async () => {
  if (!unitFormRef.value) return
  
  await unitFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    try {
      submitting.value = true
      
      if (editingUnit.value) {
        // 更新
        await request.put(
          `/api/v1/admin/courses/templates/${templateInfo.value.uuid}/units/${editingUnit.value.uuid}`,
          unitForm
        )
        ElMessage.success('单元更新成功')
      } else {
        // 新建
        await request.post(
          `/api/v1/admin/courses/templates/${templateInfo.value.uuid}/units`,
          unitForm
        )
        ElMessage.success('单元创建成功')
      }
      
      unitDialogVisible.value = false
      await loadTemplateDetail()
    } catch (error) {
      console.error('操作失败:', error)
    } finally {
      submitting.value = false
    }
  })
}

// 删除单元
const handleDeleteUnit = async (unit) => {
  try {
    await request.delete(
      `/api/v1/admin/courses/templates/${templateInfo.value.uuid}/units/${unit.uuid}`
    )
    ElMessage.success('单元删除成功')
    await loadTemplateDetail()
  } catch (error) {
    console.error('删除失败:', error)
  }
}

// ==================== 资源管理 ====================

// 添加资源
const handleAddResource = (unit) => {
  editingResource.value = null
  currentResourceUnit.value = unit
  Object.assign(resourceForm, {
    template_code: '',
    type: 'video',
    title: '',
    description: '',
    order: unit.resources?.length || 0,
    url: '',
    video_id: '',
    video_cover_url: '',
    duration: null,
    content: '',
    unit_template_uuid: unit.uuid
  })
  resourceDialogVisible.value = true
}

// 编辑资源
const handleEditResource = (unit, resource) => {
  editingResource.value = resource
  currentResourceUnit.value = unit
  Object.assign(resourceForm, {
    template_code: resource.template_code,
    type: resource.type,
    title: resource.title,
    description: resource.description || '',
    order: resource.order,
    url: resource.url || '',
    video_id: resource.video_id || '',
    video_cover_url: resource.video_cover_url || '',
    duration: resource.duration || null,
    content: resource.content || '',
    unit_template_uuid: unit.uuid
  })
  resourceDialogVisible.value = true
}

// 编辑资源内容（跳转到专门的编辑页面）
const handleEditResourceContent = (unit, resource) => {
  router.push({
    name: 'ResourceDocumentEditor',
    params: {
      templateUuid: templateInfo.value.uuid,
      unitUuid: unit.uuid,
      resourceUuid: resource.uuid
    }
  })
}

// 提交资源
const handleResourceSubmit = async () => {
  if (!resourceFormRef.value) return
  
  await resourceFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    try {
      submitting.value = true
      
      if (editingResource.value) {
        // 更新
        await request.put(
          `/api/v1/admin/courses/templates/${templateInfo.value.uuid}/units/${currentResourceUnit.value.uuid}/resources/${editingResource.value.uuid}`,
          resourceForm
        )
        ElMessage.success('资源更新成功')
      } else {
        // 新建
        await request.post(
          `/api/v1/admin/courses/templates/${templateInfo.value.uuid}/units/${currentResourceUnit.value.uuid}/resources`,
          resourceForm
        )
        ElMessage.success('资源创建成功')
      }
      
      resourceDialogVisible.value = false
      await loadTemplateDetail()
    } catch (error) {
      console.error('操作失败:', error)
    } finally {
      submitting.value = false
    }
  })
}

// 删除资源
const handleDeleteResource = async (unit, resource) => {
  try {
    await request.delete(
      `/api/v1/admin/courses/templates/${templateInfo.value.uuid}/units/${unit.uuid}/resources/${resource.uuid}`
    )
    ElMessage.success('资源删除成功')
    await loadTemplateDetail()
  } catch (error) {
    console.error('删除失败:', error)
  }
}

// ==================== 任务管理 ====================

// 添加任务
const handleAddTask = (unit) => {
  editingTask.value = null
  currentTaskUnit.value = unit
  Object.assign(taskForm, {
    template_code: '',
    title: '',
    description: '',
    type: 'analysis',
    difficulty: 'easy',
    order: unit.tasks?.length || 0,
    estimated_time: '',
    estimated_hours: null,
    unit_template_uuid: unit.uuid
  })
  taskDialogVisible.value = true
}

// 编辑任务
const handleEditTask = (unit, task) => {
  editingTask.value = task
  currentTaskUnit.value = unit
  Object.assign(taskForm, {
    template_code: task.template_code,
    title: task.title,
    description: task.description || '',
    type: task.type,
    difficulty: task.difficulty,
    order: task.order,
    estimated_time: task.estimated_time || '',
    estimated_hours: task.estimated_hours || null,
    unit_template_uuid: unit.uuid
  })
  taskDialogVisible.value = true
}

// 提交任务
const handleTaskSubmit = async () => {
  if (!taskFormRef.value) return
  
  await taskFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    try {
      submitting.value = true
      
      if (editingTask.value) {
        // 更新
        await request.put(
          `/api/v1/admin/courses/templates/${templateInfo.value.uuid}/units/${currentTaskUnit.value.uuid}/tasks/${editingTask.value.uuid}`,
          taskForm
        )
        ElMessage.success('任务更新成功')
      } else {
        // 新建
        await request.post(
          `/api/v1/admin/courses/templates/${templateInfo.value.uuid}/units/${currentTaskUnit.value.uuid}/tasks`,
          taskForm
        )
        ElMessage.success('任务创建成功')
      }
      
      taskDialogVisible.value = false
      await loadTemplateDetail()
    } catch (error) {
      console.error('操作失败:', error)
    } finally {
      submitting.value = false
    }
  })
}

// 删除任务
const handleDeleteTask = async (unit, task) => {
  try {
    await request.delete(
      `/api/v1/admin/courses/templates/${templateInfo.value.uuid}/units/${unit.uuid}/tasks/${task.uuid}`
    )
    ElMessage.success('任务删除成功')
    await loadTemplateDetail()
  } catch (error) {
    console.error('删除失败:', error)
  }
}

// 初始化
onMounted(() => {
  loadTemplateDetail()
})
</script>

<style scoped>
.course-template-detail {
  padding: 0;
}

.el-page-header {
  margin-bottom: 20px;
  padding: 20px;
  background: white;
  border-radius: 4px;
}

.page-header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.page-header-content h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.template-info-card {
  margin-bottom: 20px;
}

.template-basic-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-item .label {
  color: #909399;
  font-size: 14px;
}

.info-item .value {
  color: #303133;
  font-size: 14px;
  font-weight: 500;
}

.template-description {
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}

.template-description .label {
  color: #909399;
  font-size: 14px;
}

.template-description p {
  margin: 8px 0 0 0;
  color: #606266;
  line-height: 1.6;
}

.content-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.units-container {
  min-height: 200px;
}

.unit-item {
  margin-bottom: 20px;
}

.unit-item:last-child {
  margin-bottom: 0;
}

.unit-card {
  border: 2px solid #e4e7ed;
  transition: all 0.3s;
}

.unit-card:hover {
  border-color: #409eff;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.15);
}

.unit-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.unit-title-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.unit-title-section h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.unit-actions {
  display: flex;
  gap: 8px;
}

.unit-content {
  padding: 20px;
  background: #f5f7fa;
  border-radius: 4px;
}

.unit-description {
  margin-bottom: 16px;
  padding: 12px;
  background: white;
  border-radius: 4px;
  border-left: 3px solid #409eff;
}

.unit-description p {
  margin: 0;
  color: #606266;
  line-height: 1.6;
}

.unit-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding: 8px 12px;
  background: white;
  border-radius: 4px;
  color: #909399;
  font-size: 14px;
}

.resources-section,
.tasks-section {
  margin-top: 16px;
  padding: 16px;
  background: white;
  border-radius: 4px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.resource-table,
.task-table {
  margin-top: 12px;
}

/* 响应式 */
@media (max-width: 768px) {
  .template-basic-info {
    grid-template-columns: 1fr;
  }
  
  .unit-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .unit-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
