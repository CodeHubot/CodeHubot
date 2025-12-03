<template>
  <div class="workflow-editor-container">
    <!-- 顶部工具栏 -->
    <div class="editor-header">
      <div class="header-left">
        <el-button @click="goBack" icon="ArrowLeft">返回</el-button>
        <el-input
          v-model="workflowName"
          placeholder="请输入工作流名称"
          style="width: 300px;"
          clearable
        >
          <template #prefix>
            <el-icon><Edit /></el-icon>
          </template>
        </el-input>
        <el-input
          v-model="workflowDescription"
          placeholder="工作流描述（可选）"
          style="width: 400px;"
          clearable
        />
      </div>
      <div class="header-right">
        <el-tooltip content="撤销 (Ctrl+Z)" placement="bottom">
          <el-button @click="undo" :disabled="historyIndex <= 0" icon="RefreshLeft" circle />
        </el-tooltip>
        <el-tooltip content="重做 (Ctrl+Y)" placement="bottom">
          <el-button @click="redo" :disabled="historyIndex >= history.length - 1" icon="RefreshRight" circle />
        </el-tooltip>
        <el-divider direction="vertical" />
        <el-button @click="validateWorkflow" icon="CircleCheck">验证</el-button>
        <el-button type="primary" @click="saveWorkflow" :loading="saving" icon="Check">保存</el-button>
        <el-dropdown @command="handleMenuCommand">
          <el-button icon="More" circle />
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="clear">清空画布</el-dropdown-item>
              <el-dropdown-item command="template">使用模板</el-dropdown-item>
              <el-dropdown-item command="export">导出JSON</el-dropdown-item>
              <el-dropdown-item command="import">导入JSON</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <div class="editor-content">
      <!-- 左侧节点库 -->
      <div class="node-library">
        <div class="library-header">
          <h3>节点库</h3>
          <el-input
            v-model="nodeSearchQuery"
            placeholder="搜索节点"
            size="small"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        
        <div class="node-types">
          <div
            v-for="nodeType in filteredNodeTypes"
            :key="nodeType.type"
            class="node-type-item"
            draggable="true"
            @dragstart="handleDragStart($event, nodeType)"
            @click="addNodeToCanvas(nodeType)"
          >
            <div class="node-icon" :style="{ background: nodeType.color }">
              <el-icon><component :is="nodeType.icon" /></el-icon>
            </div>
            <div class="node-info">
              <div class="node-label">{{ nodeType.label }}</div>
              <div class="node-desc">{{ nodeType.description }}</div>
            </div>
          </div>
        </div>

        <!-- 操作说明 -->
        <div class="tips-section">
          <el-divider />
          <div class="tips-title">💡 使用说明</div>
          <ul class="tips-list">
            <li><strong>添加节点：</strong>点击或拖拽到画布</li>
            <li><strong>连接节点：</strong>从节点右侧圆点拖到目标节点</li>
            <li><strong>配置节点：</strong>点击节点查看右侧配置</li>
            <li><strong>删除节点：</strong>点击节点标题栏的删除按钮</li>
            <li><strong>移动节点：</strong>拖拽节点主体</li>
            <li><strong>缩放画布：</strong>滚轮或工具栏按钮</li>
          </ul>
          <el-divider />
          <div class="tips-title">⚠️ 规则</div>
          <ul class="tips-list">
            <li>只能有1个开始节点</li>
            <li>只能有1个结束节点</li>
            <li>节点必须连接成流程</li>
          </ul>
        </div>
      </div>

      <!-- 中间画布区域 -->
      <div class="canvas-container">
        <!-- 画布工具栏 -->
        <div class="canvas-toolbar">
          <el-button-group>
            <el-tooltip content="自动布局">
              <el-button size="small" @click="autoLayout" icon="Grid" />
            </el-tooltip>
            <el-tooltip content="居中显示">
              <el-button size="small" @click="fitView" icon="FullScreen" />
            </el-tooltip>
            <el-tooltip content="放大">
              <el-button size="small" @click="zoomIn" icon="ZoomIn" />
            </el-tooltip>
            <el-tooltip content="缩小">
              <el-button size="small" @click="zoomOut" icon="ZoomOut" />
            </el-tooltip>
          </el-button-group>
          <span class="zoom-level">{{ Math.round(viewport.zoom * 100) }}%</span>
        </div>

        <!-- 空状态提示 -->
        <div v-if="nodes.length === 0" class="empty-canvas">
          <el-empty description="画布为空">
            <template #image>
              <el-icon :size="100" color="#909399"><Operation /></el-icon>
            </template>
            <el-button type="primary" @click="showTemplateDialog = true">
              从模板开始
            </el-button>
            <el-button @click="addNodeToCanvas(nodeTypes[0])">
              添加开始节点
            </el-button>
          </el-empty>
        </div>

        <VueFlow
          v-model:nodes="nodes"
          v-model:edges="edges"
          :default-viewport="{ zoom: 1 }"
          :min-zoom="0.2"
          :max-zoom="4"
          @nodes-change="onNodesChange"
          @edges-change="onEdgesChange"
          @node-click="onNodeClick"
          @node-double-click="onNodeDoubleClick"
          @pane-click="onPaneClick"
          @drop="onDrop"
          @dragover="onDragOver"
          @connect="onConnect"
          @viewport-change="onViewportChange"
          fit-view-on-init
        >
          <Background pattern-color="#aaa" :gap="16" />
          <Controls />
          <MiniMap />
          
          <!-- 自定义节点 -->
          <template #node-default="{ data, id }">
            <div
              class="custom-node"
              :class="{ 'selected': selectedNode?.id === id }"
              :style="{ borderColor: getNodeColor(data.type) }"
            >
              <!-- 输入连接点 -->
              <Handle
                v-if="data.type !== 'start'"
                type="target"
                position="left"
                :style="{ 
                  left: '-8px',
                  background: getNodeColor(data.type),
                  width: '12px',
                  height: '12px',
                  border: '2px solid #fff'
                }"
              />
              
              <div class="node-header" :style="{ background: getNodeColor(data.type) }">
                <el-icon><component :is="getNodeIcon(data.type)" /></el-icon>
                <span class="node-title">{{ data.label }}</span>
                <el-button
                  size="small"
                  type="danger"
                  icon="Close"
                  circle
                  class="delete-btn"
                  @click.stop="deleteNode(id)"
                />
              </div>
              <div class="node-body">
                <div class="node-content" v-if="data.description">
                  {{ data.description }}
                </div>
                <div class="node-status" v-if="data.configured">
                  <el-tag size="small" type="success">已配置</el-tag>
                </div>
              </div>
              
              <!-- 输出连接点 -->
              <Handle
                v-if="data.type !== 'end'"
                type="source"
                position="right"
                :style="{ 
                  right: '-8px',
                  background: getNodeColor(data.type),
                  width: '12px',
                  height: '12px',
                  border: '2px solid #fff'
                }"
              />
            </div>
          </template>
        </VueFlow>
      </div>

      <!-- 右侧配置面板 -->
      <transition name="slide-left">
        <div class="config-panel" v-if="selectedNode">
          <div class="panel-header">
            <h3>节点配置</h3>
            <el-button size="small" @click="closeConfigPanel" icon="Close" circle />
          </div>
          
          <el-divider />
          
          <el-form :model="selectedNode" label-width="100px" label-position="top">
            <el-form-item label="节点ID">
              <el-input v-model="selectedNode.id" disabled />
            </el-form-item>
            <el-form-item label="节点标签">
              <el-input v-model="selectedNode.data.label" @change="saveToHistory" />
            </el-form-item>
            
            <el-divider />
            
            <!-- 根据节点类型显示不同的配置 -->
            <component
              :is="getConfigComponent(selectedNode.data.type)"
              v-if="selectedNode"
              :node="selectedNode"
              @update="updateNodeData"
            />
          </el-form>
        </div>
      </transition>
    </div>

    <!-- 模板选择对话框 -->
    <el-dialog
      v-model="showTemplateDialog"
      title="选择工作流模板"
      width="800px"
    >
      <el-row :gutter="16">
        <el-col :span="8" v-for="template in workflowTemplates" :key="template.id">
          <el-card
            class="template-card"
            :body-style="{ padding: '0px' }"
            shadow="hover"
            @click="useTemplate(template)"
          >
            <div class="template-image">
              <el-icon :size="60"><Operation /></el-icon>
            </div>
            <div style="padding: 14px;">
              <h4>{{ template.name }}</h4>
              <p class="template-desc">{{ template.description }}</p>
              <div class="template-meta">
                <el-tag size="small">{{ template.nodes.length }} 个节点</el-tag>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  Edit,
  Search,
  RefreshLeft,
  RefreshRight,
  Check,
  CircleCheck,
  More,
  Grid,
  FullScreen,
  ZoomIn,
  ZoomOut,
  Operation,
  Close,
  VideoPlay,
  Link,
  Document,
  ChatDotRound,
  QuestionFilled,
  Setting,
  SuccessFilled
} from '@element-plus/icons-vue'
import { VueFlow, useVueFlow, Handle } from '@vue-flow/core'
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
const { fitView: vueFlowFitView, zoomIn: vueFlowZoomIn, zoomOut: vueFlowZoomOut, project, viewport } = useVueFlow()

