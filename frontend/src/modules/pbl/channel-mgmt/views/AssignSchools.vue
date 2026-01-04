<template>
  <div class="assign-schools">
    <el-card shadow="never">
      <template #header>
        <div class="header">
          <div>
            <h2 class="page-title">学校分配管理</h2>
            <p class="page-description">为渠道商批量分配或调整学校</p>
          </div>
        </div>
      </template>

      <el-form :inline="true" class="filter-form">
        <el-form-item label="选择渠道商">
          <el-select
            v-model="selectedPartnerId"
            placeholder="请选择渠道商"
            style="width: 300px"
            @change="loadPartnerSchools"
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

      <div v-if="selectedPartnerId" class="assignment-container">
        <el-transfer
          v-model="assignedSchoolIds"
          :data="allSchools"
          :titles="['未分配学校', '已分配学校']"
          filterable
          filter-placeholder="搜索学校"
          style="text-align: left"
        />

        <div class="actions">
          <el-button type="primary" @click="handleSave" :loading="saving">
            保存分配
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </div>
      </div>

      <div v-else class="empty-hint">
        <el-empty description="请先选择一个渠道商" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getChannelPartners,
  getChannelPartnerDetail,
  getAvailableSchools,
  assignSchoolsToPartner
} from '../api'

const partners = ref([])
const selectedPartnerId = ref(null)
const allSchools = ref([])
const assignedSchoolIds = ref([])
const originalAssignedIds = ref([])
const saving = ref(false)

async function loadPartners() {
  try {
    const response = await getChannelPartners()
    partners.value = response.data || []
  } catch (error) {
    ElMessage.error('获取渠道商列表失败')
  }
}

async function loadSchools() {
  try {
    const response = await getAvailableSchools()
    allSchools.value = (response.data || []).map(school => ({
      key: school.uuid,
      label: school.name
    }))
  } catch (error) {
    ElMessage.error('获取学校列表失败')
  }
}

async function loadPartnerSchools() {
  if (!selectedPartnerId.value) return

  try {
    const response = await getChannelPartnerDetail(selectedPartnerId.value)
    const schools = response.data?.schools || []
    assignedSchoolIds.value = schools
      .filter(s => s.is_active)
      .map(s => s.school_uuid)
    originalAssignedIds.value = [...assignedSchoolIds.value]
  } catch (error) {
    ElMessage.error('获取渠道商学校失败')
  }
}

async function handleSave() {
  if (!selectedPartnerId.value) {
    ElMessage.warning('请选择渠道商')
    return
  }

  saving.value = true
  try {
    await assignSchoolsToPartner({
      channel_partner_uuid: selectedPartnerId.value,
      school_uuids: assignedSchoolIds.value
    })
    ElMessage.success('学校分配成功')
    originalAssignedIds.value = [...assignedSchoolIds.value]
  } catch (error) {
    ElMessage.error(error.message || '保存失败')
  } finally {
    saving.value = false
  }
}

function handleReset() {
  assignedSchoolIds.value = [...originalAssignedIds.value]
  ElMessage.info('已重置为原始状态')
}

onMounted(() => {
  loadPartners()
  loadSchools()
})
</script>

<style scoped lang="scss">
.assign-schools {
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .page-title {
      font-size: 20px;
      font-weight: 600;
      color: #2c3e50;
      margin: 0 0 8px 0;
    }

    .page-description {
      color: #909399;
      margin: 0;
    }
  }

  .filter-form {
    margin-bottom: 20px;
  }

  .assignment-container {
    .actions {
      margin-top: 20px;
      text-align: right;
    }
  }

  .empty-hint {
    padding: 60px 0;
  }
}
</style>
