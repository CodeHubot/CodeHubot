<template>
  <div class="class-management">
    <div class="page-header">
      <h1>课程管理</h1>
      <el-button type="primary" :icon="Plus" @click="showCreateDialog">
        创建课程
      </el-button>
    </div>

    <!-- 搜索栏 -->
    <el-card class="search-card">
      <el-form :inline="true">
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="课程名称"
            clearable
            @clear="loadCourses"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadCourses">搜索</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 课程列表 -->
    <el-card class="table-card">
      <el-table 
        :data="classes" 
        v-loading="loading" 
        stripe 
        empty-text="暂无班级数据"
        row-key="id"
      >
        <el-table-column prop="course_name" label="课程名称" min-width="250" show-overflow-tooltip />
        <el-table-column label="任课教师" min-width="200">
          <template #default="{ row }">
            <span v-if="row.teachers && row.teachers.length > 0">
              {{ row.teachers.map(t => t.name || t.username).join('、') }}
            </span>
            <span v-else style="color: #999;">未分配</span>
          </template>
        </el-table-column>
        <el-table-column label="学生数" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="primary" effect="plain">{{ row.student_count || 0 }} 人</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="设备组" width="180">
          <template #default="{ row }">
            <div v-if="row.device_groups && row.device_groups.length > 0">
              <el-tag 
                v-for="(group, index) in row.device_groups" 
                :key="group.group_id"
                type="success"
                size="small"
                effect="plain"
                style="margin: 2px;"
              >
                {{ group.group_name }} ({{ group.device_count }}设备)
              </el-tag>
            </div>
            <span v-else style="color: #999; font-size: 12px;">未授权</span>
          </template>
        </el-table-column>
        <el-table-column label="分组数" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="warning" effect="plain">{{ row.group_count || 0 }} 组</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active !== false ? 'success' : 'info'" size="small">
              {{ row.is_active !== false ? '激活' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="400">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="manageTeachers(row)">
              <el-icon><User /></el-icon> 教师
            </el-button>
            <el-button link type="success" size="small" @click="manageStudents(row)">
              <el-icon><UserFilled /></el-icon> 学生
            </el-button>
            <el-button link type="info" size="small" @click="viewClassDetail(row)">
              <el-icon><View /></el-icon> 详情
            </el-button>
            <el-button link type="warning" size="small" @click="editClass(row)">
              <el-icon><Edit /></el-icon> 编辑
            </el-button>
            <el-button link type="danger" size="small" @click="handleDelete(row)">
              <el-icon><Delete /></el-icon> 删除
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
          @current-change="loadCourses"
          @size-change="loadCourses"
        />
      </div>
    </el-card>

    <!-- 创建/编辑课程对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '创建课程' : '编辑课程'"
      width="600px"
    >
      <el-form
        ref="courseFormRef"
        :model="courseForm"
        :rules="classRules"
        label-width="100px"
        autocomplete="off"
      >
        <el-form-item label="课程名称" prop="course_name">
          <el-input 
            v-model="courseForm.course_name" 
            placeholder="如：三年级信息技术课" 
            autocomplete="off"
          />
          <span class="form-tip">建议格式：年级+课程名称，便于管理和识别</span>
        </el-form-item>
        <el-form-item label="课程描述" prop="description">
          <el-input
            v-model="courseForm.description"
            type="textarea"
            :rows="2"
            placeholder="课程简介（可选）"
            autocomplete="off"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ dialogMode === 'create' ? '创建' : '保存' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 课程详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="课程详情"
      width="800px"
    >
      <div v-if="currentCourse" class="detail-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="课程名称">
            {{ currentCourse.course_name }}
          </el-descriptions-item>
          <el-descriptions-item label="任课教师" :span="2">
            <span v-if="currentCourse.teachers && currentCourse.teachers.length > 0">
              <el-tag
                v-for="teacher in currentCourse.teachers"
                :key="teacher.id"
                style="margin-right: 8px;"
              >
                {{ teacher.name || teacher.username }}
              </el-tag>
            </span>
            <span v-else style="color: #999;">未分配</span>
          </el-descriptions-item>
          <el-descriptions-item label="学生数">
            <el-tag type="primary">{{ currentCourse.student_count || 0 }} 人</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="分组数">
            <el-tag type="warning">{{ currentCourse.group_count || 0 }} 组</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="授权设备组" :span="2">
            <div v-if="currentCourse.device_groups && currentCourse.device_groups.length > 0">
              <el-tag
                v-for="group in currentCourse.device_groups"
                :key="group.group_id"
                type="success"
                style="margin-right: 8px; margin-bottom: 4px;"
              >
                {{ group.group_name }} ({{ group.device_count }}台设备)
              </el-tag>
              <div style="margin-top: 8px; color: #999; font-size: 12px;">
                共 {{ currentCourse.total_devices || 0 }} 台设备
              </div>
            </div>
            <span v-else style="color: #999;">未授权设备组</span>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="currentCourse.is_active ? 'success' : 'info'">
              {{ currentCourse.is_active ? '激活' : '禁用' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDate(currentCourse.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="课程描述" :span="2">
            {{ currentCourse.description || '无' }}
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 复制课程对话框 -->
    <el-dialog
      v-model="copyDialogVisible"
      title="复制课程到新学年"
      width="500px"
    >
      <el-alert
        title="复制功能说明"
        type="info"
        :closable="false"
        style="margin-bottom: 15px;"
      >
        <p>将复制以下内容到新班级：</p>
        <ul style="margin: 10px 0; padding-left: 20px;">
          <li>所有小组结构</li>
          <li>所有学生成员</li>
          <li>学生的小组分配关系</li>
        </ul>
      </el-alert>

      <el-form
        ref="copyFormRef"
        :model="copyForm"
        :rules="copyRules"
        label-width="100px"
        autocomplete="off"
      >
        <el-form-item label="原课程">
          <el-input :value="copyForm.source_course_name" disabled />
        </el-form-item>
        <el-form-item label="新课程名称" prop="new_course_name">
          <el-input 
            v-model="copyForm.new_course_name" 
            placeholder="如：四年级信息技术课"
            autocomplete="off"
          />
          <span class="form-tip">建议格式：年级+课程名称</span>
        </el-form-item>
        <el-form-item label="课程描述" prop="description">
          <el-input
            v-model="copyForm.description"
            type="textarea"
            :rows="2"
            placeholder="新课程的描述（可选）"
            autocomplete="off"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="copyDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCopyClass" :loading="submitting">
          确认复制
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, View, Edit, Delete, CopyDocument, User, UserFilled } from '@element-plus/icons-vue'
import {
  getCourses, createCourse, updateCourse, deleteCourse as deleteCourseAPI,
  getCourseTeachers, addCourseTeacher, removeCourseTeacher
} from '@/api/courses'
import { getUsers } from '@/api/userManagement'
import { formatDate } from '@/utils/format'
import { useUserStore } from '@/store/user'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const submitting = ref(false)
const classes = ref([])
const dialogVisible = ref(false)
const detailDialogVisible = ref(false)
const copyDialogVisible = ref(false)
const dialogMode = ref('create')

const courseFormRef = ref(null)
const copyFormRef = ref(null)

const currentCourse = ref(null)

// 搜索表单
const searchForm = reactive({
  keyword: ''
})

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 课程表单（简化版）
const courseForm = reactive({
  course_name: '',
  description: ''
})

// 复制课程表单
const copyForm = reactive({
  source_class_uuid: null,
  source_course_name: '',
  new_course_name: '',
  description: ''
})

const classRules = {
  course_name: [
    { required: true, message: '请输入课程名称', trigger: 'blur' },
    { min: 1, max: 100, message: '长度在 1 到 100 个字符', trigger: 'blur' }
  ]
}

const copyRules = {
  new_course_name: [
    { required: true, message: '请输入新课程名称', trigger: 'blur' },
    { min: 1, max: 100, message: '长度在 1 到 100 个字符', trigger: 'blur' }
  ]
}

// 页面加载
onMounted(() => {
  loadCourses()
})

// 加载课程列表
const loadCourses = async () => {
  try {
    loading.value = true
    
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      keyword: searchForm.keyword
    }
    
    // 根据角色添加过滤条件
    if (userStore.isSchoolAdmin || userStore.isTeacher) {
      params.school_id = userStore.userInfo.school_id
    }
    
    const response = await getCourses(params)
    const data = response.data || response
    
    classes.value = data.courses || []
    pagination.total = data.total || 0
  } catch (error) {
    const errorMsg = error.response?.data?.message || error.message
    ElMessage.error(`加载班级失败: ${errorMsg}`)
  } finally {
    loading.value = false
  }
}

// 重置搜索
const resetSearch = () => {
  searchForm.keyword = ''
  loadCourses()
}

// 显示创建对话框
const showCreateDialog = () => {
  dialogMode.value = 'create'
  resetClassForm()
  dialogVisible.value = true
}

// 查看详情
const viewClassDetail = (courseItem) => {
  currentCourse.value = courseItem
  detailDialogVisible.value = true
}

// 管理教师
const manageTeachers = (courseItem) => {
  router.push({
    path: `/courses/${courseItem.uuid}/teachers`,
    query: { name: courseItem.course_name }
  })
}

// 管理学生
const manageStudents = (courseItem) => {
  router.push({
    path: `/courses/${courseItem.uuid}/students`,
    query: { name: courseItem.course_name }
  })
}

// 编辑课程
const editClass = (courseItem) => {
  dialogMode.value = 'edit'
  currentCourse.value = courseItem
  Object.assign(courseForm, {
    course_name: courseItem.course_name,
    description: courseItem.description || ''
  })
  dialogVisible.value = true
}

// 提交表单
const handleSubmit = async () => {
  if (!courseFormRef.value) return
  
  await courseFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    try {
      submitting.value = true
      
      const data = { ...courseForm }
      
      // 处理空字符串，转换为null
      Object.keys(data).forEach(key => {
        if (data[key] === '') {
          data[key] = null
        }
      })
      
      // 添加school_id
      if (userStore.isSchoolAdmin || userStore.isTeacher) {
        data.school_id = userStore.userInfo.school_id
      }
      
      if (dialogMode.value === 'create') {
        await createCourse(data)
        ElMessage.success('班级创建成功')
      } else {
        await updateCourse(currentCourse.value.uuid, data)
        ElMessage.success('班级更新成功')
      }
      
      dialogVisible.value = false
      loadCourses()
    } catch (error) {
      const errorMsg = error.response?.data?.message || error.message
      ElMessage.error(`操作失败: ${errorMsg}`)
    } finally {
      submitting.value = false
    }
  })
}

// 删除课程
const handleDelete = async (courseItem) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除课程"${courseItem.course_name}"吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await deleteCourse(courseItem.uuid)
    ElMessage.success('班级已删除')
    loadCourses()
    
  } catch (error) {
    if (error !== 'cancel') {
      const errorMsg = error.response?.data?.message || error.message
      ElMessage.error(`删除失败: ${errorMsg}`)
    }
  }
}

