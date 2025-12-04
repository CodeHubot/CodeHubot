<template>
  <div class="execution-panel">
    <div class="panel-header">
      <h3 class="panel-title">运行工作流</h3>
      <el-button circle text @click="$emit('close')">
        <el-icon><Close /></el-icon>
      </el-button>
    </div>

    <div class="panel-content">
      <!-- 输入参数区域 -->
      <div class="section-card">
        <div class="section-header">
          <el-icon><Edit /></el-icon>
          <span>输入变量</span>
        </div>
        
        <div class="params-form">
          <template v-if="startNodeParams.length > 0">
            <el-form :model="runParams" label-position="top">
              <el-form-item
                v-for="param in startNodeParams"
                :key="param.name"
                :label="param.name + (param.description ? ` (${param.description})` : '')"
                :required="param.required"
              >
                <el-input
                  v-if="param.type === 'string'"
                  v-model="runParams[param.name]"
                  :placeholder="'请输入 ' + param.name"
                  type="textarea"
                  :rows="2"
                />
                <el-input-number
                  v-else-if="param.type === 'number'"
                  v-model="runParams[param.name]"
                  style="width: 100%"
                />
                <el-switch
                  v-else-if="param.type === 'boolean'"
                  v-model="runParams[param.name]"
                />
                <el-input
                  v-else
                  v-model="runParams[param.name]"
                />
              </el-form-item>
            </el-form>
          </template>
          <div v-else class="empty-state">
            <span>无需输入参数</span>
          </div>
          
          <el-button 
            type="primary" 
            class="run-btn" 
            :loading="running" 
            @click="handleRun"
            :icon="VideoPlay"
          >
            {{ running ? '执行中...' : '开始运行' }}
          </el-button>
        </div>
      </div>

      <!-- 执行结果区域 -->
      <div v-if="hasExecuted" class="result-area">
        <el-divider content-position="center">执行结果</el-divider>
        
        <!-- 最终输出 -->
        <div class="section-card result-card">
          <div class="section-header">
            <div class="header-left">
              <el-icon><checked /></el-icon>
              <span>最终输出</span>
            </div>
            <el-tag :type="runStatus === 'completed' ? 'success' : 'danger'" size="small">
              {{ runStatus === 'completed' ? '成功' : '失败' }}
            </el-tag>
          </div>
          
          <div class="output-content">
            <div v-if="runResult?.output" class="code-block">
              {{ formatOutput(runResult.output) }}
            </div>
            <div v-if="runResult?.error_message" class="error-msg">
              {{ runResult.error_message }}
            </div>
            <div class="meta-info">
              <span>耗时: {{ runResult?.execution_time || 0 }}ms</span>
            </div>
          </div>
        </div>

        <!-- 节点执行详情 -->
        <div class="node-executions">
          <div class="section-header sub">
            <span>节点执行详情</span>
          </div>
          
          <el-timeline>
            <el-timeline-item
              v-for="node in sortedNodeExecutions"
              :key="node.node_id"
              :type="node.status === 'success' ? 'success' : 'danger'"
              :timestamp="formatTime(node.completed_at)"
              placement="top"
              hide-timestamp
            >
              <div class="node-card">
                <div class="node-header" @click="toggleNodeDetail(node.node_id)">
                  <div class="node-title">
                    <el-icon class="status-icon" :class="node.status">
                      <component :is="node.status === 'success' ? 'CircleCheck' : 'CircleClose'" />
                    </el-icon>
                    <span class="node-name">{{ getNodeLabel(node.node_id) }}</span>
                    <el-tag size="small" type="info" effect="plain">{{ node.node_type }}</el-tag>
                  </div>
                  <div class="node-meta">
                    <span class="duration">{{ node.execution_time }}ms</span>
                    <el-icon class="expand-icon" :class="{ expanded: expandedNodes.includes(node.node_id) }">
                      <ArrowRight />
                    </el-icon>
                  </div>
                </div>

                <div v-show="expandedNodes.includes(node.node_id)" class="node-detail">
                  <!-- 节点输入 -->
                  <div class="detail-section" v-if="nodeInputs[node.node_id]">
                    <div class="detail-label">输入</div>
                    <div class="code-block small">
                      {{ formatOutput(nodeInputs[node.node_id]) }}
                    </div>
                  </div>
                  
                  <!-- 节点输出 -->
                  <div class="detail-section">
                    <div class="detail-label">输出</div>
                    <div class="code-block small" :class="{ error: node.status === 'failed' }">
                      {{ node.status === 'failed' ? node.error_message : formatOutput(node.output) }}
                    </div>
                  </div>
                </div>
              </div>
            </el-timeline-item>
          </el-timeline>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { VideoPlay, Close, Edit, Checked, CircleCheck, CircleClose, ArrowRight } from '@element-plus/icons-vue'
import dayjs from 'dayjs'

