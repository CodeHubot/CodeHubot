<template>
  <div class="ai-dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card" @click="$router.push('/ai/agents')">
          <div class="stat-content">
            <div class="stat-icon agent">
              <el-icon :size="32"><Avatar /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.agents }}</div>
              <div class="stat-label">智能体</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col v-if="configStore.aiWorkflowEnabled" :span="6">
        <el-card shadow="hover" class="stat-card" @click="$router.push('/ai/workflows')">
          <div class="stat-content">
            <div class="stat-icon workflow">
              <el-icon :size="32"><Connection /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.workflows }}</div>
              <div class="stat-label">工作流</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col v-if="configStore.aiKnowledgeBaseEnabled" :span="6">
        <el-card shadow="hover" class="stat-card" @click="$router.push('/ai/knowledge-bases')">
          <div class="stat-content">
            <div class="stat-icon knowledge">
              <el-icon :size="32"><Collection /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.knowledgeBases }}</div>
              <div class="stat-label">知识库</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card" @click="$router.push('/ai/prompt-templates')">
          <div class="stat-content">
            <div class="stat-icon template">
              <el-icon :size="32"><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.templates }}</div>
              <div class="stat-label">提示词模板</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onActivated } from 'vue'
import { Avatar, Connection, Collection, Document } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getAIStats } from '../api/dashboard'
import { useConfigStore } from '@/stores/config'

const configStore = useConfigStore()

const stats = ref({
  agents: 0,
  workflows: 0,
  knowledgeBases: 0,
  templates: 0
})

const loading = ref(false)

onMounted(() => {
  loadStats()
})

// 当从其他页面返回时刷新统计数据
onActivated(() => {
  loadStats()
})

async function loadStats() {
  try {
    loading.value = true
    const response = await getAIStats()
    stats.value = {
      agents: response.data.agents || 0,
      workflows: response.data.workflows || 0,
      knowledgeBases: response.data.knowledge_bases || 0,
      templates: response.data.templates || 0
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
    ElMessage.error('加载统计数据失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.ai-dashboard {
  .stat-card {
    cursor: pointer;
    transition: all 0.3s;
    
    &:hover {
      transform: translateY(-5px);
    }
    
    .stat-content {
      display: flex;
      align-items: center;
      gap: 20px;
      
      .stat-icon {
        width: 60px;
        height: 60px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        
        &.agent {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        &.workflow {
          background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        
        &.knowledge {
          background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }
        
        &.template {
          background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        }
      }
      
      .stat-info {
        flex: 1;
        
        .stat-value {
          font-size: 32px;
          font-weight: bold;
          color: #2c3e50;
          line-height: 1;
        }
        
        .stat-label {
          font-size: 14px;
          color: #909399;
          margin-top: 8px;
        }
      }
    }
  }
}
</style>
