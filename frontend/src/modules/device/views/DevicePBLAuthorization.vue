<template>
  <div class="device-pbl-authorization">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon size="28" style="margin-right: 12px; vertical-align: middle;"><Key /></el-icon>
        PBL设备授权
      </h1>
      <p class="page-subtitle">将设备授权给班级小组，让小组学生可以使用设备</p>
    </div>

    <!-- 授权表单 -->
    <el-card class="authorization-card" shadow="never">
      <template #header>
        <div class="card-header">
          <el-icon class="header-icon"><Key /></el-icon>
          <span>授权设备给小组</span>
        </div>
      </template>

      <el-form 
        ref="authorizationFormRef" 
        :model="authorizationForm" 
        :rules="rules" 
        label-width="140px"
        class="authorization-form"
      >
        <!-- 选择设备 -->
        <el-form-item label="选择设备" prop="device_uuid">
          <el-select
            v-model="authorizationForm.device_uuid"
            placeholder="请选择要授权的设备"
            filterable
            style="width: 100%"
            @change="handleDeviceChange"
            :loading="devicesLoading"
          >
            <el-option
              v-for="device in myDevices"
              :key="device.uuid"
              :label="`${device.name} (${device.uuid})`"
              :value="device.uuid"
            >
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span>{{ device.name }}</span>
                <el-tag :type="device.is_online ? 'success' : 'info'" size="small" style="margin-left: 8px;">
                  {{ device.is_online ? '在线' : '离线' }}
                </el-tag>
              </div>
            </el-option>
          </el-select>
          <div class="form-tip">只能选择您注册的设备</div>
        </el-form-item>

        <!-- 选择小组 -->
        <el-form-item label="选择小组" prop="group_ids">
          <el-tree
            ref="groupTreeRef"
            :data="groupTreeData"
            :props="{ label: 'name', children: 'children' }"
            show-checkbox
            node-key="id"
            :default-expand-all="true"
            :check-strictly="false"
            @check="handleGroupCheck"
            style="width: 100%; max-height: 400px; overflow-y: auto; border: 1px solid #dcdfe6; border-radius: 4px; padding: 10px;"
          >
            <template #default="{ node, data }">
              <span class="tree-node">
                <el-icon v-if="data.type === 'class'" style="margin-right: 4px;"><School /></el-icon>
                <el-icon v-else-if="data.type === 'course'" style="margin-right: 4px;"><Document /></el-icon>
                <el-icon v-else style="margin-right: 4px;"><UserFilled /></el-icon>
                {{ node.label }}
                <el-tag v-if="data.type === 'group'" size="small" style="margin-left: 8px;">
                  {{ data.member_count || 0 }}人
                </el-tag>
              </span>
            </template>
          </el-tree>
          <div class="form-tip">支持多选，选择多个小组后，这些小组的学生都可以使用该设备</div>
          <div v-if="selectedGroups.length > 0" style="margin-top: 8px;">
            <el-tag
              v-for="group in selectedGroups"
              :key="group.id"
              closable
              @close="removeGroup(group.id)"
              style="margin-right: 8px; margin-bottom: 8px;"
            >
              {{ group.name }}
            </el-tag>
          </div>
        </el-form-item>

        <!-- 授权有效期 -->
        <el-form-item label="授权有效期" prop="expires_at">
          <el-date-picker
            v-model="authorizationForm.expires_at"
            type="datetime"
            placeholder="选择过期时间（留空表示永久有效）"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DDTHH:mm:ss"
            style="width: 100%"
            :disabled-date="disabledDate"
          />
          <div class="form-tip">留空表示永久有效，设置后授权将在指定时间过期</div>
        </el-form-item>

        <!-- 备注 -->
        <el-form-item label="备注" prop="notes">
          <el-input
            v-model="authorizationForm.notes"
            type="textarea"
            :rows="3"
            placeholder="请输入备注信息（可选）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <!-- 提交按钮 -->
        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="submitting" size="large">
            <el-icon><Check /></el-icon>
            提交授权
          </el-button>
          <el-button @click="handleReset" size="large">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 已授权记录（如果选择了设备） -->
    <el-card v-if="authorizationForm.device_uuid" class="authorizations-card" shadow="never" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <el-icon class="header-icon"><List /></el-icon>
          <span>该设备的授权记录</span>
        </div>
      </template>

      <el-table
        :data="deviceAuthorizations"
        v-loading="authorizationsLoading"
        style="width: 100%"
      >
        <el-table-column prop="group_name" label="小组名称" min-width="150" />
        <el-table-column prop="course_name" label="所属课程" min-width="150" />
        <el-table-column prop="class_name" label="所属班级" min-width="150" />
        <el-table-column prop="authorized_at" label="授权时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.authorized_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="expires_at" label="过期时间" width="180">
          <template #default="{ row }">
            <span v-if="row.expires_at">{{ formatDate(row.expires_at) }}</span>
            <el-tag v-else type="success" size="small">永久有效</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_expired" type="danger" size="small">已过期</el-tag>
            <el-tag v-else-if="row.is_active" type="success" size="small">有效</el-tag>
            <el-tag v-else type="info" size="small">已停用</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              type="danger"
              link
              size="small"
              @click="handleRevoke(row)"
            >
              <el-icon><Delete /></el-icon>
              撤销
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Key, Check, List, Delete, School, Document, UserFilled } from '@element-plus/icons-vue'
import { getDevices } from '@/api/device'
import {
  createPBLDeviceAuthorizations,
  getPBLDeviceAuthorizations,
  revokePBLDeviceAuthorization,
  getAuthorizableGroups
} from '@/api/devicePBLAuthorizations'
import { useUserStore } from '@/store/user'