// 工作流基本信息
const workflowName = ref('')
const workflowDescription = ref('')
const workflowUuid = ref(route.params.uuid)
const nodes = ref([])
const edges = ref([])
const saving = ref(false)

// 选中的节点
const selectedNode = ref(null)

// 节点搜索
const nodeSearchQuery = ref('')

// 模板对话框
const showTemplateDialog = ref(false)

// 历史记录（撤销/重做）
const history = ref([])
const historyIndex = ref(-1)

// 节点ID计数器
let nodeIdCounter = 1

// 节点类型定义（优化版）
const nodeTypes = [
  {
    type: 'start',
    label: '开始',
    description: '工作流入口',
    icon: 'VideoPlay',
    color: '#67c23a'
  },
  {
    type: 'llm',
    label: 'LLM调用',
    description: '调用大语言模型',
    icon: 'ChatDotRound',
    color: '#409eff'
  },
  {
    type: 'http',
    label: 'HTTP请求',
    description: '调用外部API',
    icon: 'Link',
    color: '#e6a23c'
  },
  {
    type: 'knowledge',
    label: '知识库检索',
    description: '搜索知识库',
    icon: 'Document',
    color: '#909399'
  },
  {
    type: 'intent',
    label: '意图识别',
    description: '识别用户意图',
    icon: 'QuestionFilled',
    color: '#9c27b0'
  },
  {
    type: 'string',
    label: '字符串处理',
    description: '文本操作',
    icon: 'Setting',
    color: '#00bcd4'
  },
  {
    type: 'end',
    label: '结束',
    description: '工作流出口',
    icon: 'SuccessFilled',
    color: '#f56c6c'
  }
]

