<template>
  <div class="workflow-editor">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-button @click="goBack" icon="ArrowLeft">返回</el-button>
        <el-divider direction="vertical" />
        <el-input
          v-model="workflowName"
          placeholder="请输入工作流名称"
          style="width: 300px;"
          clearable
        />
      </div>
      <div class="toolbar-right">
        <el-button-group>
          <el-button @click="autoLayout" icon="MagicStick">自动排列</el-button>
          <el-button @click="fitView" icon="FullScreen">居中显示</el-button>
        </el-button-group>
        <el-button @click="saveWorkflow" type="primary" :loading="saving" icon="Check">
          保存工作流
        </el-button>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="editor-main">
      <!-- 左侧节点面板 -->
      <div class="nodes-panel">
        <div class="panel-header">
          <h3>节点工具箱</h3>
        </div>
        
        <div class="node-categories">
          <div class="category">
            <div class="category-title">基础节点</div>
            <div
              v-for="node in basicNodes"
              :key="node.type"
              class="node-item"
              @click="addNodeToCenter(node)"
            >
              <div class="node-icon" :style="{ backgroundColor: node.color }">
                <el-icon :size="20">
                  <component :is="node.icon" />
                </el-icon>
              </div>
              <div class="node-info">
                <div class="node-name">{{ node.label }}</div>
              </div>
            </div>
          </div>

          <div class="category">
            <div class="category-title">功能节点</div>
            <div
              v-for="node in functionNodes"
              :key="node.type"
              class="node-item"
              @click="addNodeToCenter(node)"
            >
              <div class="node-icon" :style="{ backgroundColor: node.color }">
                <el-icon :size="20">
                  <component :is="node.icon" />
                </el-icon>
              </div>
              <div class="node-info">
                <div class="node-name">{{ node.label }}</div>
              </div>
            </div>
          </div>
        </div>

        <el-divider />

        <div class="help-section">
          <el-alert
            title="💡 操作提示"
            type="info"
            :closable="false"
            description="1. 点击节点添加到画布