const userStore = useUserStore()

// 表单引用
const authorizationFormRef = ref(null)
const groupTreeRef = ref(null)

// 数据
const myDevices = ref([])
const devicesLoading = ref(false)
const rawGroupData = ref([])
const selectedGroups = ref([])
const deviceAuthorizations = ref([])
const authorizationsLoading = ref(false)
const submitting = ref(false)

// 表单数据
const authorizationForm = reactive({
  device_uuid: '',
  group_ids: [],
  expires_at: null,
  notes: ''
})

// 表单验证规则
const rules = {
  device_uuid: [
    { required: true, message: '请选择要授权的设备', trigger: 'change' }
  ],
  group_ids: [
    { required: true, message: '请至少选择一个小组', trigger: 'change' },
    { 
      validator: (rule, value, callback) => {
        if (!value || value.length === 0) {
          callback(new Error('请至少选择一个小组'))
        } else {
          callback()
        }
      }, 
      trigger: 'change' 
    }
  ]
}

// 计算属性：将小组数据转换为树形结构
const groupTreeData = computed(() => {
  const classes = rawGroupData.value || []
  return classes.map(cls => ({
    id: `class_${cls.class_id}`,
    name: cls.class_name,
    type: 'class',
    children: cls.courses?.map(course => ({
      id: `course_${course.course_id}`,
      name: course.course_name,
      type: 'course',
      children: course.groups?.map(group => ({
        id: group.group_id,
        name: group.group_name,
        type: 'group',
        member_count: group.member_count
      })) || []
    })) || []
  }))
})

// 禁用过去的日期
const disabledDate = (time) => {
  return time.getTime() < Date.now() - 8.64e7 // 不能选择今天之前的日期
}

// 加载我的设备列表
const loadMyDevices = async () => {
  devicesLoading.value = true
  try {
    const response = await getDevices({ page: 1, page_size: 1000 })
    // 只显示当前用户注册的设备
    const devices = response.data || response || []
    myDevices.value = Array.isArray(devices) ? devices.filter(device => device.user_id === userStore.user?.id) : []
  } catch (error) {
    console.error('加载设备列表失败:', error)
    ElMessage.error('加载设备列表失败')
  } finally {
    devicesLoading.value = false
  }
}

// 加载可授权的小组列表
const loadAuthorizableGroups = async () => {
  try {
    const response = await getAuthorizableGroups()
    rawGroupData.value = response.data?.classes || response.classes || []
  } catch (error) {
    console.error('加载可授权小组列表失败:', error)
    ElMessage.error('加载可授权小组列表失败')
  }
}

// 设备选择变化
const handleDeviceChange = async (deviceUuid) => {
  if (deviceUuid) {
    await loadDeviceAuthorizations(deviceUuid)
  } else {
    deviceAuthorizations.value = []
  }
}

// 加载设备的授权记录
const loadDeviceAuthorizations = async (deviceUuid) => {
  authorizationsLoading.value = true
  try {
    const response = await getPBLDeviceAuthorizations(deviceUuid, {
      page: 1,
      page_size: 100
    })
    deviceAuthorizations.value = response.data?.authorizations || response.authorizations || []
  } catch (error) {
    console.error('加载授权记录失败:', error)
    ElMessage.error('加载授权记录失败')
  } finally {
    authorizationsLoading.value = false
  }
}