// 工作流模板
const workflowTemplates = ref([
  {
    id: 'simple',
    name: '简单对话',
    description: '基础的LLM对话工作流',
    nodes: [
      { id: 'start-1', type: 'start', label: '开始', position: { x: 100, y: 200 }, data: { type: 'start', label: '开始' } },
      { id: 'llm-1', type: 'llm', label: 'LLM对话', position: { x: 300, y: 200 }, data: { type: 'llm', label: 'LLM对话' } },
      { id: 'end-1', type: 'end', label: '结束', position: { x: 500, y: 200 }, data: { type: 'end', label: '结束' } }
    ],
    edges: [
      { id: 'e1-2', source: 'start-1', target: 'llm-1' },
      { id: 'e2-3', source: 'llm-1', target: 'end-1' }
    ]
  },
  {
    id: 'knowledge',
    name: '知识库问答',
    description: '结合知识库的智能问答',
    nodes: [
      { id: 'start-1', type: 'start', label: '开始', position: { x: 100, y: 200 }, data: { type: 'start', label: '开始' } },
      { id: 'knowledge-1', type: 'knowledge', label: '检索知识库', position: { x: 300, y: 200 }, data: { type: 'knowledge', label: '检索知识库' } },
      { id: 'llm-1', type: 'llm', label: 'LLM生成回答', position: { x: 500, y: 200 }, data: { type: 'llm', label: 'LLM生成回答' } },
      { id: 'end-1', type: 'end', label: '结束', position: { x: 700, y: 200 }, data: { type: 'end', label: '结束' } }
    ],
    edges: [
      { id: 'e1-2', source: 'start-1', target: 'knowledge-1' },
      { id: 'e2-3', source: 'knowledge-1', target: 'llm-1' },
      { id: 'e3-4', source: 'llm-1', target: 'end-1' }
    ]
  },
  {
    id: 'intent',
    name: '意图识别路由',
    description: '根据意图路由到不同处理',
    nodes: [
      { id: 'start-1', type: 'start', label: '开始', position: { x: 100, y: 250 }, data: { type: 'start', label: '开始' } },
      { id: 'intent-1', type: 'intent', label: '识别意图', position: { x: 300, y: 250 }, data: { type: 'intent', label: '识别意图' } },
      { id: 'llm-1', type: 'llm', label: 'LLM处理', position: { x: 500, y: 150 }, data: { type: 'llm', label: 'LLM处理' } },
      { id: 'http-1', type: 'http', label: 'API调用', position: { x: 500, y: 350 }, data: { type: 'http', label: 'API调用' } },
      { id: 'end-1', type: 'end', label: '结束', position: { x: 700, y: 250 }, data: { type: 'end', label: '结束' } }
    ],
    edges: [
      { id: 'e1-2', source: 'start-1', target: 'intent-1' },
      { id: 'e2-3', source: 'intent-1', target: 'llm-1', label: '对话类' },
      { id: 'e2-4', source: 'intent-1', target: 'http-1', label: '查询类' },
      { id: 'e3-5', source: 'llm-1', target: 'end-1' },
      { id: 'e4-5', source: 'http-1', target: 'end-1' }
    ]
  }
])

