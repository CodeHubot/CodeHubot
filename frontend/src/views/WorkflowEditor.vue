<template>
  <div class="workflow-editor-container">
    <div class="editor-header">
      <div class="header-left">
        <el-button @click="goBack">返回</el-button>
        <h2>{{ workflowName || '新建工作流' }}</h2>
      </div>
      <div class="header-right">
        <el-button @click="validateWorkflow">验证</el-button>
        <el-button type="primary" @click="saveWorkflow" :loading="saving">保存</el-button>
      </div>
    </div>

    <div class="editor-content">
      <!-- 节点库 -->
      <div class="node-library">
        <h3>节点库</h3>
        <div class="node-types">
          <div
            v-for="nodeType in nodeTypes"
            :key="nodeType.type"
            class="node-type-item"
            draggable="true"
            @dragstart="handleDragStart($event, nodeType)"
          >
            <el-icon><component :is="nodeType.icon" /></el-icon>
            <span>{{ nodeType.label }}</span>
          </div>
        </div>
      </div>

      <!-- 画布区域 -->
      <div class="canvas-container">
        <VueFlow
          :nodes="nodes"
          :edges="edges"
          :default-viewport="{ zoom: 1 }"
          :min-zoom="0.2"
          :max-zoom="4"
          @nodes-change="onNodesChange"
          @edges-change="onEdgesChange"
          @node-click="onNodeClick"
          @pane-click="onPaneClick"
          @drop="onDrop"
          @dragover="onDragOver"
          @connect="onConnect"
        >
          <Background />
          <Controls />
          <MiniMap />
        </VueFlow>
      </div>

      <!-- 配置面板 -->
      <div class="config-panel" v-if="selectedNode">
        <h3>节点配置</h3>
        <el-form :model="selectedNode.data" label-width="100px">
          <el-form-item label="节点ID">
            <el-input v-model="selectedNode.id" disabled />
          </el-form-item>
          <el-form-item label="节点标签">
            <el-input v-model="selectedNode.label" />
          </el-form-item>
          <!-- 根据节点类型显示不同的配置 -->
          <component
            :is="getConfigComponent(selectedNode.type)"
            v-if="selectedNode"
            :node="selectedNode"
            @update="updateNodeData"
          />
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Play,
  Connection,
  Document,
  Search,
  ChatDotRound,
  Operation,
  CircleCheck
} from '@element-plus/icons-vue'
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import {
  getWorkflow,
  createWorkflow,
  updateWorkflow,
  validateWorkflow as validateWorkflowAPI
} from '@/api/workflow'
import StartNodeConfig from '@/components/workflow/node-configs/StartNodeConfig.vue'
import LLMNodeConfig from '@/components/workflow/node-configs/LLMNodeConfig.vue'
import HTTPNodeConfig from '@/components/workflow/node-configs/HTTPNodeConfig.vue'
import KnowledgeNodeConfig from '@/components/workflow/node-configs/KnowledgeNodeConfig.vue'
import IntentNodeConfig from '@/components/workflow/node-configs/IntentNodeConfig.vue'
import StringNodeConfig from '@/components/workflow/node-configs/StringNodeConfig.vue'
import EndNodeConfig from '@/components/workflow/node-configs/EndNodeConfig.vue'

const route = useRoute()
const router = useRouter()
const { project } = useVueFlow()

// 工作流数据
const workflowName = ref('')
const workflowUuid = ref(route.params.uuid)
const nodes = ref([])
const edges = ref([])
const saving = ref(false)

// Vue Flow元素（nodes + edges）
const elements = computed(() => [...nodes.value, ...edges.value])

// 选中的节点
const selectedNode = ref(null)

// 节点ID计数器
let nodeIdCounter = 1

// 节点类型定义
const nodeTypes = [
  { type: 'start', label: '开始', icon: 'Play' },
  { type: 'llm', label: 'LLM', icon: 'ChatDotRound' },
  { type: 'http', label: 'HTTP', icon: 'Connection' },
  { type: 'knowledge', label: '知识库', icon: 'Document' },
  { type: 'intent', label: '意图识别', icon: 'Search' },
  { type: 'string', label: '字符串处理', icon: 'Operation' },
  { type: 'end', label: '结束', icon: 'CircleCheck' }
]

