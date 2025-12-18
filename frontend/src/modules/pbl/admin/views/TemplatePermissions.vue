<template>
  <div class="template-permissions">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>课程模板授权管理</span>
          <el-button type="primary" @click="handleOpenPermissionDialog()">
            <el-icon><Plus /></el-icon>
            开放模板给学校
          </el-button>
        </div>
      </template>

      <!-- 筛选条件 -->
      <el-form :inline="true" class="filter-form">
        <el-form-item label="搜索">
          <el-input 
            v-model="filters.search" 
            placeholder="模板名称或学校" 
            clearable
            style="width: 250px"
          />
        </el-form-item>
        <el-form-item label="模板">
          <el-select 
            v-model="filters.template_id" 
            placeholder="请选择模板" 
            clearable 
            style="width: 200px"
            filterable
          >
            <el-option 
              v-for="template in allTemplates" 
              :key="template.id" 
              :label="template.title" 
              :value="template.id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="学校">
          <el-select 
            v-model="filters.school_id" 
            placeholder="请选择学校" 
            clearable 
            style="width: 200px"
            filterable
          >
            <el-option 
              v-for="school in schools" 
              :key="school.id" 
              :label="school.school_name" 
              :value="school.id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select 
            v-model="filters.is_active" 
            placeholder="请选择状态" 
            clearable 
            style="width: 150px"
          >
            <el-option label="启用" :value="1" />
            <el-option label="禁用" :value="0" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadPermissions">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="resetFilters">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 权限列表表格 -->
      <el-table
        :data="permissions"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="template_title" label="课程模板" width="200" />
        <el-table-column prop="school_name" label="学校" width="200" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="允许自定义" width="120">
          <template #default="{ row }">
            <el-tag :type="row.can_customize ? 'success' : 'warning'" size="small">
              {{ row.can_customize ? '允许' : '不允许' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="实例限制" width="120">
          <template #default="{ row }">
            <span v-if="row.max_instances">
              {{ row.current_instances }} / {{ row.max_instances }}
            </span>
            <span v-else>不限制</span>
          </template>
        </el-table-column>
        <el-table-column label="有效期" width="180">
          <template #default="{ row }">
            <div style="font-size: 12px">
              <div v-if="row.valid_from">开始：{{ formatDate(row.valid_from) }}</div>
              <div v-if="row.valid_until">结束：{{ formatDate(row.valid_until) }}</div>
              <div v-if="!row.valid_from && !row.valid_until">永久有效</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="granted_at" label="授权时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.granted_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-popconfirm
              title="确定删除此权限吗？"
              @confirm="handleDelete(row)"
            >
              <template #reference>
                <el-button type="danger" size="small" :disabled="row.current_instances > 0">
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
          @size-change="loadPermissions"
          @current-change="loadPermissions"
        />
      </div>
    </el-card>

    <!-- 创建/编辑权限对话框 -->
    <el-dialog
      v-model="permissionDialogVisible"
      :title="editingPermission ? '编辑模板开放权限' : '开放模板给学校'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="permissionFormRef"
        :model="permissionForm"
        :rules="permissionRules"
        label-width="120px"
      >
        <el-form-item label="课程模板" prop="template_id" v-if="!editingPermission">
          <el-select 
            v-model="permissionForm.template_id" 
            placeholder="请选择模板" 
            filterable
            style="width: 100%"
          >
            <el-option 
              v-for="template in allTemplates" 
              :key="template.id" 
              :label="template.title" 
              :value="template.id" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="学校" prop="school_id" v-if="!editingPermission">
          <el-select 
            v-model="permissionForm.school_id" 
            placeholder="请选择学校" 
            filterable
            style="width: 100%"
          >
            <el-option 
              v-for="school in schools" 
              :key="school.id" 
              :label="school.school_name" 
              :value="school.id" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="状态" prop="is_active">
          <el-radio-group v-model="permissionForm.is_active">
            <el-radio :label="1">启用</el-radio>
            <el-radio :label="0">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="允许自定义" prop="can_customize">
          <el-radio-group v-model="permissionForm.can_customize">
            <el-radio :label="1">允许</el-radio>
            <el-radio :label="0">不允许</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="实例数限制">
          <el-input-number 
            v-model="permissionForm.max_instances" 
            :min="1" 
            :max="100"
            placeholder="不填表示不限制"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="有效期">
          <el-date-picker
            v-model="permissionForm.valid_range"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="备注">
          <el-input 
            v-model="permissionForm.remarks" 
            type="textarea" 
            :rows="3"
            placeholder="请输入备注说明"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="permissionDialogVisible = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="handlePermissionSubmit" 
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
import { ElMessage } from 'element-plus'
import { Search, Refresh, Plus } from '@element-plus/icons-vue'
import request from '@/utils/request'

const loading = ref(false)
const submitting = ref(false)
const permissionDialogVisible = ref(false)
const editingPermission = ref(null)
const permissionFormRef = ref(null)

const permissions = ref([])
const allTemplates = ref([])
const schools = ref([])

const filters = reactive({
  search: '',
  template_id: null,
  school_id: null,
  is_active: null
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const permissionForm = reactive({
  template_id: null,
  school_id: null,
  is_active: 1,
  can_customize: 1,
  max_instances: null,
  valid_range: null,
  remarks: ''
})

const permissionRules = {
  template_id: [{ required: true, message: '请选择课程模板', trigger: 'change' }],
  school_id: [{ required: true, message: '请选择学校', trigger: 'change' }],
  is_active: [{ required: true, message: '请选择状态', trigger: 'change' }],
  can_customize: [{ required: true, message: '请选择是否允许自定义', trigger: 'change' }]
}

// 加载权限列表
const loadPermissions = async () => {
  try {
    loading.value = true
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      ...(filters.template_id && { template_id: filters.template_id }),
      ...(filters.school_id && { school_id: filters.school_id }),
      ...(filters.is_active !== null && { is_active: filters.is_active })
    }
    
    // 使用 request 工具，自动处理 token 和响应格式
    const response = await request.get('/api/pbl/admin/template-permissions', {
      params
    })
    
    // 简化响应处理，直接使用 data
    const data = response.data
    permissions.value = data.items || []
    pagination.total = data.total || 0
    
  } catch (error) {
    // 错误已在 request 中统一处理
    console.error('加载权限列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 加载所有模板
const loadTemplates = async () => {
  try {
    const allItems = []
    let page = 1
    const pageSize = 100
    let hasMore = true
    
    // 循环加载所有页
    while (hasMore) {
      // 使用 request 工具
      const response = await request.get('/api/pbl/admin/courses/templates', {
        params: { page, page_size: pageSize }
      })
      
      // 简化响应处理
      const data = response.data
      const items = data.items || []
      allItems.push(...items)
      
      // 检查是否还有更多数据
      const total = data.total || 0
      hasMore = allItems.length < total
      page++
    }
    
    allTemplates.value = allItems
  } catch (error) {
    console.error('加载模板列表失败:', error)
  }
}

// 加载学校列表
const loadSchools = async () => {
  try {
    // 使用 request 工具
    const response = await request.get('/api/pbl/admin/schools/list', {
      params: { limit: 1000 }
    })
    
    // 简化响应处理
    const data = response.data
    schools.value = data.items || []
    
  } catch (error) {
    console.error('加载学校列表失败:', error)
  }
}

// 重置筛选
const resetFilters = () => {
  filters.search = ''
  filters.template_id = null
  filters.school_id = null
  filters.is_active = null
  pagination.page = 1
  loadPermissions()
}

// 打开权限对话框
const handleOpenPermissionDialog = (permission = null) => {
  editingPermission.value = permission
  
  if (permission) {
    // 编辑模式
    permissionForm.is_active = permission.is_active
    permissionForm.can_customize = permission.can_customize
    permissionForm.max_instances = permission.max_instances
    permissionForm.remarks = permission.remarks
    
    if (permission.valid_from && permission.valid_until) {
      permissionForm.valid_range = [permission.valid_from, permission.valid_until]
    } else {
      permissionForm.valid_range = null
    }
  } else {
    // 新建模式
    Object.assign(permissionForm, {
      template_id: null,
      school_id: null,
      is_active: 1,
      can_customize: 1,
      max_instances: null,
      valid_range: null,
      remarks: ''
    })
  }
  
  permissionDialogVisible.value = true
}

// 编辑权限
const handleEdit = (permission) => {
  handleOpenPermissionDialog(permission)
}

// 提交权限
const handlePermissionSubmit = async () => {
  if (!permissionFormRef.value) return
  
  await permissionFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    try {
      submitting.value = true
      
      const data = {
        is_active: permissionForm.is_active,
        can_customize: permissionForm.can_customize,
        max_instances: permissionForm.max_instances,
        remarks: permissionForm.remarks
      }
      
      if (permissionForm.valid_range && permissionForm.valid_range.length === 2) {
        data.valid_from = permissionForm.valid_range[0]
        data.valid_until = permissionForm.valid_range[1]
      }
      
      if (editingPermission.value) {
        // 更新
        await request.put(
          `/api/pbl/admin/template-permissions/${editingPermission.value.uuid}`,
          data
        )
        ElMessage.success('权限更新成功')
      } else {
        // 新建
        data.template_id = permissionForm.template_id
        data.school_id = permissionForm.school_id
        
        await request.post('/api/pbl/admin/template-permissions', data)
        ElMessage.success('权限创建成功')
      }
      
      permissionDialogVisible.value = false
      loadPermissions()
    } catch (error) {
      console.error('操作失败:', error)
    } finally {
      submitting.value = false
    }
  })
}

// 删除权限
const handleDelete = async (permission) => {
  try {
    await request.delete(`/api/pbl/admin/template-permissions/${permission.uuid}`)
    ElMessage.success('权限删除成功')
    loadPermissions()
  } catch (error) {
    console.error('删除失败:', error)
  }
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleDateString('zh-CN')
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
  loadPermissions()
  loadTemplates()
  loadSchools()
})
</script>

<style scoped>
.template-permissions {
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