// 过滤后的节点类型
const filteredNodeTypes = computed(() => {
  if (!nodeSearchQuery.value) return nodeTypes
  const query = nodeSearchQuery.value.toLowerCase()
  return nodeTypes.filter(type =>
    type.label.toLowerCase().includes(query) ||
    type.description.toLowerCase().includes(query)
  )
})

// 拖拽处理
const handleDragStart = (event, nodeType) => {
  event.dataTransfer.setData('nodeType', JSON.stringify(nodeType))
  event.dataTransfer.effectAllowed = 'copy'
}

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
    
    // 检查是否已存在开始或结束节点
    if (nodeType.type === 'start') {
      const hasStart = nodes.value.some(n => n.data.type === 'start')
      if (hasStart) {
        ElMessage.warning('工作流只能有一个开始节点')
        return
      }
    }
    
    if (nodeType.type === 'end') {
      const hasEnd = nodes.value.some(n => n.data.type === 'end')
      if (hasEnd) {
        ElMessage.warning('工作流只能有一个结束节点')
        return
      }
    }
    
    const rect = event.currentTarget.getBoundingClientRect()
    const position = project({
      x: event.clientX - rect.left,
      y: event.clientY - rect.top
    })

    addNode(nodeType, position)
  } catch (error) {
    console.error('添加节点失败:', error)
  }
}