// 拖拽处理
const handleDragStart = (event, nodeType) => {
  event.dataTransfer.setData('nodeType', JSON.stringify(nodeType))
  event.dataTransfer.effectAllowed = 'copy'
}

// 画布拖拽处理
const onDragOver = (event) => {
  event.preventDefault()
  event.dataTransfer.dropEffect = 'copy'
}

const onDrop = (event) => {
  event.preventDefault()
  const nodeTypeData = event.dataTransfer.getData('nodeType')
  if (!nodeTypeData) return
  
  try {
    const nodeType = JSON.parse(nodeTypeData)
    // 获取画布位置
    const rect = event.currentTarget.getBoundingClientRect()
    const position = project({ 
      x: event.clientX - rect.left, 
      y: event.clientY - rect.top 
    })
    
    const newNode = {
      id: `${nodeType.type}-${nodeIdCounter++}`,
      type: 'default',
      label: nodeType.label,
      position,
      data: {
        type: nodeType.type,
        label: nodeType.label
      },
      style: {
        background: getNodeColor(nodeType.type),
        color: '#fff',
        border: `1px solid ${getNodeColor(nodeType.type)}`,
        borderRadius: '8px',
        padding: '10px',
        minWidth: '150px'
      }
    }
    
    nodes.value.push(newNode)
  } catch (error) {
    console.error('添加节点失败:', error)
  }
}

// 节点变化处理
const onNodesChange = (changes) => {
  changes.forEach(change => {
    if (change.type === 'position' && change.dragging === false) {
      const node = nodes.value.find(n => n.id === change.id)
      if (node) {
        node.position = change.position
      }
    } else if (change.type === 'remove') {
      nodes.value = nodes.value.filter(n => n.id !== change.id)
      // 同时删除相关的边
      edges.value = edges.value.filter(e => e.source !== change.id && e.target !== change.id)
    } else if (change.type === 'select' && change.selected) {
      // 节点被选中
      selectedNode.value = nodes.value.find(n => n.id === change.id)
    }
  })
}

// 边变化处理
const onEdgesChange = (changes) => {
  changes.forEach(change => {
    if (change.type === 'remove') {
      edges.value = edges.value.filter(e => e.id !== change.id)
    }
  })
}

// 连接处理（创建新边）
const onConnect = (connection) => {
  const newEdge = {
    id: `edge-${connection.source}-${connection.target}`,
    source: connection.source,
    target: connection.target,
    sourceHandle: connection.sourceHandle,
    targetHandle: connection.targetHandle
  }
  edges.value.push(newEdge)
}

// 节点点击处理
const onNodeClick = (event) => {
  selectedNode.value = event.node
}

// 画布点击处理（取消选中）
const onPaneClick = () => {
  selectedNode.value = null
}

// 获取配置组件
const getConfigComponent = (nodeType) => {
  const components = {
    start: 'StartNodeConfig',
    llm: 'LLMNodeConfig',
    http: 'HTTPNodeConfig',
    knowledge: 'KnowledgeNodeConfig',
    intent: 'IntentNodeConfig',
    string: 'StringNodeConfig',
    end: 'EndNodeConfig'
  }
  return components[nodeType] || null
}

// 更新节点数据
const updateNodeData = (data) => {
  if (selectedNode.value) {
    selectedNode.value.data = { ...selectedNode.value.data, ...data }
  }
}

// 加载工作流
const loadWorkflow = async () => {
  if (!workflowUuid.value) {
    // 新建工作流，初始化默认节点
    nodes.value = [
      {
        id: 'start-1',
        type: 'default',
        label: '开始',
        position: { x: 100, y: 100 },
        data: { type: 'start', label: '开始' },
        style: {
          background: '#67c23a',
          color: '#fff',
          border: '1px solid #67c23a',
          borderRadius: '8px',
          padding: '10px',
          minWidth: '150px'
        }
      },
      {
        id: 'end-1',
        type: 'default',
        label: '结束',
        position: { x: 400, y: 100 },
        data: { type: 'end', label: '结束' },
        style: {
          background: '#f56c6c',
          color: '#fff',
          border: '1px solid #f56c6c',
          borderRadius: '8px',
          padding: '10px',
          minWidth: '150px'
        }
      }
    ]
    edges.value = []
    return
  }

  try {
    const response = await getWorkflow(workflowUuid.value)
    const workflow = response.data
    workflowName.value = workflow.name
    
    // 转换节点格式为Vue Flow格式
    nodes.value = (workflow.nodes || []).map(node => ({
      ...node,
      type: 'default',
      style: {
        background: getNodeColor(node.type),
        color: '#fff',
        border: `1px solid ${getNodeColor(node.type)}`,
        borderRadius: '8px',
        padding: '10px',
        minWidth: '150px'
      }
    }))
    
    edges.value = workflow.edges || []
  } catch (error) {
    ElMessage.error('加载工作流失败')
    console.error(error)
  }
}

