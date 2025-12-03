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
          <h3>添加节点</h3>
          <el-text type="info" size="small">点击节点添加到流程</el-text>
        </div>
        
        <div class="node-list">
          <div
            v-for="node in availableNodes"
            :key="node.type"
            class="node-item"
            @click="addNode(node)"
            :class="{ disabled: !canAddNode(node) }"
          >
            <div class="node-icon" :style="{ backgroundColor: node.color }">
              <el-icon :size="24">
                <component :is="node.icon" />
              </el-icon>
            </div>
            <div class="node-info">
              <div class="node-name">{{ node.label }}</div>
              <div class="node-desc">{{ node.description }}</div>
            </div>
          </div>
        </div>

        <el-divider />

        <div class="usage-tips">
          <h4>📖 使用说明</h4>
          <ol>
            <li>点击左侧节点添加到流程</li>
            <li>节点会自动按顺序连接</li>
            <li>点击节点进行配置</li>
            <li>必须有开始和结束节点</li>
            <li>点击保存按钮保存工作流</li>
          </ol>
        </div>
      </div>

      <!-- 中间流程区域 -->
      <div class="flow-panel">
        <div class="flow-header">
          <h3>工作流程</h3>
          <el-button
            @click="clearFlow"
            type="danger"
            text
            size="small"
            v-if="flowNodes.length > 0"
          >
            清空流程
          </el-button>
        </div>

        <!-- 空状态 -->
        <el-empty
          v-if="flowNodes.length === 0"
          description="还没有添加节点"
          class="flow-empty"
        >
          <el-text type="info">
            👈 点击左侧节点开始创建工作流
          </el-text>
        </el-empty>

        <!-- 流程节点列表 -->
        <div v-else class="flow-nodes">
          <div
            v-for="(node, index) in flowNodes"
            :key="node.id"
            class="flow-node-wrapper"
          >
            <!-- 节点 -->
            <div
              class="flow-node"
              :class="{ active: selectedNodeId === node.id, configured: node.configured }"
              @click="selectNode(node)"
            >
              <div class="node-header" :style="{ backgroundColor: node.color }">
                <el-icon :size="20">
                  <component :is="node.icon" />
                </el-icon>
                <span class="node-title">{{ node.label }}</span>
                <el-button
                  type="danger"
                  icon="Close"
                  circle
                  size="small"
                  @click.stop="removeNode(index)"
                />
              </div>
              <div class="node-body">
                <el-tag v-if="node.configured" type="success" size="small">已配置</el-tag>
                <el-tag v-else type="warning" size="small">待配置</el-tag>
                <el-text size="small" type="info" style="margin-top: 8px;">
                  {{ node.description }}
                </el-text>
              </div>
            </div>

            <!-- 连接箭头 -->
            <div v-if="index < flowNodes.length - 1" class="flow-arrow">
              <el-icon :size="24" color="#409eff">
                <ArrowDown />
              </el-icon>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧配置面板 -->
      <div class="config-panel" v-if="selectedNode">
        <div class="panel-header">
          <h3>节点配置</h3>
          <el-button icon="Close" circle size="small" @click="selectedNodeId = null" />
        </div>

        <el-divider />

        <el-form label-position="top">
          <el-form-item label="节点名称">
            <el-input v-model="selectedNode.label" />
          </el-form-item>

          <el-form-item label="节点ID">
            <el-input v-model="selectedNode.id" disabled />
          </el-form-item>

          <el-divider>详细配置</el-divider>

          <!-- 动态加载配置组件 -->
          <component
            :is="getConfigComponent(selectedNode.type)"
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
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  ArrowDown,
  Check,
  Close,
  VideoPlay,
  ChatDotRound,
  Link,
  Document,
  QuestionFilled,
  Setting,
  SuccessFilled
} from '@element-plus/icons-vue'
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

// 基础数据
const workflowName = ref('')
const workflowUuid = ref(route.params.uuid)
const saving = ref(false)

// 流程节点
const flowNodes = ref([])
const selectedNodeId = ref(null)

// 节点ID计数器
let nodeIdCounter = 1

// 可用节点类型
const availableNodes = [
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
    description: '搜索知识库内容',
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
    description: '处理文本数据',
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

// 选中的节点
const selectedNode = computed(() => {
  return flowNodes.value.find(n => n.id === selectedNodeId.value)
})

// 判断是否可以添加节点
const canAddNode = (nodeType) => {
  // 开始节点只能有一个且必须在第一位
  if (nodeType.type === 'start') {
    return flowNodes.value.length === 0
  }
  
  // 结束节点只能有一个且必须在最后
  if (nodeType.type === 'end') {
    const hasEnd = flowNodes.value.some(n => n.type === 'end')
    return !hasEnd && flowNodes.value.length > 0
  }
  
  // 其他节点必须在有开始节点后才能添加
  const hasStart = flowNodes.value.some(n => n.type === 'start')
  return hasStart
}

// 添加节点
const addNode = (nodeType) => {
  if (!canAddNode(nodeType)) {
    if (nodeType.type === 'start') {
      ElMessage.warning('开始节点必须是第一个节点')
    } else if (nodeType.type === 'end') {
      if (flowNodes.value.length === 0) {
        ElMessage.warning('请先添加开始节点')
      } else {
        ElMessage.warning('已有结束节点')
      }
    } else {
      ElMessage.warning('请先添加开始节点')
    }
    return
  }

  // 如果要添加结束节点，检查是否已经有结束节点
  if (nodeType.type === 'end') {
    const lastNode = flowNodes.value[flowNodes.value.length - 1]
    if (lastNode && lastNode.type === 'end') {
      ElMessage.warning('已有结束节点')
      return
    }
  }

  const newNode = {
    id: `${nodeType.type}-${nodeIdCounter++}`,
    type: nodeType.type,
    label: nodeType.label,
    description: nodeType.description,
    icon: nodeType.icon,
    color: nodeType.color,
    configured: false,
    data: {}
  }

  flowNodes.value.push(newNode)
  selectedNodeId.value = newNode.id
  ElMessage.success(`已添加 ${nodeType.label}`)
}

// 移除节点
const removeNode = (index) => {
  ElMessageBox.confirm('确定要删除这个节点吗？', '提示', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    const node = flowNodes.value[index]
    flowNodes.value.splice(index, 1)
    
    if (selectedNodeId.value === node.id) {
      selectedNodeId.value = null
    }
    
    ElMessage.success('节点已删除')
  }).catch(() => {})
}

