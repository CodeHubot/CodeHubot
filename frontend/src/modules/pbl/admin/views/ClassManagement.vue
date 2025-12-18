<template>
  <div class="class-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>班级管理</span>
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>
            新建班级
          </el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="班级名称">
          <el-input v-model="searchForm.name" placeholder="请输入班级名称" clearable />
        </el-form-item>
        <el-form-item label="班级类型">
          <el-select v-model="searchForm.class_type" placeholder="请选择班级类型" clearable>
            <el-option label="普通班" value="regular" />
            <el-option label="项目班" value="project" />
            <el-option label="社团班" value="club" />
            <el-option label="兴趣班" value="interest" />
            <el-option label="竞赛班" value="competition" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 表格 -->
      <el-table :data="classes" style="width: 100%" v-loading="loading">
        <el-table-column prop="name" label="班级名称" min-width="200" />
        <el-table-column label="班级类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getClassTypeTag(row.class_type)">
              {{ getClassTypeName(row.class_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="current_members" label="当前人数" width="100" />
        <el-table-column prop="description" label="描述" min-width="250" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleView(row)">查看</el-button>
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="primary" @click="handleMembers(row)">成员</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        style="margin-top: 20px; justify-content: flex-end;"
      />
    </el-card>

    <!-- 新建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="handleDialogClose"
    >
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="班级名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入班级名称" />
        </el-form-item>
        <el-form-item label="班级类型" prop="class_type">
          <el-select v-model="formData.class_type" placeholder="请选择班级类型" style="width: 100%">
            <el-option label="普通班" value="regular" />
            <el-option label="项目班" value="project" />
            <el-option label="社团班" value="club" />
            <el-option label="兴趣班" value="interest" />
            <el-option label="竞赛班" value="competition" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input 
            v-model="formData.description" 
            type="textarea" 
            :rows="3"
            placeholder="请输入描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

const router = useRouter()

// 搜索表单
const searchForm = reactive({
  name: '',
  class_type: ''
})

// 表格数据
const classes = ref([])
const loading = ref(false)

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

// 对话框
const dialogVisible = ref(false)
const dialogTitle = ref('新建班级')
const formRef = ref(null)
const formData = reactive({
  name: '',
  class_type: '',
  description: ''
})

// 表单验证规则
const rules = {
  name: [{ required: true, message: '请输入班级名称', trigger: 'blur' }],
  class_type: [{ required: true, message: '请选择班级类型', trigger: 'change' }]
}

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    // TODO: 调用 API 获取数据
    classes.value = []
    pagination.total = 0
  } catch (error) {
    ElMessage.error('加载数据失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  loadData()
}

// 重置
const handleReset = () => {
  searchForm.name = ''
  searchForm.class_type = ''
  handleSearch()
}

// 新增
const handleAdd = () => {
  dialogTitle.value = '新建班级'
  dialogVisible.value = true
}

// 查看
const handleView = (row) => {
  router.push(`/pbl/admin/classes/${row.uuid}`)
}

// 编辑
const handleEdit = (row) => {
  dialogTitle.value = '编辑班级'
  Object.assign(formData, row)
  dialogVisible.value = true
}

// 成员管理
const handleMembers = (row) => {
  router.push(`/pbl/admin/classes/${row.uuid}/members`)
}

// 删除
const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该班级吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    // TODO: 调用删除 API
    ElMessage.success('删除成功')
    loadData()
  }).catch(() => {})
}

// 提交表单
const handleSubmit = () => {
  formRef.value.validate((valid) => {
    if (valid) {
      // TODO: 调用保存 API
      ElMessage.success('保存成功')
      dialogVisible.value = false
      loadData()
    }
  })
}

// 关闭对话框
const handleDialogClose = () => {
  formRef.value?.resetFields()
  Object.assign(formData, {
    name: '',
    class_type: '',
    description: ''
  })
}

// 分页改变
const handleSizeChange = (val) => {
  pagination.pageSize = val
  loadData()
}

const handleCurrentChange = (val) => {
  pagination.page = val
  loadData()
}

// 获取班级类型名称
const getClassTypeName = (type) => {
  const map = {
    regular: '普通班',
    project: '项目班',
    club: '社团班',
    interest: '兴趣班',
    competition: '竞赛班'
  }
  return map[type] || type
}

// 获取班级类型标签
const getClassTypeTag = (type) => {
  const map = {
    regular: 'info',
    project: 'success',
    club: 'primary',
    interest: 'warning',
    competition: 'danger'
  }
  return map[type] || 'info'
}

// 初始化
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.class-management {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-form {
  margin-bottom: 20px;
}
</style>