const props = defineProps({
  nodes: {
    type: Array,
    default: () => []
  },
  startNodeParams: {
    type: Array,
    default: () => []
  },
  running: {
    type: Boolean,
    default: false
  },
  runResult: {
    type: Object,
    default: null
  },
  // 传递整个 execution context 或许更好，但现在先简单处理
  // 假设父组件能计算出每个节点的输入（这个比较难，暂时只显示输出）
  // 可以在 execute workflow 返回结果中带上 input，或者后端修改返回结构
  // 目前后端只返回了 output
})

const emit = defineEmits(['close', 'run'])

const runParams = ref({})
const hasExecuted = ref(false)
const expandedNodes = ref([])
const runStatus = ref('pending')

// 监听参数定义变化，初始化输入值
watch(() => props.startNodeParams, (params) => {
  const newParams = {}
  params.forEach(p => {
    if (p.type === 'boolean') {
      newParams[p.name] = false
    } else {
      newParams[p.name] = ''
    }
  })
  runParams.value = newParams
}, { immediate: true })

// 监听运行结果
watch(() => props.runResult, (res) => {
  if (res) {
    hasExecuted.value = true
    runStatus.value = res.status
    // 默认展开所有失败节点
    if (res.node_executions) {
      res.node_executions.forEach(node => {
        if (node.status === 'failed') {
          expandedNodes.value.push(node.node_id)
        }
      })
    }
  }
})

// 模拟节点输入数据（目前后端未返回，暂留空或尝试从 output 推断）
// 实际上要显示输入，需要后端记录每个节点的 input
const nodeInputs = computed(() => {
  return {} 
})

const sortedNodeExecutions = computed(() => {
  if (!props.runResult?.node_executions) return []
  // 按开始时间排序
  return [...props.runResult.node_executions].sort((a, b) => {
    return new Date(a.started_at) - new Date(b.started_at)
  })
})

const getNodeLabel = (nodeId) => {
  const node = props.nodes.find(n => n.id === nodeId)
  return node?.data?.label || nodeId
}

const formatOutput = (val) => {
  if (typeof val === 'object') {
    return JSON.stringify(val, null, 2)
  }
  return val
}

const formatTime = (time) => {
  return dayjs(time).format('HH:mm:ss')
}

const toggleNodeDetail = (nodeId) => {
  const index = expandedNodes.value.indexOf(nodeId)
  if (index > -1) {
    expandedNodes.value.splice(index, 1)
  } else {
    expandedNodes.value.push(nodeId)
  }
}

const handleRun = () => {
  emit('run', runParams.value)
}
</script>

<style scoped>
.execution-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-left: 1px solid #e4e7ed;
  width: 100%;
}

.panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.section-card {
  background: #fff;
  border-radius: 8px;
  margin-bottom: 20px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.section-header.sub {
  font-size: 13px;
  color: #606266;
  margin-bottom: 12px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.empty-state {
  padding: 20px;
  text-align: center;
  color: #909399;
  font-size: 13px;
  background: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 16px;
}

.run-btn {
  width: 100%;
  margin-top: 8px;
}

.result-card {
  background: #f8f9fa;
  border: 1px solid #ebeef5;
  padding: 16px;
}

.output-content {
  margin-top: 12px;
}

.code-block {
  background: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 12px;
  font-family: monospace;
  font-size: 13px;
  color: #303133;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 300px;
  overflow-y: auto;
}

.code-block.small {
  padding: 8px;
  font-size: 12px;
  max-height: 200px;
}

.error-msg {
  color: #f56c6c;
  background: #fef0f0;
  padding: 12px;
  border-radius: 4px;
  font-size: 13px;
}

.meta-info {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
  text-align: right;
}

.node-executions {
  margin-top: 24px;
}

.node-card {
  border: 1px solid #ebeef5;
  border-radius: 6px;
  overflow: hidden;
  background: #fff;
  transition: all 0.3s;
}

.node-card:hover {
  border-color: #c0c4cc;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.node-header {
  padding: 10px 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  background: #fff;
}

.node-header:hover {
  background: #f5f7fa;
}

.node-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.node-name {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
}

.node-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.duration {
  font-size: 12px;
  color: #909399;
  min-width: 45px;
  text-align: right;
}

.status-icon {
  font-size: 16px;
}

.status-icon.success {
  color: #67c23a;
}

.status-icon.failed {
  color: #f56c6c;
}

.expand-icon {
  font-size: 12px;
  color: #909399;
  transition: transform 0.3s;
}

.expand-icon.expanded {
  transform: rotate(90deg);
}

.node-detail {
  border-top: 1px solid #ebeef5;
  padding: 12px;
  background: #fafafa;
}

.detail-section {
  margin-bottom: 12px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.detail-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.code-block.error {
  border-color: #fde2e2;
  background: #fef0f0;
  color: #f56c6c;
}

/* 调整表单间距 */
:deep(.el-form-item) {
  margin-bottom: 16px;
}

:deep(.el-input-number) {
  width: 100%;
}
</style>

