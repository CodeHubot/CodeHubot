<template>
  <div class="device-group-management">
    <div class="page-header">
      <h1>设备分组管理</h1>
      <el-button type="primary" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>
        创建设备组
      </el-button>
    </div>

    <!-- 搜索 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="设备组名称或编号"
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

    <!-- 设备组列表 -->
    <el-card class="table-card">
      <el-table
        :data="deviceGroups"
        v-loading="loading"
        style="width: 100%"
      >
        <el-table-column prop="group_name" label="设备组名称" min-width="150" />
        <el-table-column prop="group_code" label="设备组编号" min-width="120" />
        <el-table-column prop="device_count" label="设备数量" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="info">{{ row.device_count }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '激活' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="350" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewDevices(row)">
              <el-icon><List /></el-icon>
              查看设备
            </el-button>
            <el-button type="success" link @click="authorizeToCourse(row)">
              <el-icon><Key /></el-icon>
              授权课程
            </el-button>
            <el-button type="warning" link @click="editGroup(row)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button type="danger" link @click="deleteGroup(row)">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadDeviceGroups"
          @current-change="loadDeviceGroups"
        />
      </div>
    </el-card>

    <!-- 创建/编辑设备组对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="groupFormRef"
        :model="groupForm"
        :rules="groupFormRules"
        label-width="100px"
        autocomplete="off"
      >
        <el-form-item label="设备组名称" prop="group_name">
          <el-input
            v-model="groupForm.group_name"
            placeholder="请输入设备组名称"
            autocomplete="off"
          />
        </el-form-item>
        <el-form-item label="设备组编号" prop="group_code">
          <el-input
            v-model="groupForm.group_code"
            placeholder="请输入设备组编号（可选）"
            autocomplete="off"
          />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="groupForm.description"
            type="textarea"
            :rows="4"
            placeholder="请输入描述（可选）"
            autocomplete="off"
          />
        </el-form-item>
        <el-form-item label="状态" prop="is_active" v-if="!isCreateMode">
          <el-switch
            v-model="groupForm.is_active"
            active-text="激活"
            inactive-text="禁用"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 设备列表对话框 -->
    <el-dialog
      v-model="devicesDialogVisible"
      title="设备列表"
      width="1000px"
      :close-on-click-modal="false"
    >
      <div class="devices-actions">
        <el-button type="primary" @click="showAddDevicesDialog">
          <el-icon><Plus /></el-icon>
          添加设备
        </el-button>
      </div>

      <el-table
        :data="groupDevices"
        v-loading="devicesLoading"
        style="width: 100%; margin-top: 20px"
      >
        <el-table-column prop="device_name" label="设备名称" min-width="150" />
        <el-table-column label="MAC地址" min-width="150">
          <template #default="{ row }">
            {{ row.device_mac || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="joined_at" label="加入时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.joined_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="danger" link @click="removeDevice(row)">
              <el-icon><Delete /></el-icon>
              移除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="devicesPagination.page"
          v-model:page-size="devicesPagination.page_size"
          :total="devicesPagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadGroupDevices"
          @current-change="loadGroupDevices"
        />
      </div>
    </el-dialog>

    <!-- 添加设备对话框 -->
    <el-dialog
      v-model="addDevicesDialogVisible"
      title="添加设备到组"
      width="800px"
      :close-on-click-modal="false"
    >
      <el-form :inline="true" :model="deviceSearchForm">
        <el-form-item label="关键词">
          <el-input
            v-model="deviceSearchForm.keyword"
            placeholder="设备名称或SN"
            clearable
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="searchAvailableDevices">搜索</el-button>
        </el-form-item>
      </el-form>

      <el-table
        ref="deviceTableRef"
        :data="availableDevices"
        v-loading="availableDevicesLoading"
        @selection-change="handleDeviceSelectionChange"
        style="width: 100%; margin-top: 20px"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="设备名称" min-width="150" />
        <el-table-column label="MAC地址" min-width="150">
          <template #default="{ row }">
            {{ row.device_mac || row.mac_address || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="device_status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.device_status === 'online' ? 'success' : 'info'">
              {{ row.device_status === 'online' ? '在线' : '离线' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <template #footer>
        <el-button @click="addDevicesDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          @click="submitAddDevices"
          :loading="addingDevices"
          :disabled="selectedDevices.length === 0"
        >
          添加 {{ selectedDevices.length > 0 ? `(${selectedDevices.length})` : '' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 授权课程对话框 -->
    <el-dialog
      v-model="authorizeCourseDialogVisible"
      title="授权设备组给课程"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="authFormRef"
        :model="authForm"
        :rules="authFormRules"
        label-width="100px"
        autocomplete="off"
      >
        <el-form-item label="选择课程" prop="course_uuid">
          <el-select
            v-model="authForm.course_uuid"
            placeholder="请选择课程"
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="course in coursesList"
              :key="course.uuid"
              :label="course.course_name"
              :value="course.uuid"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="有效期至" prop="expires_at">
          <el-date-picker
            v-model="authForm.expires_at"
            type="datetime"
            placeholder="选择到期时间"
            style="width: 100%"
            :disabled-date="disabledDate"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
        <el-form-item label="备注" prop="notes">
          <el-input
            v-model="authForm.notes"
            type="textarea"
            :rows="4"
            placeholder="请输入备注（可选）"
            autocomplete="off"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="authorizeCourseDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAuthorization" :loading="authorizing">
          确定授权
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, List, Key } from '@element-plus/icons-vue'
import {
  getDeviceGroups, createDeviceGroup, updateDeviceGroup, deleteDeviceGroup,
  getGroupDevices, batchAddDevicesToGroup, removeDeviceFromGroup,
  createDeviceAuthorization
} from '@/api/deviceGroups'
import { getDevices } from '@/api/device'
import { getCourses } from '@/api/courses'
import { formatDate } from '@/utils/format'
import { useUserStore } from '@/store/user'

const userStore = useUserStore()

const loading = ref(false)
const submitting = ref(false)
const deviceGroups = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('')
const isCreateMode = ref(true)
const groupFormRef = ref(null)
const currentGroupUuid = ref(null)

const searchForm = reactive({
  keyword: '',
  is_active: null
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const groupForm = reactive({
  group_name: '',
  group_code: '',
  description: '',
  is_active: true
})

const groupFormRules = {
  group_name: [
    { required: true, message: '请输入设备组名称', trigger: 'blur' },
    { min: 1, max: 100, message: '长度在1到100个字符', trigger: 'blur' }
  ]
}

// 设备列表相关
const devicesDialogVisible = ref(false)
const devicesLoading = ref(false)
const groupDevices = ref([])
const devicesPagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 添加设备相关
const addDevicesDialogVisible = ref(false)
const availableDevicesLoading = ref(false)
const availableDevices = ref([])
const selectedDevices = ref([])
const addingDevices = ref(false)
const deviceSearchForm = reactive({
  keyword: ''
})

// 授权课程相关
const authorizeCourseDialogVisible = ref(false)
const authorizing = ref(false)
const coursesList = ref([])
const currentAuthGroupId = ref(null)
const authFormRef = ref(null)

const authForm = reactive({
  course_uuid: '',
  expires_at: '',
  notes: ''
})

const authFormRules = {
  course_uuid: [
    { required: true, message: '请选择课程', trigger: 'change' }
  ],
  expires_at: [
    { required: true, message: '请选择有效期', trigger: 'change' }
  ]
}

// 加载设备组列表
const loadDeviceGroups = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      keyword: searchForm.keyword || undefined,
      is_active: searchForm.is_active !== null ? searchForm.is_active : undefined
    }
    
    const data = await getDeviceGroups(params)
    deviceGroups.value = data.device_groups || []
    pagination.total = data.total || 0
  } catch (error) {
    ElMessage.error('加载设备组列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  loadDeviceGroups()
}

// 重置
const handleReset = () => {
  searchForm.keyword = ''
  searchForm.is_active = null
  pagination.page = 1
  loadDeviceGroups()
}

// 显示创建对话框
const showCreateDialog = () => {
  isCreateMode.value = true
  dialogTitle.value = '创建设备组'
  resetGroupForm()
  dialogVisible.value = true
}

// 编辑设备组
const editGroup = (group) => {
  isCreateMode.value = false
  dialogTitle.value = '编辑设备组'
  currentGroupUuid.value = group.uuid
  
  groupForm.group_name = group.group_name
  groupForm.group_code = group.group_code || ''
  groupForm.description = group.description || ''
  groupForm.is_active = group.is_active
  
  dialogVisible.value = true
}

// 提交表单
const submitForm = async () => {
  if (!groupFormRef.value) return
  
  await groupFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      const data = {
        group_name: groupForm.group_name,
        group_code: groupForm.group_code || null,
        description: groupForm.description || null
      }
      
      if (!isCreateMode.value) {
        data.is_active = groupForm.is_active
        await updateDeviceGroup(currentGroupUuid.value, data)
        ElMessage.success('设备组更新成功')
      } else {
        await createDeviceGroup(data)
        ElMessage.success('设备组创建成功')
      }
      
      dialogVisible.value = false
      loadDeviceGroups()
    } catch (error) {
      ElMessage.error(error.message || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

// 删除设备组
const deleteGroup = async (group) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除设备组"${group.group_name}"吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await deleteDeviceGroup(group.uuid)
    ElMessage.success('设备组删除成功')
    loadDeviceGroups()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除设备组失败')
    }
  }
}

// 重置表单
const resetGroupForm = () => {
  if (groupFormRef.value) {
    groupFormRef.value.resetFields()
  }
  groupForm.group_name = ''
  groupForm.group_code = ''
  groupForm.description = ''
  groupForm.is_active = true
}

// 查看设备列表
const viewDevices = (group) => {
  currentGroupUuid.value = group.uuid
  devicesPagination.page = 1
  devicesDialogVisible.value = true
  loadGroupDevices()
}

// 加载设备组的设备列表
const loadGroupDevices = async () => {
  devicesLoading.value = true
  try {
    const params = {
      page: devicesPagination.page,
      page_size: devicesPagination.page_size
    }
    
    const data = await getGroupDevices(currentGroupUuid.value, params)
    groupDevices.value = data.devices || []
    devicesPagination.total = data.total || 0
  } catch (error) {
    ElMessage.error('加载设备列表失败')
  } finally {
    devicesLoading.value = false
  }
}

// 显示添加设备对话框
const showAddDevicesDialog = () => {
  addDevicesDialogVisible.value = true
  deviceSearchForm.keyword = ''
  selectedDevices.value = []
  searchAvailableDevices()
}

// 搜索可用设备
const searchAvailableDevices = async () => {
  availableDevicesLoading.value = true
  try {
    // 获取当前学校的所有设备，排除已在设备组中的设备
    const response = await getDevices({
      keyword: deviceSearchForm.keyword || undefined,
      page: 1,
      page_size: 100,
      exclude_grouped: true  // 排除已在设备组中的设备
    })
    
    // request拦截器已经提取了data字段，所以response.data就是设备数组
    availableDevices.value = Array.isArray(response.data) ? response.data : []
  } catch (error) {
    console.error('加载设备失败:', error)
    ElMessage.error('加载设备列表失败')
  } finally {
    availableDevicesLoading.value = false
  }
}

// 设备选择变化
const handleDeviceSelectionChange = (selection) => {
  selectedDevices.value = selection
}

// 提交添加设备
const submitAddDevices = async () => {
  if (selectedDevices.value.length === 0) {
    ElMessage.warning('请选择要添加的设备')
    return
  }
  
  addingDevices.value = true
  try {
    const deviceIds = selectedDevices.value.map(d => d.id)
    await batchAddDevicesToGroup(currentGroupUuid.value, { device_ids: deviceIds })
    
    ElMessage.success('设备添加成功')
    addDevicesDialogVisible.value = false
    loadGroupDevices()
    loadDeviceGroups() // 更新设备数量
  } catch (error) {
    ElMessage.error(error.message || '添加设备失败')
  } finally {
    addingDevices.value = false
  }
}

// 移除设备
const removeDevice = async (device) => {
  try {
    await ElMessageBox.confirm(
      `确定要从该组中移除设备"${device.device_name}"吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await removeDeviceFromGroup(currentGroupUuid.value, device.device_id)
    ElMessage.success('设备移除成功')
    loadGroupDevices()
    loadDeviceGroups() // 更新设备数量
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('移除设备失败')
    }
  }
}

// 授权给课程
const authorizeToCourse = (group) => {
  currentAuthGroupId.value = group.id
  currentGroupUuid.value = group.uuid
  authorizeCourseDialogVisible.value = true
  
  // 重置表单
  authForm.course_uuid = ''
  authForm.expires_at = ''
  authForm.notes = ''
  
  // 加载课程列表
  loadCoursesList()
}

// 加载课程列表
const loadCoursesList = async () => {
  try {
    const data = await getCourses({
      page: 1,
      page_size: 100,
      is_active: true
    })
    
    coursesList.value = data.courses || []
  } catch (error) {
    ElMessage.error('加载课程列表失败')
  }
}

// 禁用过去的日期
const disabledDate = (time) => {
  return time.getTime() < Date.now() - 8.64e7 // 禁用今天之前的日期
}

// 提交授权
const submitAuthorization = async () => {
  if (!authFormRef.value) return
  
  await authFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    authorizing.value = true
    try {
      const data = {
        device_group_id: currentAuthGroupId.value,
        expires_at: authForm.expires_at,
        notes: authForm.notes || null
      }
      
      await createDeviceAuthorization(authForm.course_uuid, data)
      
      ElMessage.success('设备授权成功')
      authorizeCourseDialogVisible.value = false
    } catch (error) {
      ElMessage.error(error.message || '授权失败')
    } finally {
      authorizing.value = false
    }
  })
}

onMounted(() => {
  loadDeviceGroups()
})
</script>

<style scoped>
.device-group-management {
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

.devices-actions {
  display: flex;
  justify-content: flex-end;
}
</style>

