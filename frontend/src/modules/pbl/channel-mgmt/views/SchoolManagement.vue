<template>
  <div class="school-management">
    <el-card class="header-card" shadow="never">
      <div class="header-content">
        <div>
          <h2 class="page-title">学校管理</h2>
          <p class="page-description">创建学校并分配给渠道商</p>
        </div>
        <el-button type="primary" :icon="Plus" @click="showCreateDialog">
          创建学校
        </el-button>
      </div>
    </el-card>

    <el-card class="content-card" shadow="never" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span class="card-title">学校列表</span>
          <el-input
            v-model="searchText"
            placeholder="搜索学校名称或代码"
            style="width: 300px"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
      </template>

      <el-table :data="filteredSchools" style="width: 100%">
        <el-table-column prop="school_code" label="学校代码" width="150" />
        <el-table-column prop="school_name" label="学校名称" min-width="200" />
        <el-table-column label="地区" width="200">
          <template #default="{ row }">
            {{ [row.province, row.city, row.district].filter(Boolean).join(' / ') || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="contact_person" label="联系人" width="120" />
        <el-table-column prop="contact_phone" label="联系电话" width="130" />
        
        <el-table-column prop="partner_count" label="分配渠道商数" width="130" align="center">
          <template #default="{ row }">
            <el-tag>{{ row.partner_count || 0 }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="is_active" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '正常' : '已禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" align="center" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetail(row)">查看详情</el-button>
            <el-button size="small" type="primary" @click="assignPartner(row)">
              分配渠道商
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="filteredSchools.length === 0 && !loading" class="empty-state">
        <el-empty description="暂无学校数据" />
      </div>
    </el-card>

    <!-- 创建学校对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="创建学校"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="学校代码" prop="school_code">
              <el-input v-model="formData.school_code" placeholder="如: BJ-YCZX" />
              <div class="form-tip">唯一标识，如: BJ-YCZX</div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="学校名称" prop="school_name">
              <el-input v-model="formData.school_name" placeholder="请输入学校名称" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="省份" prop="province">
              <el-input v-model="formData.province" placeholder="如: 北京市" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="城市" prop="city">
              <el-input v-model="formData.city" placeholder="如: 北京市" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="区/县" prop="district">
              <el-input v-model="formData.district" placeholder="如: 海淀区" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="详细地址" prop="address">
          <el-input v-model="formData.address" placeholder="请输入详细地址" />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="联系人" prop="contact_person">
              <el-input v-model="formData.contact_person" placeholder="联系人姓名" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="联系电话" prop="contact_phone">
              <el-input v-model="formData.contact_phone" placeholder="联系电话" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="联系邮箱" prop="contact_email">
              <el-input v-model="formData.contact_email" placeholder="联系邮箱" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">授权配置</el-divider>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="最大教师数" prop="max_teachers">
              <el-input-number v-model="formData.max_teachers" :min="1" :max="10000" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="最大学生数" prop="max_students">
              <el-input-number v-model="formData.max_students" :min="1" :max="100000" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="最大设备数" prop="max_devices">
              <el-input-number v-model="formData.max_devices" :min="1" :max="10000" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="授权到期时间" prop="license_expire_at">
          <el-date-picker
            v-model="formData.license_expire_at"
            type="date"
            placeholder="选择授权到期时间"
            style="width: 100%"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="submitting">创建</el-button>
      </template>
    </el-dialog>

    <!-- 分配渠道商对话框 -->
    <el-dialog
      v-model="assignDialogVisible"
      title="分配渠道商"
      width="600px"
    >
      <div class="assign-info">
        <p><strong>学校：</strong>{{ currentSchool?.school_name }}</p>
      </div>
      
      <el-form label-width="100px">
        <el-form-item label="选择渠道商">
          <el-select
            v-model="selectedPartnerId"
            placeholder="请选择渠道商"
            style="width: 100%"
          >
            <el-option
              v-for="partner in partners"
              :key="partner.uuid"
              :label="`${partner.name} (${partner.username})`"
              :value="partner.uuid"
            />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="assignDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAssign" :loading="assigning">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Plus } from '@element-plus/icons-vue'
import {
  getSchools,
  createSchool,
  getChannelPartners,
  assignSchoolsToPartner
} from '../api'

const router = useRouter()

const loading = ref(false)
const schools = ref([])
const searchText = ref('')
const createDialogVisible = ref(false)
const assignDialogVisible = ref(false)
const formRef = ref(null)
const submitting = ref(false)
const assigning = ref(false)
const currentSchool = ref(null)
const partners = ref([])
const selectedPartnerId = ref(null)

const formData = ref({
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
  license_expire_at: null
})

const formRules = {
  school_code: [
    { required: true, message: '请输入学校代码', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  school_name: [
    { required: true, message: '请输入学校名称', trigger: 'blur' },
    { min: 2, max: 200, message: '长度在 2 到 200 个字符', trigger: 'blur' }
  ]
}

const filteredSchools = computed(() => {
  if (!searchText.value) return schools.value
  const text = searchText.value.toLowerCase()
  return schools.value.filter(school =>
    school.school_name?.toLowerCase().includes(text) ||
    school.school_code?.toLowerCase().includes(text)
  )
})

async function fetchSchools() {
  loading.value = true
  try {
    const response = await getSchools()
    schools.value = response.data || []
  } catch (error) {
    console.error('获取学校列表失败:', error)
    ElMessage.error(error.message || '获取学校列表失败')
  } finally {
    loading.value = false
  }
}

async function fetchPartners() {
  try {
    const response = await getChannelPartners()
    partners.value = response.data || []
  } catch (error) {
    console.error('获取渠道商列表失败:', error)
  }
}

function showCreateDialog() {
  formData.value = {
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
    license_expire_at: null
  }
  createDialogVisible.value = true
}

async function handleCreate() {
  try {
    await formRef.value.validate()
    submitting.value = true

    await createSchool(formData.value)
    ElMessage.success('学校创建成功')
    createDialogVisible.value = false
    fetchSchools()
  } catch (error) {
    if (error.message) {
      ElMessage.error(error.message)
    }
  } finally {
    submitting.value = false
  }
}

function viewDetail(school) {
  ElMessage.info('学校详情页面开发中')
}

function assignPartner(school) {
  currentSchool.value = school
  selectedPartnerId.value = null
  assignDialogVisible.value = true
}

async function handleAssign() {
  if (!selectedPartnerId.value) {
    ElMessage.warning('请选择渠道商')
    return
  }

  assigning.value = true
  try {
    await assignSchoolsToPartner({
      channel_partner_uuid: selectedPartnerId.value,
      school_uuids: [currentSchool.value.uuid]
    })
    ElMessage.success('渠道商分配成功')
    assignDialogVisible.value = false
    fetchSchools()
  } catch (error) {
    ElMessage.error(error.message || '分配失败')
  } finally {
    assigning.value = false
  }
}

onMounted(() => {
  fetchSchools()
  fetchPartners()
})
</script>

<style scoped lang="scss">
.school-management {
  .header-card {
    margin-bottom: 20px;
    
    .header-content {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .page-title {
        font-size: 24px;
        font-weight: 600;
        color: #2c3e50;
        margin: 0 0 8px 0;
      }
      
      .page-description {
        color: #909399;
        margin: 0;
      }
    }
  }
  
  .content-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .card-title {
        font-size: 16px;
        font-weight: 600;
        color: #2c3e50;
      }
    }
    
    .empty-state {
      padding: 40px 0;
    }
  }

  .form-tip {
    font-size: 12px;
    color: #909399;
    margin-top: 4px;
  }

  .assign-info {
    padding: 10px;
    background: #f5f7fa;
    border-radius: 4px;
    margin-bottom: 20px;

    p {
      margin: 5px 0;
    }
  }
}
</style>
