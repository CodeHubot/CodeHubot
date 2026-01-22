<template>
  <div class="team-management">
    <div class="page-header">
      <h1>团队管理</h1>
      <el-button type="primary" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>
        创建团队
      </el-button>
    </div>

    <!-- 搜索筛选 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm" @submit.prevent="handleSearch">
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="团队代码或名称"
            clearable
            @clear="handleSearch"
          />
        </el-form-item>
        <el-form-item label="省份">
          <el-input
            v-model="searchForm.province"
            placeholder="省份"
            clearable
            @clear="handleSearch"
          />
        </el-form-item>
        <el-form-item label="城市">
          <el-input
            v-model="searchForm.city"
            placeholder="城市"
            clearable
            @clear="handleSearch"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select
            v-model="searchForm.is_active"
            placeholder="全部"
            clearable
            @clear="handleSearch"
          >
            <el-option label="激活" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 团队列表 -->
    <el-card class="table-card">
      <el-table :data="teams" v-loading="loading" stripe :header-cell-style="{ background: '#f5f7fa', color: '#606266', fontWeight: 'bold' }">
        <el-table-column prop="team_code" label="团队代码" width="140" align="center" />
        <el-table-column prop="team_name" label="团队名称" min-width="180" show-overflow-tooltip />
        <el-table-column label="地区" width="180" align="center">
          <template #default="{ row }">
            <div class="location-info">
              <span v-if="row.province">{{ row.province }}</span>
              <span v-if="row.city" class="city-divider">·</span>
              <span v-if="row.city">{{ row.city }}</span>
              <span v-if="!row.province && !row.city" class="text-gray">未设置</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="统计信息" width="240">
          <template #default="{ row }">
            <div class="stats-container">
              <div class="stat-row">
                <el-icon class="stat-icon" color="#409EFF"><User /></el-icon>
                <span class="stat-label">教师</span>
                <el-progress 
                  :percentage="Math.round((row.teacher_count / row.max_teachers) * 100)" 
                  :stroke-width="6"
                  :show-text="false"
                  style="flex: 1; margin: 0 8px;"
                />
                <span class="stat-number">{{ row.teacher_count }}/{{ row.max_teachers }}</span>
              </div>
              <div class="stat-row">
                <el-icon class="stat-icon" color="#67C23A"><UserFilled /></el-icon>
                <span class="stat-label">学生</span>
                <el-progress 
                  :percentage="Math.round((row.student_count / row.max_students) * 100)" 
                  :stroke-width="6"
                  :show-text="false"
                  style="flex: 1; margin: 0 8px;"
                />
                <span class="stat-number">{{ row.student_count }}/{{ row.max_students }}</span>
              </div>
              <div class="stat-row">
                <el-icon class="stat-icon" color="#E6A23C"><Monitor /></el-icon>
                <span class="stat-label">设备</span>
                <el-progress 
                  :percentage="Math.round((row.device_count / row.max_devices) * 100)" 
                  :stroke-width="6"
                  :show-text="false"
                  style="flex: 1; margin: 0 8px;"
                />
                <span class="stat-number">{{ row.device_count }}/{{ row.max_devices }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '激活' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="220" align="center">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="viewTeam(row)">
              <el-icon><View /></el-icon>
              详情
            </el-button>
            <el-button link type="success" size="small" @click="showSetAdminDialog(row)">
              <el-icon><UserFilled /></el-icon>
              设置管理员
            </el-button>
            <el-button link type="primary" size="small" @click="editTeam(row)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button link type="danger" size="small" @click="handleDelete(row)">
              <el-icon><Delete /></el-icon>
              删除
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
          @current-change="loadTeams"
          @size-change="loadTeams"
        />
      </div>
    </el-card>

    <!-- 创建/编辑团队对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '创建团队' : '编辑团队'"
      width="600px"
    >
      <el-form
        ref="teamFormRef"
        :model="teamForm"
        :rules="teamRules"
        label-width="120px"
        autocomplete="off"
      >
        <el-form-item label="团队代码" prop="team_code">
          <el-input
            v-model="teamForm.team_code"
            placeholder="如: BJ-YCZX"
            :disabled="dialogMode === 'edit'"
            autocomplete="off"
          />
        </el-form-item>
        <el-form-item label="团队名称" prop="team_name">
          <el-input v-model="teamForm.team_name" placeholder="团队名称" autocomplete="off" />
        </el-form-item>
        <el-form-item label="省份" prop="province">
          <el-input v-model="teamForm.province" placeholder="省份" autocomplete="off" />
        </el-form-item>
        <el-form-item label="城市" prop="city">
          <el-input v-model="teamForm.city" placeholder="城市" autocomplete="off" />
        </el-form-item>
        <el-form-item label="区/县" prop="district">
          <el-input v-model="teamForm.district" placeholder="区/县" autocomplete="off" />
        </el-form-item>
        <el-form-item label="详细地址" prop="address">
          <el-input v-model="teamForm.address" placeholder="详细地址" autocomplete="off" />
        </el-form-item>
        <el-form-item label="联系人" prop="contact_person">
          <el-input v-model="teamForm.contact_person" placeholder="联系人" autocomplete="off" />
        </el-form-item>
        <el-form-item label="联系电话" prop="contact_phone">
          <el-input v-model="teamForm.contact_phone" placeholder="联系电话" autocomplete="off" />
        </el-form-item>
        <el-form-item label="联系邮箱" prop="contact_email">
          <el-input v-model="teamForm.contact_email" placeholder="联系邮箱" autocomplete="off" />
        </el-form-item>
        <el-form-item label="授权到期时间" prop="license_expire_at">
          <el-date-picker
            v-model="teamForm.license_expire_at"
            type="date"
            placeholder="选择日期"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="最大教师数" prop="max_teachers">
          <el-input-number 
            v-model="teamForm.max_teachers" 
            :min="1" 
            :max="10000" 
            :step="10"
            controls-position="right"
            placeholder="请输入最大教师数"
          />
          <span class="form-tip">建议范围: 10-1000</span>
        </el-form-item>
        <el-form-item label="最大学生数" prop="max_students">
          <el-input-number 
            v-model="teamForm.max_students" 
            :min="1" 
            :max="100000"
            :step="100"
            controls-position="right"
            placeholder="请输入最大学生数"
          />
          <span class="form-tip">建议范围: 100-10000</span>
        </el-form-item>
        <el-form-item label="最大设备数" prop="max_devices">
          <el-input-number 
            v-model="teamForm.max_devices" 
            :min="1" 
            :max="50000"
            :step="50"
            controls-position="right"
            placeholder="请输入最大设备数"
          />
          <span class="form-tip">建议范围: 50-5000</span>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 团队详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="团队详情"
      width="600px"
    >
      <el-descriptions :column="2" border v-if="currentTeam">
        <el-descriptions-item label="团队代码">
          {{ currentTeam.team_code }}
        </el-descriptions-item>
        <el-descriptions-item label="团队名称">
          {{ currentTeam.team_name }}
        </el-descriptions-item>
        <el-descriptions-item label="省份">
          {{ currentTeam.province || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="城市">
          {{ currentTeam.city || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="区/县">
          {{ currentTeam.district || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="详细地址" :span="2">
          {{ currentTeam.address || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="联系人">
          {{ currentTeam.contact_person || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="联系电话">
          {{ currentTeam.contact_phone || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="联系邮箱" :span="2">
          {{ currentTeam.contact_email || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="授权到期">
          {{ currentTeam.license_expire_at || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="currentTeam.is_active ? 'success' : 'danger'">
            {{ currentTeam.is_active ? '激活' : '禁用' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="最大教师数">
          {{ currentTeam.max_teachers }}
        </el-descriptions-item>
        <el-descriptions-item label="最大学生数">
          {{ currentTeam.max_students }}
        </el-descriptions-item>
        <el-descriptions-item label="最大设备数">
          {{ currentTeam.max_devices }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatDate(currentTeam.created_at) }}
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- 设置管理员对话框 -->
    <el-dialog
      v-model="adminDialogVisible"
      title="设置团队管理员"
      width="600px"
    >
      <el-alert
        title="提示"
        type="info"
        :closable="false"
        style="margin-bottom: 20px;"
      >
        团队管理员将拥有管理本校教师、学生和设备的权限。
      </el-alert>

      <!-- 选择方式 -->
      <el-radio-group v-model="adminCreateMode" style="margin-bottom: 20px;">
        <el-radio-button label="select">从现有用户选择</el-radio-button>
        <el-radio-button label="create">创建新账号</el-radio-button>
      </el-radio-group>

      <!-- 从现有用户选择 -->
      <el-form
        v-if="adminCreateMode === 'select'"
        ref="selectAdminFormRef"
        :model="selectAdminForm"
        label-width="100px"
      >
        <el-form-item label="团队">
          <el-input v-model="adminForm.team_name" disabled />
        </el-form-item>
        <el-form-item label="搜索用户" prop="keyword">
          <el-input
            v-model="selectAdminForm.keyword"
            placeholder="输入至少3个字符搜索用户名或昵称"
            clearable
            @input="handleSearchInput"
            @clear="handleSearchClear"
            autocomplete="off"
          >
            <template #append>
              <el-button :icon="Search" @click="searchUsers" />
            </template>
          </el-input>
          <div v-if="selectAdminForm.keyword && selectAdminForm.keyword.length > 0">
            <span class="form-tip" v-if="selectAdminForm.keyword.length < 3" style="color: #909399;">
              请输入至少3个字符
            </span>
            <span class="form-tip" v-else-if="searchingUsers" style="color: #409EFF;">
              🔍 搜索中...
            </span>
            <span class="form-tip" v-else-if="!searchingUsers && individualUsers.length === 0" style="color: #E6A23C;">
              ⚠️ 未找到匹配的独立用户
            </span>
            <span class="form-tip" v-else-if="!searchingUsers && individualUsers.length > 0" style="color: #67C23A;">
              ✓ 找到 {{ individualUsers.length }} 个用户
            </span>
          </div>
        </el-form-item>
        <el-form-item label="选择用户" prop="user_id" v-if="individualUsers.length > 0">
          <el-select
            v-model="selectAdminForm.user_id"
            placeholder="请选择要设置为管理员的用户"
            style="width: 100%;"
            filterable
            clearable
          >
            <el-option
              v-for="user in individualUsers"
              :key="user.id"
              :label="`${user.real_name || user.username} (${user.username})`"
              :value="user.id"
            >
              <span style="font-weight: 500;">{{ user.real_name || user.username }}</span>
              <span style="margin-left: 10px; color: #8492a6; font-size: 13px;">({{ user.username }})</span>
            </el-option>
          </el-select>
          <div style="margin-top: 8px; padding: 8px; background: #f5f7fa; border-radius: 4px; font-size: 12px; color: #606266;">
            <div v-for="user in individualUsers" :key="'info-' + user.id" style="margin-bottom: 4px; line-height: 1.8;">
              <span style="font-weight: 500;">{{ user.real_name || user.username }}</span>
              <span style="color: #909399;"> ({{ user.username }})</span>
            </div>
          </div>
        </el-form-item>
        <el-form-item label="工号" prop="teacher_number">
          <el-input
            v-model="selectAdminForm.teacher_number"
            placeholder="请输入工号"
          />
          <span class="form-tip">工号在该团队内唯一</span>
        </el-form-item>
      </el-form>

      <!-- 创建新账号 -->
      <el-form
        v-else
        ref="adminFormRef"
        :model="adminForm"
        :rules="adminRules"
        label-width="100px"
        autocomplete="off"
      >
        <el-form-item label="团队" prop="team_name">
          <el-input v-model="adminForm.team_name" disabled autocomplete="off" />
        </el-form-item>
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="adminForm.username"
            placeholder="请输入用户名（用于登录）"
            autocomplete="off"
          />
        </el-form-item>
        <el-form-item label="真实姓名" prop="real_name">
          <el-input v-model="adminForm.real_name" placeholder="请输入真实姓名" autocomplete="off" />
        </el-form-item>
        <el-form-item label="工号" prop="teacher_number">
          <el-input
            v-model="adminForm.teacher_number"
            placeholder="请输入工号"
            autocomplete="off"
          />
          <span class="form-tip">工号在该团队内唯一</span>
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="adminForm.email" placeholder="请输入邮箱（选填）" autocomplete="off" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="adminForm.phone" placeholder="请输入手机号（选填）" autocomplete="off" />
        </el-form-item>
        <el-form-item label="初始密码" prop="password">
          <el-input
            v-model="adminForm.password"
            type="password"
            show-password
            placeholder="请输入初始密码（至少8位，包含字母和数字）"
            autocomplete="new-password"
          />
          <span class="form-tip">管理员首次登录后需修改密码</span>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="adminDialogVisible = false">取消</el-button>
        <el-button 
          v-if="adminCreateMode === 'select'"
          type="primary" 
          @click="handleAssignAdmin" 
          :loading="submitting"
          :disabled="!selectAdminForm.user_id"
        >
          设置为管理员
        </el-button>
        <el-button 
          v-else
          type="primary" 
          @click="handleCreateAdmin" 
          :loading="submitting"
        >
          创建管理员
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, User, UserFilled, Monitor, View, Edit, Delete, Search } from '@element-plus/icons-vue'
import { getTeams, createTeam, updateTeam, deleteTeam, getTeam } from '@/api/teams'
import { createTeamAdmin, searchIndividualUsers, assignRole } from '@/api/userManagement'
import { formatDate } from '@/utils/format'

// 数据
const loading = ref(false)
const submitting = ref(false)
const teams = ref([])
const dialogVisible = ref(false)
const detailDialogVisible = ref(false)
const adminDialogVisible = ref(false)
const dialogMode = ref('create') // create | edit
const adminCreateMode = ref('select') // select | create
const currentTeam = ref(null)
const teamFormRef = ref(null)
const adminFormRef = ref(null)
const selectAdminFormRef = ref(null)
const individualUsers = ref([])
const searchingUsers = ref(false)

// 防抖定时器
let searchTimer = null

// 搜索表单
const searchForm = reactive({
  keyword: '',
  province: '',
  city: '',
  is_active: null
})

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 团队表单
const teamForm = reactive({
  team_code: '',
  team_name: '',
  province: '',
  city: '',
  district: '',
  address: '',
  contact_person: '',
  contact_phone: '',
  contact_email: '',
  license_expire_at: null,
  max_teachers: 100,
  max_students: 1000,
  max_devices: 500
})

// 管理员表单
const adminForm = reactive({
  team_id: null,
  team_name: '',
  username: '',
  real_name: '',
  teacher_number: '',
  email: '',
  phone: '',
  password: ''
})

// 选择现有用户表单
const selectAdminForm = reactive({
  keyword: '',
  user_id: null,
  teacher_number: ''
})

// 表单验证规则
const teamRules = {
  team_code: [
    { required: true, message: '请输入团队代码', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  team_name: [
    { required: true, message: '请输入团队名称', trigger: 'blur' },
    { min: 2, max: 200, message: '长度在 2 到 200 个字符', trigger: 'blur' }
  ],
  license_expire_at: [
    { required: true, message: '请选择授权到期时间', trigger: 'change' }
  ],
  max_teachers: [
    { required: true, message: '请输入最大教师数', trigger: 'blur' },
    { type: 'number', min: 1, max: 10000, message: '范围在 1 到 10000', trigger: 'blur' }
  ],
  max_students: [
    { required: true, message: '请输入最大学生数', trigger: 'blur' },
    { type: 'number', min: 1, max: 100000, message: '范围在 1 到 100000', trigger: 'blur' }
  ],
  max_devices: [
    { required: true, message: '请输入最大设备数', trigger: 'blur' },
    { type: 'number', min: 1, max: 50000, message: '范围在 1 到 50000', trigger: 'blur' }
  ]
}

// 管理员表单验证规则
const adminRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '长度在 3 到 50 个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  real_name: [
    { required: true, message: '请输入真实姓名', trigger: 'blur' },
    { min: 1, max: 100, message: '长度在 1 到 100 个字符', trigger: 'blur' }
  ],
  teacher_number: [
    { required: true, message: '请输入工号', trigger: 'blur' },
    { min: 1, max: 50, message: '长度在 1 到 50 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入初始密码', trigger: 'blur' },
    { min: 8, max: 128, message: '密码长度至少8位', trigger: 'blur' },
    { pattern: /^(?=.*[A-Za-z])(?=.*\d)/, message: '密码必须包含字母和数字', trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ]
}

// 加载团队列表
const loadTeams = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      ...searchForm
    }
    const response = await getTeams(params)
    if (response.data) {
      teams.value = response.data.teams || []
      pagination.total = response.data.total || 0
    }
  } catch (error) {
    ElMessage.error('加载团队列表失败: ' + (error.response?.data?.message || error.message))
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  loadTeams()
}

// 重置搜索
const handleReset = () => {
  searchForm.keyword = ''
  searchForm.province = ''
  searchForm.city = ''
  searchForm.is_active = null
  handleSearch()
}

// 显示创建对话框
const showCreateDialog = () => {
  dialogMode.value = 'create'
  resetForm()
  dialogVisible.value = true
}

// 编辑团队
const editTeam = async (team) => {
  dialogMode.value = 'edit'
  currentTeam.value = team
  
  // 先加载完整的团队数据（使用UUID）
  try {
    loading.value = true
    const response = await getTeam(team.uuid)
    const fullTeamData = response.data
    
    // 使用完整数据填充表单
    Object.assign(teamForm, {
      team_code: fullTeamData.team_code,
      team_name: fullTeamData.team_name,
      province: fullTeamData.province || '',
      city: fullTeamData.city || '',
      district: fullTeamData.district || '',
      address: fullTeamData.address || '',
      contact_person: fullTeamData.contact_person || '',
      contact_phone: fullTeamData.contact_phone || '',
      contact_email: fullTeamData.contact_email || '',
      license_expire_at: fullTeamData.license_expire_at || null,
      max_teachers: fullTeamData.max_teachers || 100,
      max_students: fullTeamData.max_students || 1000,
      max_devices: fullTeamData.max_devices || 500
    })
    
    dialogVisible.value = true
  } catch (error) {
    ElMessage.error('加载团队详情失败: ' + (error.response?.data?.message || error.message))
  } finally {
    loading.value = false
  }
}

// 查看团队详情
const viewTeam = async (team) => {
  try {
    const response = await getTeam(team.uuid)
    if (response.data) {
      currentTeam.value = response.data
      detailDialogVisible.value = true
    }
  } catch (error) {
    ElMessage.error('加载团队详情失败: ' + (error.response?.data?.message || error.message))
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!teamFormRef.value) return
  
  await teamFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      if (dialogMode.value === 'create') {
        await createTeam(teamForm)
        ElMessage.success('团队创建成功')
      } else {
        await updateTeam(currentTeam.value.uuid, teamForm)
        ElMessage.success('团队更新成功')
      }
      dialogVisible.value = false
      loadTeams()
    } catch (error) {
      ElMessage.error(
        (dialogMode.value === 'create' ? '创建' : '更新') + 
        '团队失败: ' + 
        (error.response?.data?.message || error.message)
      )
    } finally {
      submitting.value = false
    }
  })
}

// 删除团队
const handleDelete = async (team) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除团队 "${team.team_name}" 吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await deleteTeam(team.uuid)
    ElMessage.success('团队删除成功')
    loadTeams()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除团队失败: ' + (error.response?.data?.message || error.message))
    }
  }
}

// 重置表单
const resetForm = () => {
  // 默认授权到期时间为一年后
  const defaultExpireDate = new Date()
  defaultExpireDate.setFullYear(defaultExpireDate.getFullYear() + 1)
  const expireDateStr = defaultExpireDate.toISOString().split('T')[0] // YYYY-MM-DD 格式
  
  Object.assign(teamForm, {
    team_code: '',
    team_name: '',
    province: '',
    city: '',
    district: '',
    address: '',
    contact_person: '',
    contact_phone: '',
    contact_email: '',
    license_expire_at: expireDateStr,
    max_teachers: 100,
    max_students: 1000,
    max_devices: 500
  })
  teamFormRef.value?.clearValidate()
}

// 初始化
// 显示设置管理员对话框
const showSetAdminDialog = (team) => {
  currentTeam.value = team
  adminCreateMode.value = 'select' // 默认选择现有用户
  individualUsers.value = []
  searchingUsers.value = false
  
  // 清除搜索定时器
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
  
  // 重置表单
  Object.assign(adminForm, {
    team_id: team.id,
    team_name: team.team_name,
    username: '',
    real_name: '',
    teacher_number: '',
    email: '',
    phone: '',
    password: ''
  })
  
  Object.assign(selectAdminForm, {
    keyword: '',
    user_id: null,
    teacher_number: ''
  })
  
  adminFormRef.value?.clearValidate()
  selectAdminFormRef.value?.clearValidate()
  adminDialogVisible.value = true
}

// 搜索独立用户
// 处理搜索输入（带防抖）
const handleSearchInput = () => {
  // 清除之前的定时器
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
  
  // 如果输入少于3个字符，清空结果
  if (!selectAdminForm.keyword || selectAdminForm.keyword.trim().length < 3) {
    individualUsers.value = []
    selectAdminForm.user_id = null
    return
  }
  
  // 设置新的定时器，500ms后触发搜索
  searchTimer = setTimeout(() => {
    searchUsers()
  }, 500)
}

// 清空搜索
const handleSearchClear = () => {
  selectAdminForm.keyword = ''
  selectAdminForm.user_id = null
  individualUsers.value = []
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
}

// 搜索用户
const searchUsers = async () => {
  if (!selectAdminForm.keyword || selectAdminForm.keyword.trim().length < 3) {
    individualUsers.value = []
    return
  }
  
  try {
    searchingUsers.value = true
    const response = await searchIndividualUsers({ keyword: selectAdminForm.keyword.trim() })
    
    console.log('📡 API响应:', response)
    console.log('📦 响应数据:', response.data)
    
    // response.data 已经是提取后的数据内容（request.js 拦截器已处理）
    if (response.data && response.data.users) {
      individualUsers.value = response.data.users
      console.log('✅ 设置用户列表:', individualUsers.value)
      console.log(`✓ 找到 ${individualUsers.value.length} 个用户`)
      
      // 详细输出每个用户的信息
      individualUsers.value.forEach((user, index) => {
        console.log(`用户 ${index + 1}:`, {
          id: user.id,
          username: user.username,
          real_name: user.real_name,
          email: user.email
        })
      })
    } else {
      console.warn('⚠️ 响应数据中没有 users 字段:', response.data)
      individualUsers.value = []
    }
  } catch (error) {
    console.error('❌ 搜索用户失败:', error)
    ElMessage.error('搜索用户失败: ' + (error.response?.data?.message || error.message))
    individualUsers.value = []
  } finally {
    searchingUsers.value = false
  }
}

// 从现有用户分配为管理员
const handleAssignAdmin = async () => {
  if (!selectAdminForm.user_id) {
    ElMessage.warning('请选择要设置为管理员的用户')
    return
  }
  
  if (!selectAdminForm.teacher_number) {
    ElMessage.warning('请输入工号')
    return
  }
  
  try {
    submitting.value = true
    
    const data = {
      new_role: 'team_admin',
      team_id: currentTeam.value.id,
      teacher_number: selectAdminForm.teacher_number
    }
    
    const response = await assignRole(selectAdminForm.user_id, data)
    
    // 获取被设置为管理员的用户信息
    const selectedUser = individualUsers.value.find(u => u.id === selectAdminForm.user_id)
    
    ElMessage.success({
      message: `成功设置 ${selectedUser?.real_name || selectedUser?.username} 为团队管理员`,
      duration: 3000
    })
    
    // 显示登录信息提示
    ElMessageBox.alert(
      `<div style="line-height: 1.8;">
        <p><strong>用户名：</strong>${selectedUser?.username}</p>
        <p><strong>工号：</strong>${selectAdminForm.teacher_number}</p>
        <p><strong>登录方式：</strong>使用用户名 + 密码登录</p>
        <p style="color: #E6A23C; margin-top: 10px;">请通知管理员使用原密码登录</p>
      </div>`,
      '管理员信息',
      {
        dangerouslyUseHTMLString: true,
        confirmButtonText: '知道了'
      }
    )
    
    adminDialogVisible.value = false
    loadTeams()
  } catch (error) {
    console.error('设置管理员失败:', error)
    const errorMsg = error.response?.data?.message || error.response?.data?.detail || error.message
    ElMessage.error('设置管理员失败: ' + errorMsg)
  } finally {
    submitting.value = false
  }
}

// 创建管理员
const handleCreateAdmin = async () => {
  if (!adminFormRef.value) return
  
  await adminFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    try {
      submitting.value = true
      
      const data = {
        team_id: adminForm.team_id,
        username: adminForm.username,
        real_name: adminForm.real_name,
        teacher_number: adminForm.teacher_number,
        password: adminForm.password,
        email: adminForm.email || undefined,
        phone: adminForm.phone || undefined
      }
      
      const response = await createTeamAdmin(data)
      
      if (response.code === 200) {
        ElMessage.success('团队管理员创建成功')
        
        // 显示登录信息
        ElMessageBox.alert(
          `<div style="padding: 10px;">
            <p><strong>团队管理员创建成功！</strong></p>
            <p style="margin-top: 15px; line-height: 1.8;">
              <strong>用户名：</strong>${adminForm.username}<br/>
              <strong>工号：</strong>${adminForm.teacher_number}<br/>
              <strong>初始密码：</strong>${adminForm.password}<br/>
            </p>
            <p style="margin-top: 15px; color: #E6A23C;">
              ⚠️ 请妥善保管登录信息，管理员首次登录后需修改密码。
            </p>
            <p style="margin-top: 10px; color: #909399; font-size: 13px;">
              登录方式：用户名 + 密码
            </p>
          </div>`,
          '管理员信息',
          {
            dangerouslyUseHTMLString: true,
            confirmButtonText: '我已记录',
            type: 'success'
          }
        )
        
        adminDialogVisible.value = false
        loadTeams() // 刷新列表
      }
    } catch (error) {
      ElMessage.error('创建失败: ' + (error.response?.data?.message || error.message))
    } finally {
      submitting.value = false
    }
  })
}

onMounted(() => {
  loadTeams()
})
</script>

<style scoped>
.team-management {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  font-size: 24px;
  margin: 0;
}

.search-card {
  margin-bottom: 20px;
}

.table-card {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

/* 地区信息样式 */
.location-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-size: 14px;
}

.city-divider {
  color: #DCDFE6;
  margin: 0 2px;
}

.text-gray {
  color: #C0C4CC;
  font-size: 13px;
}

/* 统计信息容器 */
.stats-container {
  padding: 8px 0;
}

.stat-row {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  gap: 6px;
}

.stat-row:last-child {
  margin-bottom: 0;
}

.stat-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.stat-label {
  font-size: 13px;
  color: #606266;
  font-weight: 500;
  width: 36px;
  flex-shrink: 0;
}

.stat-number {
  font-size: 12px;
  color: #909399;
  font-family: 'Monaco', 'Consolas', monospace;
  width: 70px;
  text-align: right;
  flex-shrink: 0;
}

/* 表格行悬停效果 */
:deep(.el-table__row:hover) {
  background-color: #f5f7fa;
}

/* 操作按钮样式优化 */
:deep(.el-button.is-link) {
  padding: 4px 8px;
  margin: 0 2px;
}

/* 表单提示文字 */
.form-tip {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}

/* 数字输入框样式优化 */
:deep(.el-input-number) {
  width: 200px;
}

/* 用户选择框样式优化 */
:deep(.el-select-dropdown__item) {
  height: auto !important;
  padding: 8px 12px;
  line-height: 1.5;
}

:deep(.el-select-dropdown__item div) {
  white-space: normal;
  word-break: break-word;
}

/* 搜索结果状态提示 */
.form-tip {
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>

