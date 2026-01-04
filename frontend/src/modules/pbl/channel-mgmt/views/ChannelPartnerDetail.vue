<template>
  <div class="channel-partner-detail">
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <span class="page-title">{{ partnerInfo.name }}</span>
      </template>
    </el-page-header>

    <el-row :gutter="20" v-loading="loading">
      <!-- 基本信息 -->
      <el-col :span="24">
        <el-card class="info-card" shadow="never">
          <template #header>
            <span class="card-title">渠道商信息</span>
          </template>
          
          <el-descriptions :column="2" border>
            <el-descriptions-item label="账号">{{ partnerInfo.username }}</el-descriptions-item>
            <el-descriptions-item label="渠道商名称">{{ partnerInfo.name }}</el-descriptions-item>
            <el-descriptions-item label="公司名称">{{ partnerInfo.company_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="联系电话">{{ partnerInfo.phone || '-' }}</el-descriptions-item>
            <el-descriptions-item label="邮箱">{{ partnerInfo.email || '-' }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="partnerInfo.is_active ? 'success' : 'info'">
                {{ partnerInfo.is_active ? '正常' : '已禁用' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">
              {{ formatDate(partnerInfo.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="最后登录">
              {{ formatDate(partnerInfo.last_login) }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>

      <!-- 负责的学校 -->
      <el-col :span="24" style="margin-top: 20px">
        <el-card class="schools-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="card-title">负责的学校（{{ schools.length }}所）</span>
              <el-button type="primary" size="small" @click="showAssignDialog">
                分配学校
              </el-button>
            </div>
          </template>
          
          <el-table :data="schools" style="width: 100%">
            <el-table-column prop="school_name" label="学校名称" min-width="200" />
            <el-table-column prop="is_active" label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'info'">
                  {{ row.is_active ? '正常' : '已停用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="assigned_at" label="分配时间" width="180">
              <template #default="{ row }">
                {{ formatDate(row.assigned_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" align="center">
              <template #default="{ row }">
                <el-button
                  v-if="row.is_active"
                  size="small"
                  type="danger"
                  @click="removeSchool(row)"
                >
                  解除关联
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <div v-if="schools.length === 0" class="empty-state">
            <el-empty description="暂未分配学校" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 分配学校对话框 -->
    <el-dialog v-model="assignDialogVisible" title="分配学校" width="600px">
      <el-transfer
        v-model="selectedSchools"
        :data="availableSchools"
        :titles="['可分配学校', '已选学校']"
        filterable
        filter-placeholder="搜索学校"
      />
      <template #footer>
        <el-button @click="assignDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAssign" :loading="assigning">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getChannelPartnerDetail,
  getAvailableSchools,
  assignSchoolsToPartner,
  removeSchoolFromPartner
} from '../api'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const partnerInfo = ref({})
const schools = ref([])
const assignDialogVisible = ref(false)
const availableSchools = ref([])
const selectedSchools = ref([])
const assigning = ref(false)

function goBack() {
  router.push({ name: 'AdminChannelPartners' })
}

async function fetchDetail() {
  loading.value = true
  try {
    const partnerId = route.params.partnerId
    const response = await getChannelPartnerDetail(partnerId)
    partnerInfo.value = response.data || {}
    schools.value = response.data?.schools || []
  } catch (error) {
    console.error('获取渠道商详情失败:', error)
    ElMessage.error(error.message || '获取渠道商详情失败')
  } finally {
    loading.value = false
  }
}

async function showAssignDialog() {
  try {
    const response = await getAvailableSchools()
    availableSchools.value = (response.data || []).map(school => ({
      key: school.uuid,
      label: school.name
    }))
    
    // 预选已分配的学校
    selectedSchools.value = schools.value
      .filter(s => s.is_active)
      .map(s => s.school_uuid)
    
    assignDialogVisible.value = true
  } catch (error) {
    ElMessage.error(error.message || '获取学校列表失败')
  }
}

async function handleAssign() {
  if (selectedSchools.value.length === 0) {
    ElMessage.warning('请至少选择一所学校')
    return
  }

  assigning.value = true
  try {
    await assignSchoolsToPartner({
      channel_partner_uuid: route.params.partnerId,
      school_uuids: selectedSchools.value
    })
    ElMessage.success('学校分配成功')
    assignDialogVisible.value = false
    fetchDetail()
  } catch (error) {
    ElMessage.error(error.message || '学校分配失败')
  } finally {
    assigning.value = false
  }
}

function removeSchool(school) {
  ElMessageBox.confirm(
    `确定要解除与 ${school.school_name} 的关联吗？`,
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await removeSchoolFromPartner(partnerInfo.value.uuid, school.school_uuid)
      ElMessage.success('关联已解除')
      fetchDetail()
    } catch (error) {
      ElMessage.error(error.message || '操作失败')
    }
  }).catch(() => {})
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return dateStr.split('T')[0] + ' ' + dateStr.split('T')[1]?.split('.')[0]
}

onMounted(() => {
  fetchDetail()
})
</script>

<style scoped lang="scss">
.channel-partner-detail {
  .page-header {
    margin-bottom: 20px;
    background: white;
    padding: 16px 20px;
    border-radius: 4px;
    
    .page-title {
      font-size: 18px;
      font-weight: 600;
      color: #2c3e50;
    }
  }
  
  .card-title {
    font-size: 16px;
    font-weight: 600;
    color: #2c3e50;
  }
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .empty-state {
    padding: 40px 0;
  }
}
</style>
