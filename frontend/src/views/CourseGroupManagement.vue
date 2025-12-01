<template>
  <div class="course-group-management">
    <div class="page-header">
      <el-button @click="$router.back()" type="text" size="large">
        <el-icon><ArrowLeft /></el-icon> 返回学生管理
      </el-button>
      <h2>{{ courseName }} - 学生分组</h2>
    </div>
    
    <el-card>
      <p style="text-align: center; color: #909399; padding: 40px;">学生分组功能开发中...</p>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'

const route = useRoute()
const courseName = ref(route.query.name || '课程')
</script>

<style scoped>
.course-group-management {
  padding: 20px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  padding: 16px;
  background: white;
  border-radius: 4px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
}
</style>