// 小组选择变化
const handleGroupCheck = (data, checked) => {
  const checkedKeys = groupTreeRef.value.getCheckedKeys()
  const halfCheckedKeys = groupTreeRef.value.getHalfCheckedKeys()
  
  // 只保留小组ID（排除班级和课程的ID）
  const groupIds = checkedKeys.filter(key => {
    const node = findNodeById(groupTreeData.value, key)
    return node && node.type === 'group'
  })
  
  // 更新选中的小组列表
  selectedGroups.value = groupIds.map(id => {
    const node = findNodeById(groupTreeData.value, id)
    return {
      id: node.id,
      name: node.name,
      member_count: node.member_count
    }
  })
  
  authorizationForm.group_ids = groupIds
}

// 查找节点
const findNodeById = (nodes, id) => {
  for (const node of nodes) {
    if (node.id === id) {
      return node
    }
    if (node.children) {
      const found = findNodeById(node.children, id)
      if (found) return found
    }
  }
  return null
}

// 移除小组
const removeGroup = (groupId) => {
  selectedGroups.value = selectedGroups.value.filter(g => g.id !== groupId)
  authorizationForm.group_ids = authorizationForm.group_ids.filter(id => id !== groupId)
  
  // 更新树的选择状态
  groupTreeRef.value.setChecked(groupId, false)
}

// 提交授权
const handleSubmit = async () => {
  if (!authorizationFormRef.value) return
  
  await authorizationFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    if (authorizationForm.group_ids.length === 0) {
      ElMessage.warning('请至少选择一个小组')
      return
    }
    
    submitting.value = true
    try {
      const data = {
        group_ids: authorizationForm.group_ids,
        expires_at: authorizationForm.expires_at || null,
        notes: authorizationForm.notes || ''
      }
      
      await createPBLDeviceAuthorizations(authorizationForm.device_uuid, data)
      ElMessage.success('设备授权成功')
      
      // 重新加载授权记录
      await loadDeviceAuthorizations(authorizationForm.device_uuid)
      
      // 重置表单（保留设备选择）
      const deviceUuid = authorizationForm.device_uuid
      handleReset()
      authorizationForm.device_uuid = deviceUuid
      if (deviceUuid) {
        await loadDeviceAuthorizations(deviceUuid)
      }
    } catch (error) {
      console.error('授权失败:', error)
      ElMessage.error(error.response?.data?.detail || error.message || '授权失败')
    } finally {
      submitting.value = false
    }
  })
}

// 撤销授权
const handleRevoke = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要撤销对"${row.group_name}"的授权吗？`,
      '确认撤销',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await revokePBLDeviceAuthorization(authorizationForm.device_uuid, row.id)
    ElMessage.success('授权已撤销')
    
    // 重新加载授权记录
    await loadDeviceAuthorizations(authorizationForm.device_uuid)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('撤销授权失败:', error)
      ElMessage.error(error.response?.data?.detail || error.message || '撤销授权失败')
    }
  }
}

// 重置表单
const handleReset = () => {
  authorizationFormRef.value?.resetFields()
  selectedGroups.value = []
  authorizationForm.group_ids = []
  if (groupTreeRef.value) {
    groupTreeRef.value.setCheckedKeys([])
  }
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 初始化
onMounted(async () => {
  await Promise.all([
    loadMyDevices(),
    loadAuthorizableGroups()
  ])
})
</script>

<style scoped lang="scss">
.device-pbl-authorization {
  padding: 20px;
  background: #f5f7fa;
  min-height: calc(100vh - 60px);

  .page-header {
    margin-bottom: 20px;

    .page-title {
      font-size: 24px;
      font-weight: 600;
      color: #303133;
      margin: 0 0 8px 0;
      display: flex;
      align-items: center;
    }

    .page-subtitle {
      font-size: 14px;
      color: #909399;
      margin: 0;
    }
  }

  .authorization-card,
  .authorizations-card {
    background: #fff;
    border-radius: 8px;

    .card-header {
      display: flex;
      align-items: center;
      font-size: 16px;
      font-weight: 600;
      color: #303133;

      .header-icon {
        margin-right: 8px;
        color: #409eff;
      }
    }
  }

  .authorization-form {
    .form-tip {
      font-size: 12px;
      color: #909399;
      margin-top: 4px;
      line-height: 1.5;
    }

    .tree-node {
      display: flex;
      align-items: center;
    }
  }
}
</style>