// 选中节点
const selectNode = (node) => {
  selectedNodeId.value = node.id
}

// 清空流程
const clearFlow = () => {
  ElMessageBox.confirm('确定要清空整个流程吗？', '提示', {
    confirmButtonText: '清空',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    flowNodes.value = []
    selectedNodeId.value = null
    ElMessage.success('流程已清空')
  }).catch(() => {})
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

// 更新节点配置
const updateNodeConfig = (data) => {
  if (selectedNode.value) {
    selectedNode.value.data = { ...selectedNode.value.data, ...data }
  }
}

// 保存节点配置
const saveNodeConfig = () => {
  if (selectedNode.value) {
    selectedNode.value.configured = true
    ElMessage.success('配置已保存')
  }
}

// 加载工作流
const loadWorkflow = async () => {
  if (!workflowUuid.value) return

  try {
    const response = await getWorkflow(workflowUuid.value)
    const workflow = response.data
    
    workflowName.value = workflow.name
    
    // 转换节点格式
    flowNodes.value = (workflow.nodes || []).map(node => {
      const nodeType = availableNodes.find(n => n.type === node.type)
      return {
        ...node,
        icon: nodeType?.icon || 'Setting',
        color: nodeType?.color || '#409eff',
        configured: !!node.data && Object.keys(node.data).length > 0
      }
    })
    
    // 更新节点计数器
    const maxId = Math.max(...flowNodes.value.map(n => {
      const match = n.id.match(/-(\d+)$/)
      return match ? parseInt(match[1]) : 0
    }), 0)
    nodeIdCounter = maxId + 1
    
    ElMessage.success('工作流加载成功')
  } catch (error) {
    ElMessage.error('加载工作流失败')
    console.error(error)
  }
}

// 保存工作流
const saveWorkflow = async () => {
  // 验证
  if (!workflowName.value) {
    ElMessage.warning('请输入工作流名称')
    return
  }

  if (flowNodes.value.length < 2) {
    ElMessage.warning('工作流至少需要开始和结束节点')
    return
  }

  const hasStart = flowNodes.value.some(n => n.type === 'start')
  const hasEnd = flowNodes.value.some(n => n.type === 'end')
  
  if (!hasStart) {
    ElMessage.warning('工作流必须有开始节点')
    return
  }
  
  if (!hasEnd) {
    ElMessage.warning('工作流必须有结束节点')
    return
  }

  // 转换为API格式
  saving.value = true
  try {
    const nodes = flowNodes.value.map((node, index) => ({
      id: node.id,
      type: node.type,
      label: node.label,
      position: { x: 250, y: 100 + index * 150 }, // 自动计算位置
      data: node.data
    }))

    // 自动生成连接
    const edges = []
    for (let i = 0; i < nodes.length - 1; i++) {
      edges.push({
        id: `edge-${i}`,
        source: nodes[i].id,
        target: nodes[i + 1].id
      })
    }

    const data = {
      name: workflowName.value,
      description: '',
      nodes,
      edges,
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
  if (flowNodes.value.length > 0) {
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

/* 主内容区 */
.editor-main {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 左侧节点面板 */
.nodes-panel {
  width: 280px;
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
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
}

.node-list {
  flex: 1;
  padding: 16px;
}

.node-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  margin-bottom: 12px;
  background: #f8f9fa;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.node-item:hover:not(.disabled) {
  border-color: #409eff;
  background: #ecf5ff;
  transform: translateX(4px);
}

.node-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.node-icon {
  width: 44px;
  height: 44px;
  border-radius: 8px;
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
  margin-bottom: 4px;
}

.node-desc {
  font-size: 12px;
  color: #909399;
}

.usage-tips {
  padding: 16px;
  background: #fafafa;
  border-top: 1px solid #f0f0f0;
}

.usage-tips h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #606266;
}

.usage-tips ol {
  margin: 0;
  padding-left: 20px;
  font-size: 13px;
  color: #909399;
  line-height: 1.8;
}

/* 中间流程区域 */
.flow-panel {
  flex: 1;
  background: #fafafa;
  overflow-y: auto;
  padding: 20px;
}

.flow-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.flow-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.flow-empty {
  margin-top: 100px;
}

.flow-nodes {
  max-width: 600px;
  margin: 0 auto;
}

.flow-node-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.flow-node {
  width: 100%;
  background: #fff;
  border: 2px solid #e4e7ed;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.flow-node:hover {
  border-color: #409eff;
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.2);
}

.flow-node.active {
  border-color: #409eff;
  border-width: 3px;
  box-shadow: 0 4px 20px rgba(64, 158, 255, 0.3);
}

.node-header {
  padding: 14px 16px;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 500;
}

.node-title {
  flex: 1;
  font-size: 15px;
}

.node-body {
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.flow-arrow {
  padding: 12px 0;
  display: flex;
  justify-content: center;
}

/* 右侧配置面板 */
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
  margin-bottom: 12px;
}

.config-panel .panel-header h3 {
  margin: 0;
}
</style>