// 复制课程
const copyCourse = (courseItem) => {
  // 自动生成新课程名称（递增年级）
  const suggestedName = courseItem.course_name.replace(/[一二三四五六]年级/, (match) => {
    const grades = { '一': '二', '二': '三', '三': '四', '四': '五', '五': '六' }
    return grades[match[0]] ? grades[match[0]] + '年级' : match
  })
  
  Object.assign(copyForm, {
    source_class_uuid: courseItem.uuid,
    source_course_name: courseItem.course_name,
    new_course_name: suggestedName,
    description: courseItem.description || ''
  })
  
  copyDialogVisible.value = true
}

// 执行复制课程
const handleCopyClass = async () => {
  if (!copyFormRef.value) return
  
  await copyFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    try {
      submitting.value = true
      
      const data = {
        new_course_name: copyForm.new_course_name,
        description: copyForm.description || null
      }
      
      await copyCourseAPI(copyForm.source_class_uuid, data)
      
      ElMessage.success({
        message: '班级复制成功！所有小组和学生已同步到新班级',
        duration: 3000
      })
      
      copyDialogVisible.value = false
      loadCourses()
    } catch (error) {
      const errorMsg = error.response?.data?.message || error.message
      ElMessage.error(`复制失败: ${errorMsg}`)
    } finally {
      submitting.value = false
    }
  })
}

// 重置表单
const resetClassForm = () => {
  Object.assign(courseForm, {
    course_name: '',
    description: ''
  })
  courseFormRef.value?.clearValidate()
}
</script>

<style scoped>
.class-management {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  color: #303133;
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

.form-tip {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
  line-height: 1.5;
}

.detail-content {
  padding: 10px 0;
}

.teacher-management {
  padding: 10px 0;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 15px;
}

.section-title .el-icon {
  font-size: 18px;
  color: #409EFF;
}
</style>
