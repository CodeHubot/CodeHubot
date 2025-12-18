<template>
  <div class="admin-schools">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>学校管理</span>
          <el-button type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            创建学校
          </el-button>
        </div>
      </template>

      <!-- 筛选条件 -->
      <el-form :inline="true" class="filter-form">
        <el-form-item label="搜索">
          <el-input 
            v-model="filters.search" 
            placeholder="学校名称/代码/城市" 
            clearable
            style="width: 250px"
            @keyup.enter="handleFilter"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select 
            v-model="filters.isActive" 
            placeholder="请选择状态" 
            clearable 
            style="width: 150px"
          >
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
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

      <!-- 数据表格 -->
      <el-table 
        :data="schools" 
        v-loading="loading" 
        stripe
        style="width: 100%"
      >
        <el-table-column prop="school_name" label="学校名称" min-width="200" fixed="left" />
        <el-table-column prop="school_code" label="学校代码" width="120" />
        <el-table-column label="地址" min-width="200">
          <template #default="{ row }">
            {{ [row.province, row.city, row.district].filter(Boolean).join(' ') || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="教师容量" width="120">
          <template #default="{ row }">
            <el-progress 
              :percentage="calculatePercentage(row.current_teachers, row.max_teachers)" 
              :color="getProgressColor(row.current_teachers, row.max_teachers)"
              :format="() => `${row.current_teachers}/${row.max_teachers}`"
            />
          </template>
        </el-table-column>
        <el-table-column label="学生容量" width="120">
          <template #default="{ row }">
            <el-progress 
              :percentage="calculatePercentage(row.current_students, row.max_students)" 
              :color="getProgressColor(row.current_students, row.max_students)"
              :format="() => `${row.current_students}/${row.max_students}`"
            />
          </template>
        </el-table-column>
        <el-table-column prop="admin_username" label="管理员" width="120">
          <template #default="{ row }">
            {{ row.admin_username || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="license_expire_at" label="授权到期" width="120">
          <template #default="{ row }">
            {{ row.license_expire_at || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="350" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleView(row)">
              <el-icon><View /></el-icon>
              详情
            </el-button>
            <el-button size="small" @click="handleEdit(row)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button 
              size="small" 
              type="primary"
              @click="handleManageAdmin(row)"
            >
              <el-icon><User /></el-icon>
              管理员
            </el-button>
            <el-button 
              size="small" 
              :type="row.is_active ? 'warning' : 'success'" 
              @click="handleToggleActive(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 创建/编辑学校对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '创建学校' : '编辑学校'"
      width="800px"
      :close-on-click-modal="false"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="学校代码" prop="school_code">
              <el-input v-model="form.school_code" placeholder="如：BJ-YCZX" :disabled="dialogMode === 'edit'" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="学校名称" prop="school_name">
              <el-input v-model="form.school_name" placeholder="请输入学校名称" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="省份">
              <el-input v-model="form.province" placeholder="如：北京市" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="城市">
              <el-input v-model="form.city" placeholder="如：北京市" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="区/县">
              <el-input v-model="form.district" placeholder="如：朝阳区" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="详细地址">
          <el-input v-model="form.address" placeholder="请输入详细地址" />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="联系人">
              <el-input v-model="form.contact_person" placeholder="联系人姓名" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="联系电话">
              <el-input v-model="form.contact_phone" placeholder="联系电话" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="联系邮箱">
              <el-input v-model="form.contact_email" placeholder="联系邮箱" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="教师容量" prop="max_teachers">
              <el-input-number v-model="form.max_teachers" :min="1" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="学生容量" prop="max_students">
              <el-input-number v-model="form.max_students" :min="1" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="设备容量">
              <el-input-number v-model="form.max_devices" :min="1" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="授权到期时间">
          <el-date-picker
            v-model="form.license_expire_at"
            type="date"
            placeholder="选择授权到期时间"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="学校描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入学校描述"
          />
        </el-form-item>

        <!-- 视频权限设置 - 暂时隐藏 -->
        <!-- 
        <el-divider>视频权限设置</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="学生观看次数">
              <el-input-number 
                v-model="form.video_student_view_limit" 
                :min="0" 
                placeholder="留空表示不限制"
                style="width: 100%" 
              />
              <div style="color: #909399; font-size: 12px; margin-top: 5px;">
                设置学生每个视频可观看的次数，留空或0表示不限制
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="教师观看次数">
              <el-input-number 
                v-model="form.video_teacher_view_limit" 
                :min="0" 
                placeholder="留空表示不限制"
                style="width: 100%" 
              />
              <div style="color: #909399; font-size: 12px; margin-top: 5px;">
                设置教师每个视频可观看的次数，留空或0表示不限制
              </div>
            </el-form-item>
          </el-col>
        </el-row>
        -->

        <!-- 管理员信息（仅创建时显示） -->
        <el-divider v-if="dialogMode === 'create'">学校管理员信息（可选）</el-divider>
        <template v-if="dialogMode === 'create'">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="管理员工号">
                <el-input v-model="form.admin_teacher_number" placeholder="管理员职工号" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="管理员密码">
                <el-input v-model="form.admin_password" type="password" placeholder="管理员登录密码" show-password />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="管理员姓名">
                <el-input v-model="form.admin_name" placeholder="管理员姓名" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="管理员电话">
                <el-input v-model="form.admin_phone" placeholder="管理员电话" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="管理员邮箱">
                <el-input v-model="form.admin_email" placeholder="管理员邮箱" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-alert
            type="info"
            :closable="false"
            style="margin-top: 10px"
          >
            <template #default>
              <div style="font-size: 13px;">
                <strong>说明：</strong>管理员用户名将自动生成为"工号@学校编码"的格式
              </div>
            </template>
          </el-alert>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- 管理员管理对话框 -->
    <el-dialog
      v-model="adminDialogVisible"
      :title="currentSchool ? `管理学校管理员 - ${currentSchool.school_name}` : '管理学校管理员'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-alert
        v-if="adminInfo.has_admin"
        title="该学校已有管理员，编辑后将更新管理员信息"
        type="warning"
        :closable="false"
        style="margin-bottom: 20px"
      />
      <el-alert
        v-else
        title="该学校尚未设置管理员，请创建管理员账号"
        type="info"
        :closable="false"
        style="margin-bottom: 20px"
      />
      
      <el-form :model="adminForm" :rules="adminRules" ref="adminFormRef" label-width="100px">
        <el-form-item label="职工号" prop="teacher_number">
          <el-input 
            v-model="adminForm.teacher_number" 
            placeholder="请输入职工号"
          />
          <div style="color: #909399; font-size: 12px; margin-top: 5px;">
            用户名将自动生成为：{{ adminForm.teacher_number }}@{{ currentSchool?.school_code }}
          </div>
        </el-form-item>
        
        <el-form-item label="登录密码" prop="password">
          <el-input 
            v-model="adminForm.password" 
            type="password"
            :placeholder="adminInfo.has_admin ? '留空则不修改密码' : '请输入登录密码'"
            show-password
          />
          <div style="color: #909399; font-size: 12px; margin-top: 5px;">
            {{ adminInfo.has_admin ? '留空则不修改密码，如需修改请输入新密码' : '首次登录后需修改密码' }}
          </div>
        </el-form-item>
        
        <el-form-item label="姓名" prop="name">
          <el-input v-model="adminForm.name" placeholder="请输入姓名" />
        </el-form-item>
        
        <el-form-item label="联系电话">
          <el-input v-model="adminForm.phone" placeholder="请输入联系电话" />
        </el-form-item>
        
        <el-form-item label="邮箱">
          <el-input v-model="adminForm.email" placeholder="请输入邮箱" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="adminDialogVisible = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="handleSubmitAdmin" 
          :loading="adminSubmitting"
        >
          {{ adminInfo.has_admin ? '更新管理员' : '创建管理员' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 学校详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="学校详情"
      width="800px"
    >
      <el-descriptions :column="2" border>
        <el-descriptions-item label="学校名称">{{ detailData.school_name }}</el-descriptions-item>
        <el-descriptions-item label="学校代码">{{ detailData.school_code }}</el-descriptions-item>
        <el-descriptions-item label="省份">{{ detailData.province || '-' }}</el-descriptions-item>
        <el-descriptions-item label="城市">{{ detailData.city || '-' }}</el-descriptions-item>
        <el-descriptions-item label="区/县">{{ detailData.district || '-' }}</el-descriptions-item>
        <el-descriptions-item label="详细地址">{{ detailData.address || '-' }}</el-descriptions-item>
        <el-descriptions-item label="联系人">{{ detailData.contact_person || '-' }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{ detailData.contact_phone || '-' }}</el-descriptions-item>
        <el-descriptions-item label="联系邮箱">{{ detailData.contact_email || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="detailData.is_active ? 'success' : 'danger'">
            {{ detailData.is_active ? '启用' : '禁用' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="教师数">
          {{ detailData.current_teachers }} / {{ detailData.max_teachers }}
        </el-descriptions-item>
        <el-descriptions-item label="学生数">
          {{ detailData.current_students }} / {{ detailData.max_students }}
        </el-descriptions-item>
        <el-descriptions-item label="设备容量">{{ detailData.max_devices }}</el-descriptions-item>
        <el-descriptions-item label="授权到期">{{ detailData.license_expire_at || '-' }}</el-descriptions-item>
        <!-- 视频权限信息 - 暂时隐藏
        <el-descriptions-item label="学生观看限制">
          {{ detailData.video_student_view_limit ? `${detailData.video_student_view_limit}次` : '不限制' }}
        </el-descriptions-item>
        <el-descriptions-item label="教师观看限制">
          {{ detailData.video_teacher_view_limit ? `${detailData.video_teacher_view_limit}次` : '不限制' }}
        </el-descriptions-item>
        -->
        <el-descriptions-item label="学校管理员" :span="2">
          {{ detailData.admin_user ? `${detailData.admin_user.name} (${detailData.admin_user.username})` : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间" :span="2">{{ formatDateTime(detailData.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="学校描述" :span="2">
          {{ detailData.description || '-' }}
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, Edit, View, User } from '@element-plus/icons-vue'
import request from '@/utils/request'

const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const detailDialogVisible = ref(false)
const adminDialogVisible = ref(false)
const adminSubmitting = ref(false)
const dialogMode = ref('create') // 'create' or 'edit'
const formRef = ref(null)
const adminFormRef = ref(null)

const schools = ref([])
const detailData = ref({})
const currentSchool = ref(null)
const adminInfo = ref({
  has_admin: false,
  admin_user: null
})

const filters = reactive({
  search: '',
  isActive: null
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const form = reactive({
  school_uuid: null,
  school_code: '',
  school_name: '',
  province: '',
  city: '',
  district: '',
  address: '',
  contact_person: '',
  contact_phone: '',
  contact_email: '',
  max_teachers: 100,
  max_students: 1000,
  max_devices: 500,
  license_expire_at: null,
  description: '',
  video_student_view_limit: null,
  video_teacher_view_limit: null,
  admin_teacher_number: '',
  admin_password: '',
  admin_name: '',
  admin_phone: '',
  admin_email: ''
})

const adminForm = reactive({
  teacher_number: '',
  password: '',
  name: '',
  phone: '',
  email: ''
})

const rules = {
  school_code: [{ required: true, message: '请输入学校代码', trigger: 'blur' }],
  school_name: [{ required: true, message: '请输入学校名称', trigger: 'blur' }],
  max_teachers: [{ required: true, message: '请设置教师容量', trigger: 'blur' }],
  max_students: [{ required: true, message: '请设置学生容量', trigger: 'blur' }]
}

// 管理员表单验证规则（动态生成，因为密码在更新时不是必填的）
const getAdminRules = () => {
  const hasAdmin = adminInfo.value?.has_admin || false
  return {
    teacher_number: [{ required: true, message: '请输入职工号', trigger: 'blur' }],
    password: [{ 
      required: !hasAdmin, // 创建时必填，更新时可选
      message: '请输入登录密码', 
      trigger: 'blur' 
    }],
    name: [{ required: true, message: '请输入姓名', trigger: 'blur' }]
  }
}

const adminRules = computed(() => getAdminRules())

// 加载学校列表
const loadSchools = async () => {
  try {
    loading.value = true
    const params = {
      skip: (pagination.page - 1) * pagination.pageSize,
      limit: pagination.pageSize,
      search: filters.search || undefined,
      is_active: filters.isActive !== null ? filters.isActive : undefined
    }
    
    const response = await request.get('/pbl/admin/schools/list', { params })
    
    const data = response.data
    schools.value = data.items || []
    pagination.total = data.total || 0
  } catch (error) {
    console.error('加载学校列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 查看详情
const handleView = async (row) => {
  try {
    loading.value = true
    const response = await request.get(`/pbl/admin/schools/${row.uuid}`)
    
    detailData.value = response.data
    detailDialogVisible.value = true
  } catch (error) {
    console.error('获取学校详情失败:', error)
  } finally {
    loading.value = false
  }
}

// 打开创建对话框
const handleCreate = () => {
  dialogMode.value = 'create'
  resetForm()
  dialogVisible.value = true
}

// 打开编辑对话框
const handleEdit = (row) => {
  dialogMode.value = 'edit'
  Object.assign(form, {
    school_uuid: row.uuid,
    school_code: row.school_code,
    school_name: row.school_name,
    province: row.province,
    city: row.city,
    district: row.district,
    address: row.address,
    contact_person: row.contact_person,
    contact_phone: row.contact_phone,
    contact_email: row.contact_email,
    max_teachers: row.max_teachers,
    max_students: row.max_students,
    max_devices: row.max_devices,
    license_expire_at: row.license_expire_at,
    description: row.description,
    video_student_view_limit: row.video_student_view_limit,
    video_teacher_view_limit: row.video_teacher_view_limit
  })
  dialogVisible.value = true
}

// 重置表单
const resetForm = () => {
  Object.assign(form, {
    school_uuid: null,
    school_code: '',
    school_name: '',
    province: '',
    city: '',
    district: '',
    address: '',
    contact_person: '',
    contact_phone: '',
    contact_email: '',
    max_teachers: 100,
    max_students: 1000,
    max_devices: 500,
    license_expire_at: null,
    description: '',
    video_student_view_limit: null,
    video_teacher_view_limit: null,
    admin_teacher_number: '',
    admin_password: '',
    admin_name: '',
    admin_phone: '',
    admin_email: ''
  })
  formRef.value?.resetFields()
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    submitting.value = true
    
    const data = new FormData()
    Object.keys(form).forEach(key => {
      if (form[key] !== null && form[key] !== '' && key !== 'school_uuid') {
        data.append(key, form[key])
      }
    })
    
    let response
    if (dialogMode.value === 'create') {
      response = await request.post('/pbl/admin/schools', data)
    } else {
      response = await request.put(`/pbl/admin/schools/${form.school_uuid}`, data)
    }
    
    ElMessage.success(dialogMode.value === 'create' ? '创建成功！' : '更新成功！')
    dialogVisible.value = false
    loadSchools()
  } catch (error) {
    if (error.errors) {
      return
    }
    console.error('提交失败:', error)
  } finally {
    submitting.value = false
  }
}

// 管理学校管理员
const handleManageAdmin = async (row) => {
  currentSchool.value = row
  
  try {
    loading.value = true
    const response = await request.get(`/pbl/admin/schools/${row.uuid}/admin`)
    
    adminInfo.value = response.data
    
    // 如果已有管理员，填充表单
    if (adminInfo.value.has_admin && adminInfo.value.admin_user) {
      const admin = adminInfo.value.admin_user
      Object.assign(adminForm, {
        teacher_number: admin.teacher_number || '',
        password: '', // 密码不回显
        name: admin.name || '',
        phone: admin.phone || '',
        email: admin.email || ''
      })
    } else {
      // 重置表单
      Object.assign(adminForm, {
        teacher_number: '',
        password: '',
        name: '',
        phone: '',
        email: ''
      })
    }
    
    adminDialogVisible.value = true
  } catch (error) {
    console.error('获取管理员信息失败:', error)
  } finally {
    loading.value = false
  }
}

// 提交管理员信息
const handleSubmitAdmin = async () => {
  if (!adminFormRef.value) return
  
  try {
    await adminFormRef.value.validate()
    
    adminSubmitting.value = true
    
    const data = new FormData()
    data.append('teacher_number', adminForm.teacher_number)
    // 只有密码不为空时才添加密码字段
    if (adminForm.password) {
      data.append('password', adminForm.password)
    }
    if (adminForm.name) data.append('name', adminForm.name)
    if (adminForm.phone) data.append('phone', adminForm.phone)
    if (adminForm.email) data.append('email', adminForm.email)
    
    const response = await request.post(
      `/pbl/admin/schools/${currentSchool.value.uuid}/admin`,
      data
    )
    
    ElMessage.success(response.message)
    adminDialogVisible.value = false
    loadSchools() // 刷新学校列表以显示新的管理员信息
  } catch (error) {
    if (error.errors) {
      return
    }
    console.error('提交失败:', error)
  } finally {
    adminSubmitting.value = false
  }
}

// 启用/禁用学校
const handleToggleActive = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要${row.is_active ? '禁用' : '启用'}学校"${row.school_name}"吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    loading.value = true
    const response = await request.patch(`/pbl/admin/schools/${row.uuid}/toggle-active`, {})
    
    ElMessage.success(response.message)
    loadSchools()
  } catch (error) {
    if (error === 'cancel') {
      return
    }
    console.error('操作失败:', error)
  } finally {
    loading.value = false
  }
}

// 筛选处理
const handleFilter = () => {
  pagination.page = 1
  loadSchools()
}

// 重置筛选
const resetFilters = () => {
  filters.search = ''
  filters.isActive = null
  pagination.page = 1
  loadSchools()
}

// 分页处理
const handleSizeChange = (size) => {
  pagination.pageSize = size
  pagination.page = 1
  loadSchools()
}

const handlePageChange = (page) => {
  pagination.page = page
  loadSchools()
}

// 计算百分比
const calculatePercentage = (current, max) => {
  if (!max || max === 0) return 0
  return Math.round((current / max) * 100)
}

// 获取进度条颜色
const getProgressColor = (current, max) => {
  const percentage = (current / max) * 100
  if (percentage >= 90) return '#F56C6C'
  if (percentage >= 70) return '#E6A23C'
  return '#67C23A'
}

// 格式化日期时间
const formatDateTime = (dateTime) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 初始化
onMounted(() => {
  loadSchools()
})
</script>

<style scoped>
.admin-schools {
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