2. 从节点圆点拖动连线
3. 点击节点查看配置
4. 双击节点快速编辑"
          />
        </div>
      </div>

      <!-- 中间画布区域 -->
      <div class="canvas-area">
        <VueFlow
          v-model:nodes="nodes"
          v-model:edges="edges"
          :default-viewport="{ zoom: 1 }"
          :min-zoom="0.5"
          :max-zoom="2"
          @node-click="onNodeClick"
          @node-double-click="onNodeDoubleClick"
          @edge-click="onEdgeClick"
          @connect="onConnect"
          fit-view-on-init
          class="vue-flow-wrapper"
        >
          <Background pattern-color="#e5e7eb" :gap="20" />
          <Controls />

          <!-- 自定义节点模板 -->
          <template #node-custom="{ data, id }">
            <div class="workflow-node" :class="{ selected: selectedNodeId === id }">
              <!-- 输入连接点 -->
              <Handle
                v-if="data.nodeType !== 'start'"
                type="target"
                :position="Position.Left"
                class="node-handle handle-input"
              />

              <div class="node-content">
                <div class="node-header" :style="{ background: data.color }">
                  <el-icon :size="18">
                    <component :is="data.icon" />
                  </el-icon>
                  <span class="node-title">{{ data.label }}</span>
                  <el-button
                    type="danger"
                    icon="Close"
                    circle
                    size="small"
                    class="delete-btn"
                    @click.stop="deleteNode(id)"
                  />
                </div>
                <div class="node-body">
                  <el-tag v-if="data.configured" type="success" size="small">
                    ✓ 已配置
                  </el-tag>
                  <el-tag v-else type="info" size="small">
                    待配置
                  </el-tag>
                </div>
              </div>

              <!-- 输出连接点 -->
              <Handle
                v-if="data.nodeType !== 'end'"
                type="source"
                :position="Position.Right"
                class="node-handle handle-output"
              />
            </div>
          </template>
        </VueFlow>

        <!-- 空状态提示 -->
        <div v-if="nodes.length === 0" class="empty-state">
          <el-empty description="画布为空">
            <template #image>
              <el-icon :size="80" color="#909399">
                <Box />
              </el-icon>
            </template>
            <el-text type="info" size="large">
              👈 点击左侧节点开始创建工作流
            </el-text>
          </el-empty>
        </div>

        <!-- 连线提示浮层 -->
        <div v-if="showConnectTip" class="connect-tip">
          <el-icon color="#409eff" :size="24">
            <Position />
          </el-icon>
          <span>拖动圆点到目标节点建立连接</span>
        </div>
      </div>

      <!-- 右侧配置面板 -->
      <transition name="slide-left">
        <div class="config-panel" v-if="selectedNode">
          <div class="panel-header">
            <h3>节点配置</h3>
            <el-button icon="Close" circle size="small" @click="closeConfig" />
          </div>

          <el-divider />

          <el-form label-position="top">
            <el-form-item label="节点名称">
              <el-input v-model="selectedNode.data.label" placeholder="输入节点名称" />
            </el-form-item>

            <el-form-item label="节点类型">
              <el-tag :type="getNodeTypeColor(selectedNode.data.nodeType)">
                {{ selectedNode.data.nodeType }}
              </el-tag>
            </el-form-item>

            <el-divider>节点配置</el-divider>

            <!-- 动态配置组件 -->
            <component
              :is="getConfigComponent(selectedNode.data.nodeType)"
              v-if="selectedNode"
              :node="selectedNode"
              @update="updateNodeConfig"
            />

            <el-button
              type="primary"
              style="width: 100%; margin-top: 20px;"
              @click="saveNodeConfig"
            >
              保存配置
            </el-button>
          </el-form>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  Check,
  Close,
  VideoPlay,
  ChatDotRound,
  Link,
  Document,
  QuestionFilled,
  Setting,
  SuccessFilled,
  MagicStick,
  FullScreen,
  Box,
  Position as PositionIcon
} from '@element-plus/icons-vue'
import { VueFlow, useVueFlow, Handle, Position } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import {
  getWorkflow,
  createWorkflow,
  updateWorkflow
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
const { fitView: vueFlowFitView, project, viewport } = useVueFlow()

// 基础数据
const workflowName = ref('')
const workflowUuid = ref(route.params.uuid)
const saving = ref(false)
const selectedNodeId = ref(null)
const showConnectTip = ref(true)

// 节点和边
const nodes = ref([])
const edges = ref([])

// 节点计数器
let nodeIdCounter = 1

// 基础节点
const basicNodes = [
  {
    type: 'start',
    label: '开始',
    icon: 'VideoPlay',
    color: '#67c23a'
  },
  {
    type: 'end',
    label: '结束',
    icon: 'SuccessFilled',
    color: '#f56c6c'
  }
]

// 功能节点
const functionNodes = [
  {
    type: 'llm',
    label: 'LLM调用',
    icon: 'ChatDotRound',
    color: '#409eff'
  },
  {
    type: 'http',
    label: 'HTTP请求',
    icon: 'Link',
    color: '#e6a23c'
  },
  {
    type: 'knowledge',
    label: '知识库检索',
    icon: 'Document',
    color: '#909399'
  },
  {
    type: 'intent',
    label: '意图识别',
    icon: 'QuestionFilled',
    color: '#9c27b0'
  },
  {
    type: 'string',
    label: '字符串处理',
    icon: 'Setting',
    color: '#00bcd4'
  }
]

// 选中的节点
const selectedNode = computed(() => {
  return nodes.value.find(n => n.id === selectedNodeId.value)
})

// 添加节点到画布中心
const addNodeToCenter = (nodeType) => {
  // 检查开始和结束节点
  if (nodeType.type === 'start' || nodeType.type === 'end') {
    const exists = nodes.value.some(n => n.data.nodeType === nodeType.type)
    if (exists) {
      ElMessage.warning(`${nodeType.label}节点只能有一个`)
      return
    }
  }

  const newNode = {
    id: `${nodeType.type}-${nodeIdCounter++}`,
    type: 'custom',
    position: {
      x: 200 + nodes.value.length * 50,
      y: 100 + (nodes.value.length % 3) * 150
    },
    data: {
      nodeType: nodeType.type,
      label: nodeType.label,
      icon: nodeType.icon,
      color: nodeType.color,
      configured: false
    }
  }

  nodes.value.push(newNode)
  selectedNodeId.value = newNode.id
  
  // 隐藏提示
  if (nodes.value.length > 0) {
    showConnectTip.value = false
  }
  
  ElMessage.success(`已添加${nodeType.label}节点`)
}

// 删除节点
const deleteNode = (nodeId) => {
  ElMessageBox.confirm('确定删除这个节点吗？', '提示', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    nodes.value = nodes.value.filter(n => n.id !== nodeId)
    edges.value = edges.value.filter(e => e.source !== nodeId && e.target !== nodeId)
    
    if (selectedNodeId.value === nodeId) {
      selectedNodeId.value = null
    }
    
    ElMessage.success('节点已删除')
  }).catch(() => {})
}