// 添加节点到画布（点击或拖拽）
const addNodeToCanvas = (nodeType) => {
  // 检查是否已存在开始或结束节点
  if (nodeType.type === 'start') {
    const hasStart = nodes.value.some(n => n.data.type === 'start')
    if (hasStart) {
      ElMessage.warning('工作流只能有一个开始节点')
      return
    }
  }
  
  if (nodeType.type === 'end') {
    const hasEnd = nodes.value.some(n => n.data.type === 'end')
    if (hasEnd) {
      ElMessage.warning('工作流只能有一个结束节点')
      return
    }
  }
  
  const position = {
    x: 100 + nodes.value.length * 50,
    y: 100 + (nodes.value.length % 5) * 100
  }
  addNode(nodeType, position)
}

// 添加节点
const addNode = (nodeType, position) => {
  const newNode = {
    id: `${nodeType.type}-${nodeIdCounter++}`,
    type: 'default',
    label: nodeType.label,
    position,
    data: {
      type: nodeType.type,
      label: nodeType.label,
      description: nodeType.description,
      configured: false
    }
  }

  nodes.value.push(newNode)
  saveToHistory()
  
  // 自动选中新添加的节点
  selectedNode.value = newNode
  
  ElMessage.success(`已添加${nodeType.label}节点`)
}

// 删除节点
const deleteNode = (nodeId) => {
  nodes.value = nodes.value.filter(n => n.id !== nodeId)
  edges.value = edges.value.filter(e => e.source !== nodeId && e.target !== nodeId)
  if (selectedNode.value?.id === nodeId) {
    selectedNode.value = null
  }
  saveToHistory()
}

// 节点变化处理
const onNodesChange = (changes) => {
  changes.forEach(change => {
    if (change.type === 'position' && change.dragging === false) {
      const node = nodes.value.find(n => n.id === change.id)
      if (node && change.position) {
        node.position = change.position
        saveToHistory()
      }
    } else if (change.type === 'remove') {
      deleteNode(change.id)
    }
  })
}

// 边变化处理
const onEdgesChange = (changes) => {
  changes.forEach(change => {
    if (change.type === 'remove') {
      edges.value = edges.value.filter(e => e.id !== change.id)
      saveToHistory()
    }
  })
}

// 连接处理
const onConnect = (connection) => {
  const newEdge = {
    id: `edge-${connection.source}-${connection.target}`,
    source: connection.source,
    target: connection.target,
    sourceHandle: connection.sourceHandle,
    targetHandle: connection.targetHandle,
    type: 'default',
    animated: true
  }
  edges.value.push(newEdge)
  saveToHistory()
  ElMessage.success('连接成功')
}

// 节点点击
const onNodeClick = ({ node }) => {
  selectedNode.value = node
}

// 节点双击
const onNodeDoubleClick = ({ node }) => {
  selectedNode.value = node
  ElMessage.info('请在右侧配置节点')
}

// 画布点击
const onPaneClick = () => {
  // 不自动关闭配置面板，用户体验更好
  // selectedNode.value = null
}

// 关闭配置面板
const closeConfigPanel = () => {
  selectedNode.value = null
}

// 视口变化（viewport 由 useVueFlow 提供，会自动更新）
const onViewportChange = (newViewport) => {
  // viewport 由 Vue Flow 自动管理，无需手动更新
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
    selectedNode.value.data = { ...selectedNode.value.data, ...data, configured: true }
    saveToHistory()
  }
}

// 获取节点颜色
const getNodeColor = (nodeType) => {
  const type = nodeTypes.find(t => t.type === nodeType)
  return type?.color || '#409eff'
}

// 获取节点图标
const getNodeIcon = (nodeType) => {
  const type = nodeTypes.find(t => t.type === nodeType)
  return type?.icon || 'Operation'
}

