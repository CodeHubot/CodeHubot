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
            <!-- 使用 Markdown 查看器显示输出 -->
            <div v-if="runResult?.output">
              <MarkdownViewer 
                v-if="isMarkdownContent(formattedOutput)"
                :content="formattedOutput"
              />
              <div v-else class="code-block">
                {{ formattedOutput }}
              </div>
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
                    <div v-if="node.status === 'failed'" class="code-block small error">
                      {{ node.error_message }}
                    </div>
                    <template v-else>
                      <MarkdownViewer 
                        v-if="isMarkdownContent(formatOutput(node.output))"
                        :content="formatOutput(node.output)"
                        class="small-viewer"
                      />
                      <div v-else class="code-block small">
                        {{ formatOutput(node.output) }}
                      </div>
                    </template>
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
import MarkdownViewer from '@/components/common/MarkdownViewer.vue'

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
  if (typeof val === 'object' && val !== null) {
    // 如果对象只有一个 output 字段，直接返回 output 的值
    if (Object.keys(val).length === 1 && 'output' in val) {
      return formatOutput(val.output) // 递归处理，防止 output 值也是对象
    }
    // 其他情况格式化为 JSON
    return JSON.stringify(val, null, 2)
  }
  return val
}

// 格式化后的输出（用于显示）
const formattedOutput = computed(() => {
  if (!props.runResult?.output) return ''
  return formatOutput(props.runResult.output)
})

// 判断内容是否包含 Markdown 标记
const isMarkdownContent = (content) => {
  if (!content || typeof content !== 'string') return false
  
  // 检查是否包含常见的 Markdown 标记
  const markdownPatterns = [
    /^#{1,6}\s/m,           // 标题 (# ## ###)
    /\*\*.*?\*\*/,          // 粗体 (**text**)
    /\*.*?\*/,              // 斜体 (*text*)
    /\[.*?\]\(.*?\)/,       // 链接 [text](url)
    /^\s*[-*+]\s/m,         // 无序列表
    /^\s*\d+\.\s/m,         // 有序列表
    /^>\s/m,                // 引用
    /```[\s\S]*?```/,       // 代码块
    /`[^`]+`/,              // 行内代码
    /^\s*\|.+\|/m,          // 表格
    /^---+$/m,              // 分隔线
    /!\[.*?\]\(.*?\)/       // 图片
  ]
  
  // 如果匹配到2个或以上的 Markdown 模式，认为是 Markdown 内容
  const matchCount = markdownPatterns.filter(pattern => pattern.test(content)).length
  return matchCount >= 2
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
  // 清除上一次的执行结果
  hasExecuted.value = false
  runStatus.value = 'pending'
  expandedNodes.value = []
  
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

/* Markdown 查看器样式调整 */
:deep(.small-viewer) {
  font-size: 12px;
}

:deep(.small-viewer .viewer-content) {
  max-height: 300px;
  padding: 12px;
}

:deep(.small-viewer .viewer-toolbar) {
  padding: 6px 10px;
}

:deep(.small-viewer .markdown-body) {
  font-size: 12px;
}
</style>