// 节点点击
const onNodeClick = ({ node }) => {
  selectedNodeId.value = node.id
}

// 节点双击
const onNodeDoubleClick = ({ node }) => {
  selectedNodeId.value = node.id
  ElMessage.info('在右侧面板配置节点')
}

// 边点击
const onEdgeClick = ({ edge }) => {
  ElMessageBox.confirm('确定删除这条连线吗？', '提示', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    edges.value = edges.value.filter(e => e.id !== edge.id)
    ElMessage.success('连线已删除')
  }).catch(() => {})
}

// 创建连接
const onConnect = (connection) => {
  // 检查是否已存在相同连接
  const exists = edges.value.some(
    e => e.source === connection.source && e.target === connection.target
  )
  
  if (exists) {
    ElMessage.warning('连接已存在')
    return
  }

  const newEdge = {
    id: `edge-${connection.source}-${connection.target}`,
    source: connection.source,
    target: connection.target,
    type: 'smoothstep',
    animated: true,
    style: { stroke: '#409eff', strokeWidth: 2 }
  }

  edges.value.push(newEdge)
  ElMessage.success('连接创建成功')
}

// 自动布局
const autoLayout = () => {
  if (nodes.value.length === 0) {
    ElMessage.info('画布为空')
    return
  }

  // 简单的分层布局
  const startNodes = nodes.value.filter(n => n.data.nodeType === 'start')
  if (startNodes.length === 0) {
    ElMessage.warning('请先添加开始节点')
    return
  }

  // 使用BFS进行分层
  const layers = []
  const visited = new Set()
  const nodeMap = new Map(nodes.value.map(n => [n.id, n]))
  const edgeMap = new Map()

  edges.value.forEach(e => {
    if (!edgeMap.has(e.source)) {
      edgeMap.set(e.source, [])
    }
    edgeMap.get(e.source).push(e.target)
  })

  let queue = startNodes.map(n => n.id)
  let layer = 0

  while (queue.length > 0) {
    layers[layer] = []
    const nextQueue = []

    queue.forEach(nodeId => {
      if (!visited.has(nodeId)) {
        visited.add(nodeId)
        layers[layer].push(nodeId)

        const neighbors = edgeMap.get(nodeId) || []
        neighbors.forEach(neighbor => {
          if (!visited.has(neighbor)) {
            nextQueue.push(neighbor)
          }
        })
      }
    })

    queue = [...new Set(nextQueue)]
    layer++
  }

  // 应用布局
  const layerGap = 250
  const nodeGap = 120

  layers.forEach((layerNodes, layerIndex) => {
    layerNodes.forEach((nodeId, nodeIndex) => {
      const node = nodeMap.get(nodeId)
      if (node) {
        node.position = {
          x: layerIndex * layerGap + 100,
          y: nodeIndex * nodeGap + 100
        }
      }
    })
  })

  nextTick(() => {
    fitView()
  })

  ElMessage.success('自动排列完成')
}