// 保存到历史记录
const saveToHistory = () => {
  // 删除当前位置之后的历史
  history.value = history.value.slice(0, historyIndex.value + 1)
  
  // 添加新的历史记录
  history.value.push({
    nodes: JSON.parse(JSON.stringify(nodes.value)),
    edges: JSON.parse(JSON.stringify(edges.value))
  })
  
  historyIndex.value = history.value.length - 1
  
  // 限制历史记录数量
  if (history.value.length > 50) {
    history.value.shift()
    historyIndex.value--
  }
}

// 撤销
const undo = () => {
  if (historyIndex.value > 0) {
    historyIndex.value--
    const state = history.value[historyIndex.value]
    nodes.value = JSON.parse(JSON.stringify(state.nodes))
    edges.value = JSON.parse(JSON.stringify(state.edges))
  }
}

// 重做
const redo = () => {
  if (historyIndex.value < history.value.length - 1) {
    historyIndex.value++
    const state = history.value[historyIndex.value]
    nodes.value = JSON.parse(JSON.stringify(state.nodes))
    edges.value = JSON.parse(JSON.stringify(state.edges))
  }
}

// 画布操作
const fitView = () => {
  vueFlowFitView({ duration: 300 })
}

const zoomIn = () => {
  vueFlowZoomIn({ duration: 300 })
}

const zoomOut = () => {
  vueFlowZoomOut({ duration: 300 })
}

// 自动布局
const autoLayout = () => {
  // 简单的层次布局
  const startNodes = nodes.value.filter(n => n.data.type === 'start')
  if (startNodes.length === 0) return

  const layers = []
  const visited = new Set()
  const nodeMap = new Map(nodes.value.map(n => [n.id, n]))
  const edgeMap = new Map()
  
  // 构建边映射
  edges.value.forEach(e => {
    if (!edgeMap.has(e.source)) {
      edgeMap.set(e.source, [])
    }
    edgeMap.get(e.source).push(e.target)
  })

  // BFS分层
  let queue = startNodes.map(n => n.id)
  let currentLayer = 0
  
  while (queue.length > 0) {
    const nextQueue = []
    layers[currentLayer] = []
    
    queue.forEach(nodeId => {
      if (!visited.has(nodeId)) {
        visited.add(nodeId)
        layers[currentLayer].push(nodeId)
        
        const neighbors = edgeMap.get(nodeId) || []
        neighbors.forEach(neighbor => {
          if (!visited.has(neighbor)) {
            nextQueue.push(neighbor)
          }
        })
      }
    })
    
    queue = [...new Set(nextQueue)]
    currentLayer++
  }

  // 应用布局
  const layerWidth = 250
  const nodeHeight = 100
  
  layers.forEach((layer, layerIndex) => {
    layer.forEach((nodeId, nodeIndex) => {
      const node = nodeMap.get(nodeId)
      if (node) {
        node.position = {
          x: layerIndex * layerWidth + 100,
          y: nodeIndex * nodeHeight + 100
        }
      }
    })
  })

  saveToHistory()
  fitView()
  ElMessage.success('自动布局完成')
}

// 使用模板
const useTemplate = (template) => {
  ElMessageBox.confirm('使用模板将清空当前画布，是否继续？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    nodes.value = template.nodes.map(node => ({
      ...node,
      type: 'default',
      data: { ...node.data, configured: false }
    }))
    edges.value = template.edges
    nodeIdCounter = nodes.value.length + 1
    saveToHistory()
    showTemplateDialog.value = false
    fitView()
    ElMessage.success(`已应用"${template.name}"模板`)
  }).catch(() => {})
}

// 菜单命令处理
const handleMenuCommand = (command) => {
  switch (command) {
    case 'clear':
      ElMessageBox.confirm('确定要清空画布吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        nodes.value = []
        edges.value = []
        selectedNode.value = null
        saveToHistory()
        ElMessage.success('画布已清空')
      }).catch(() => {})
      break
    case 'template':
      showTemplateDialog.value = true
      break
    case 'export':
      exportWorkflow()
      break
    case 'import':
      importWorkflow()
      break
  }
}