// 获取节点颜色
const getNodeColor = (nodeType) => {
  const colors = {
    start: '#67c23a',
    end: '#f56c6c',
    llm: '#409eff',
    http: '#e6a23c',
    knowledge: '#909399',
    intent: '#9c27b0',
    string: '#00bcd4'
  }
  return colors[nodeType] || '#409eff'
}

// 保存工作流
const saveWorkflow = async () => {
  if (!workflowName.value) {
    ElMessage.warning('请输入工作流名称')
    return
  }

  saving.value = true
  try {
    // 转换Vue Flow格式为API格式
    const apiNodes = nodes.value.map(node => ({
      id: node.id,
      type: node.data.type || node.type,
      label: node.label || node.data.label,
      position: node.position,
      data: node.data
    }))
    
    const data = {
      name: workflowName.value,
      description: '',
      nodes: apiNodes,
      edges: edges.value,
      config: {}
    }

    if (workflowUuid.value) {
      await updateWorkflow(workflowUuid.value, data)
      ElMessage.success('保存成功')
    } else {
      const response = await createWorkflow(data)
      workflowUuid.value = response.data.uuid
      router.replace(`/workflows/editor/${workflowUuid.value}`)
      ElMessage.success('创建成功')
    }
  } catch (error) {
    ElMessage.error('保存失败: ' + (error.response?.data?.message || error.message))
  } finally {
    saving.value = false
  }
}

// 验证工作流
const validateWorkflow = async () => {
  if (!workflowUuid.value) {
    ElMessage.warning('请先保存工作流')
    return
  }

  try {
    const response = await validateWorkflowAPI(workflowUuid.value)
    const result = response.data

    if (result.is_valid) {
      ElMessage.success('工作流验证通过')
      if (result.warnings && result.warnings.length > 0) {
        ElMessage.warning(result.warnings.join('; '))
      }
    } else {
      ElMessage.error('工作流验证失败: ' + result.errors.join('; '))
    }
  } catch (error) {
    ElMessage.error('验证失败: ' + (error.response?.data?.message || error.message))
  }
}

// 返回
const goBack = () => {
  router.push('/workflows')
}

onMounted(async () => {
  await nextTick()
  await loadWorkflow()
})
</script>

<style scoped>
.workflow-editor-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #e4e7ed;
  background: #fff;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.header-left h2 {
  margin: 0;
  font-size: 20px;
}

.editor-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.node-library {
  width: 200px;
  border-right: 1px solid #e4e7ed;
  padding: 15px;
  background: #f5f7fa;
  overflow-y: auto;
}

.node-library h3 {
  margin: 0 0 15px 0;
  font-size: 16px;
}

.node-types {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.node-type-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  cursor: move;
  transition: all 0.3s;
}

.node-type-item:hover {
  border-color: #409eff;
  background: #ecf5ff;
}

.canvas-container {
  flex: 1;
  position: relative;
  background: #fafafa;
}

.workflow-canvas {
  width: 100%;
  height: 100%;
}

:deep(.vue-flow__node) {
  cursor: move;
}

:deep(.vue-flow__node.selected) {
  box-shadow: 0 0 0 2px #409eff;
}

.config-panel {
  width: 300px;
  border-left: 1px solid #e4e7ed;
  padding: 15px;
  background: #fff;
  overflow-y: auto;
}

.config-panel h3 {
  margin: 0 0 15px 0;
  font-size: 16px;
}
</style>