// 居中显示
const fitView = () => {
  vueFlowFitView({ duration: 300, padding: 0.2 })
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

// 获取节点类型颜色
const getNodeTypeColor = (type) => {
  const colors = {
    start: 'success',
    end: 'danger',
    llm: 'primary',
    http: 'warning',
    knowledge: 'info',
    intent: '',
    string: ''
  }
  return colors[type] || 'info'
}

// 更新节点配置
const updateNodeConfig = (data) => {
  if (selectedNode.value) {
    selectedNode.value.data = { ...selectedNode.value.data, ...data }
  }
}

// 保存节点配置
const saveNodeConfig = () => {
  if (selectedNode.value) {
    selectedNode.value.data.configured = true
    ElMessage.success('配置已保存')
  }
}

// 关闭配置面板
const closeConfig = () => {
  selectedNodeId.value = null
}

// 加载工作流
const loadWorkflow = async () => {
  if (!workflowUuid.value) return

  try {
    const response = await getWorkflow(workflowUuid.value)
    const workflow = response.data

    workflowName.value = workflow.name

    // 转换节点
    nodes.value = (workflow.nodes || []).map(node => {
      const allNodes = [...basicNodes, ...functionNodes]
      const nodeType = allNodes.find(n => n.type === node.type)
      return {
        ...node,
        type: 'custom',
        data: {
          ...node.data,
          nodeType: node.type,
          icon: nodeType?.icon || 'Setting',
          color: nodeType?.color || '#409eff',
          configured: !!node.data && Object.keys(node.data).length > 0
        }
      }
    })

    edges.value = (workflow.edges || []).map(edge => ({
      ...edge,
      type: 'smoothstep',
      animated: true,
      style: { stroke: '#409eff', strokeWidth: 2 }
    }))

    // 更新计数器
    const maxId = Math.max(...nodes.value.map(n => {
      const match = n.id.match(/-(\d+)$/)
      return match ? parseInt(match[1]) : 0
    }), 0)
    nodeIdCounter = maxId + 1

    await nextTick()
    fitView()

    ElMessage.success('工作流加载成功')
  } catch (error) {
    ElMessage.error('加载工作流失败')
    console.error(error)
  }
}

// 保存工作流
const saveWorkflow = async () => {
  if (!workflowName.value) {
    ElMessage.warning('请输入工作流名称')
    return
  }

  if (nodes.value.length < 2) {
    ElMessage.warning('工作流至少需要2个节点')
    return
  }

  const hasStart = nodes.value.some(n => n.data.nodeType === 'start')
  const hasEnd = nodes.value.some(n => n.data.nodeType === 'end')

  if (!hasStart) {
    ElMessage.warning('工作流必须有开始节点')
    return
  }

  if (!hasEnd) {
    ElMessage.warning('工作流必须有结束节点')
    return
  }

  saving.value = true
  try {
    const apiNodes = nodes.value.map(node => ({
      id: node.id,
      type: node.data.nodeType,
      label: node.data.label,
      position: node.position,
      data: node.data
    }))

    const apiEdges = edges.value.map(edge => ({
      id: edge.id,
      source: edge.source,
      target: edge.target
    }))

    const data = {
      name: workflowName.value,
      description: '',
      nodes: apiNodes,
      edges: apiEdges,
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

// 返回
const goBack = () => {
  if (nodes.value.length > 0) {
    ElMessageBox.confirm('有未保存的更改，确定离开吗？', '提示', {
      confirmButtonText: '离开',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(() => {
      router.push('/workflows')
    }).catch(() => {})
  } else {
    router.push('/workflows')
  }
}

// 初始化
if (workflowUuid.value) {
  loadWorkflow()
}
</script>

<style scoped>
.workflow-editor {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

/* 工具栏 */
.toolbar {
  height: 60px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 主内容 */
.editor-main {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 左侧节点面板 */
.nodes-panel {
  width: 260px;
  background: #fff;
  border-right: 1px solid #e4e7ed;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.panel-header {
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.node-categories {
  flex: 1;
  padding: 16px;
}

.category {
  margin-bottom: 20px;
}

.category-title {
  font-size: 13px;
  color: #909399;
  margin-bottom: 12px;
  font-weight: 500;
}

.node-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  margin-bottom: 8px;
  background: #f8f9fa;
  border: 2px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.node-item:hover {
  border-color: #409eff;
  background: #ecf5ff;
  transform: translateX(2px);
}

.node-icon {
  width: 36px;
  height: 36px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.node-info {
  flex: 1;
}

.node-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.help-section {
  padding: 16px;
}

/* 画布区域 */
.canvas-area {
  flex: 1;
  position: relative;
  background: #fafafa;
}

.vue-flow-wrapper {
  width: 100%;
  height: 100%;
}

.empty-state {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 10;
  pointer-events: none;
}

.connect-tip {
  position: absolute;
  bottom: 30px;
  left: 50%;
  transform: translateX(-50%);
  background: #fff;
  padding: 12px 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  gap: 10px;
  z-index: 10;
}

/* 自定义节点 */
.workflow-node {
  min-width: 180px;
  background: #fff;
  border: 2px solid #e4e7ed;
  border-radius: 10px;
  overflow: hidden;
  transition: all 0.3s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.workflow-node:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.workflow-node.selected {
  border-color: #409eff;
  border-width: 3px;
  box-shadow: 0 4px 20px rgba(64, 158, 255, 0.3);
}

.node-content {
  position: relative;
}

.node-header {
  padding: 12px;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.node-title {
  flex: 1;
  font-size: 14px;
}

.delete-btn {
  opacity: 0;
  transition: opacity 0.3s;
}

.workflow-node:hover .delete-btn {
  opacity: 1;
}

.node-body {
  padding: 12px;
  text-align: center;
}

/* 连接点 */
.node-handle {
  width: 14px;
  height: 14px;
  border: 3px solid #fff;
  background: #409eff;
  transition: all 0.3s;
}

.node-handle:hover {
  transform: scale(1.4);
  box-shadow: 0 0 0 4px rgba(64, 158, 255, 0.3);
}

.handle-input {
  left: -7px;
}

.handle-output {
  right: -7px;
}

/* 配置面板 */
.config-panel {
  width: 350px;
  background: #fff;
  border-left: 1px solid #e4e7ed;
  overflow-y: auto;
  padding: 20px;
}

.config-panel .panel-header {
  padding: 0;
  border: none;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.config-panel .panel-header h3 {
  margin: 0;
}

/* 动画 */
.slide-left-enter-active,
.slide-left-leave-active {
  transition: all 0.3s ease;
}

.slide-left-enter-from {
  transform: translateX(100%);
  opacity: 0;
}

.slide-left-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

/* Vue Flow 样式 */
:deep(.vue-flow__edge-path) {
  stroke-width: 2;
}

:deep(.vue-flow__edge.selected .vue-flow__edge-path) {
  stroke: #f56c6c;
  stroke-width: 3;
}

:deep(.vue-flow__connection-path) {
  stroke: #409eff;
  stroke-width: 3;
  stroke-dasharray: 5, 5;
  animation: dash 0.5s linear infinite;
}

@keyframes dash {
  to {
    stroke-dashoffset: -10;
  }
}
</style>