// 导出工作流
const exportWorkflow = () => {
  const data = {
    name: workflowName.value,
    description: workflowDescription.value,
    nodes: nodes.value,
    edges: edges.value
  }
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `workflow_${Date.now()}.json`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('导出成功')
}

// 导入工作流
const importWorkflow = () => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'application/json'
  input.onchange = (e) => {
    const file = e.target.files[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (event) => {
      try {
        const data = JSON.parse(event.target.result)
        workflowName.value = data.name || ''
        workflowDescription.value = data.description || ''
        nodes.value = data.nodes || []
        edges.value = data.edges || []
        saveToHistory()
        fitView()
        ElMessage.success('导入成功')
      } catch (error) {
        ElMessage.error('导入失败：JSON格式错误')
      }
    }
    reader.readAsText(file)
  }
  input.click()
}

// 加载工作流
const loadWorkflow = async () => {
  if (!workflowUuid.value) {
    // 新建工作流，保存初始状态
    saveToHistory()
    return
  }

  try {
    const response = await getWorkflow(workflowUuid.value)
    const workflow = response.data
    workflowName.value = workflow.name
    workflowDescription.value = workflow.description || ''

    nodes.value = (workflow.nodes || []).map(node => ({
      ...node,
      type: 'default'
    }))

    edges.value = workflow.edges || []
    
    // 更新节点计数器
    const maxId = Math.max(...nodes.value.map(n => {
      const match = n.id.match(/-(\d+)$/)
      return match ? parseInt(match[1]) : 0
    }), 0)
    nodeIdCounter = maxId + 1

    saveToHistory()
    await nextTick()
    fitView()
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
    ElMessage.warning('工作流至少需要开始和结束节点')
    return
  }

  saving.value = true
  try {
    const apiNodes = nodes.value.map(node => ({
      id: node.id,
      type: node.data.type || node.type,
      label: node.label || node.data.label,
      position: node.position,
      data: node.data
    }))

    const data = {
      name: workflowName.value,
      description: workflowDescription.value,
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
      ElMessage.success('工作流验证通过 ✓')
      if (result.warnings && result.warnings.length > 0) {
        result.warnings.forEach(warning => {
          ElMessage.warning(warning)
        })
      }
    } else {
      ElMessage.error('工作流验证失败')
      result.errors.forEach(error => {
        ElMessage.error(error)
      })
    }
  } catch (error) {
    ElMessage.error('验证失败: ' + (error.response?.data?.message || error.message))
  }
}

// 返回
const goBack = () => {
  if (history.value.length > 1) {
    ElMessageBox.confirm('有未保存的更改，确定要离开吗？', '提示', {
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

// 键盘快捷键
const handleKeyDown = (event) => {
  // Ctrl/Cmd + Z: 撤销
  if ((event.ctrlKey || event.metaKey) && event.key === 'z' && !event.shiftKey) {
    event.preventDefault()
    undo()
  }
  // Ctrl/Cmd + Y 或 Ctrl/Cmd + Shift + Z: 重做
  else if ((event.ctrlKey || event.metaKey) && (event.key === 'y' || (event.key === 'z' && event.shiftKey))) {
    event.preventDefault()
    redo()
  }
  // Ctrl/Cmd + S: 保存
  else if ((event.ctrlKey || event.metaKey) && event.key === 's') {
    event.preventDefault()
    saveWorkflow()
  }
  // Delete: 删除选中节点
  else if (event.key === 'Delete' && selectedNode.value) {
    event.preventDefault()
    deleteNode(selectedNode.value.id)
  }
}

onMounted(async () => {
  await nextTick()
  await loadWorkflow()
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})
</script>

<style scoped>
.workflow-editor-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  border-bottom: 1px solid #e4e7ed;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.editor-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 左侧节点库 */
.node-library {
  width: 280px;
  border-right: 1px solid #e4e7ed;
  background: #fff;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.library-header {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.library-header h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
}

.node-types {
  flex: 1;
  padding: 12px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.node-type-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f8f9fa;
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.node-type-item:hover {
  border-color: #409eff;
  background: #ecf5ff;
  transform: translateX(4px);
}

.node-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 20px;
}

.node-info {
  flex: 1;
}

.node-label {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 2px;
}

.node-desc {
  font-size: 12px;
  color: #909399;
}

.tips-section {
  padding: 16px;
  border-top: 1px solid #f0f0f0;
  background: #fafafa;
}

.tips-title {
  font-size: 13px;
  font-weight: 500;
  color: #606266;
  margin-bottom: 8px;
}

.tips-list {
  margin: 0;
  padding-left: 18px;
  font-size: 12px;
  color: #909399;
  line-height: 1.8;
}

/* 画布区域 */
.canvas-container {
  flex: 1;
  position: relative;
  background: #fafafa;
}

.canvas-toolbar {
  position: absolute;
  top: 16px;
  left: 16px;
  z-index: 10;
  background: #fff;
  border-radius: 8px;
  padding: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 12px;
}

.zoom-level {
  font-size: 13px;
  color: #606266;
  font-weight: 500;
  min-width: 50px;
  text-align: center;
}

.empty-canvas {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 5;
  text-align: center;
}

/* 自定义节点样式 */
.custom-node {
  min-width: 180px;
  background: #fff;
  border: 2px solid #dcdfe6;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.custom-node:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.custom-node.selected {
  border-width: 3px;
  box-shadow: 0 4px 20px rgba(64, 158, 255, 0.3);
}

.node-header {
  padding: 10px 12px;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  position: relative;
}

.node-title {
  flex: 1;
  font-size: 14px;
}

.delete-btn {
  opacity: 0;
  transition: opacity 0.3s;
}

.custom-node:hover .delete-btn {
  opacity: 1;
}

.node-body {
  padding: 12px;
  min-height: 50px;
}

.node-content {
  font-size: 12px;
  color: #606266;
  margin-bottom: 8px;
}

.node-status {
  margin-top: 8px;
}

/* 配置面板 */
.config-panel {
  width: 350px;
  border-left: 1px solid #e4e7ed;
  background: #fff;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.config-panel :deep(.el-form) {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
}

/* 模板卡片 */
.template-card {
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 16px;
}

.template-card:hover {
  transform: translateY(-4px);
}

.template-image {
  height: 120px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.template-desc {
  font-size: 13px;
  color: #909399;
  margin: 8px 0;
}

.template-meta {
  margin-top: 8px;
}

/* 过渡动画 */
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

/* Vue Flow 自定义样式 */
:deep(.vue-flow__node) {
  cursor: pointer;
}

:deep(.vue-flow__edge-path) {
  stroke-width: 2;
  stroke: #b1b1b7;
}

:deep(.vue-flow__edge.selected .vue-flow__edge-path) {
  stroke: #409eff;
  stroke-width: 3;
}

:deep(.vue-flow__edge-text) {
  font-size: 12px;
}

:deep(.vue-flow__minimap) {
  background: #f5f7fa;
}

:deep(.vue-flow__controls) {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

/* 连接点样式 */
:deep(.vue-flow__handle) {
  cursor: crosshair;
  transition: all 0.3s;
}

:deep(.vue-flow__handle:hover) {
  transform: scale(1.3);
  box-shadow: 0 0 0 4px rgba(64, 158, 255, 0.3);
}

:deep(.vue-flow__handle-connecting) {
  background: #409eff !important;
  transform: scale(1.5);
  box-shadow: 0 0 0 6px rgba(64, 158, 255, 0.4);
}

/* 连接线样式优化 */
:deep(.vue-flow__edge) {
  cursor: pointer;
}

:deep(.vue-flow__edge:hover .vue-flow__edge-path) {
  stroke: #409eff;
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
