<template>
  <div class="workflow-editor">
    <!-- 顶部工具栏 -->
    <div class="top-toolbar">
      <!-- 第一行：基本操作 -->
      <div class="toolbar-row toolbar-main">
        <div class="toolbar-left">
          <el-button @click="goBack" icon="ArrowLeft">返回</el-button>
          <el-divider direction="vertical" />
          <el-input
            v-model="workflowName"
            placeholder="请输入工作流名称"
            style="width: 400px;"
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

      <!-- 第二行：节点工具栏 -->
      <div class="toolbar-row toolbar-nodes">
        <div class="node-toolbar">
          <span class="toolbar-label">
            <el-icon><Box /></el-icon>
            节点工具箱:
          </span>
          <div class="node-buttons">
            <el-button
              v-for="nodeType in nodeTypes"
              :key="nodeType.type"
              @click="addNodeToCenter(nodeType)"
              :disabled="(nodeType.type === 'start' || nodeType.type === 'end') && hasNodeType(nodeType.type)"
              class="node-add-btn"
            >
              <div class="btn-content" :style="{ borderLeftColor: nodeType.color }">
                <el-icon :size="18" :color="nodeType.color">
                  <component :is="nodeType.icon" />
                </el-icon>
                <span>{{ nodeType.label }}</span>
              </div>
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 画布区域 -->
    <div class="canvas-container">
      <VueFlow
        v-model:nodes="nodes"
        v-model:edges="edges"
        :default-viewport="{ zoom: 1 }"
        :min-zoom="0.3"
        :max-zoom="2"
        @node-click="onNodeClick"
        @edge-click="onEdgeClick"
        @connect="onConnect"
        fit-view-on-init
        class="vue-flow-wrapper"
      >
        <Background pattern-color="#e5e7eb" :gap="20" />
        <Controls position="bottom-right" />

        <!-- 自定义节点 -->
        <template #node-custom="{ data, id }">
          <div class="workflow-node" :class="{ selected: selectedNodeId === id }">
            <Handle
              v-if="data.nodeType !== 'start'"
              type="target"
              :position="Position.Left"
              class="node-handle"
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
                <el-tag v-if="data.configured" type="success" size="small">✓ 已配置</el-tag>
                <el-tag v-else type="warning" size="small">待配置</el-tag>
              </div>
            </div>

            <Handle
              v-if="data.nodeType !== 'end'"
              type="source"
              :position="Position.Right"
              class="node-handle"
            />
          </div>
        </template>
      </VueFlow>

      <!-- 空状态 -->
      <div v-if="nodes.length === 0" class="empty-hint">
        <el-icon :size="60" color="#909399"><Box /></el-icon>
        <p>点击顶部工具栏的图标添加节点</p>
      </div>

      <!-- 操作提示 -->
      <div class="operation-tips">
        <el-icon><InfoFilled /></el-icon>
        <span>从节点右侧圆点拖动到目标节点建立连接</span>
      </div>
    </div>

    <!-- 右侧配置抽屉 -->
    <el-drawer
      v-model="showConfigDrawer"
      :title="`配置: ${selectedNode?.data.label || ''}`"
      size="500px"
      direction="rtl"
    >
      <div v-if="selectedNode" class="config-content">
        <el-form :model="selectedNode.data" label-position="top">
          <!-- 基础信息 -->
          <el-divider content-position="left">基础信息</el-divider>
          
          <el-form-item label="节点名称">
            <el-input v-model="selectedNode.data.label" placeholder="输入节点名称" />
          </el-form-item>

          <el-form-item label="节点说明">
            <el-input
              v-model="selectedNode.data.description"
              type="textarea"
              :rows="2"
              placeholder="可选：输入节点说明"
            />
          </el-form-item>

          <!-- 根据节点类型显示不同配置 -->
          <el-divider content-position="left">节点配置</el-divider>

          <!-- 开始节点配置 -->
          <template v-if="selectedNode.data.nodeType === 'start'">
            <el-form-item label="输入参数定义">
              <el-input
                v-model="selectedNode.data.inputSchema"
                type="textarea"
                :rows="6"
                placeholder='定义工作流输入参数 (JSON Schema):
{
  "query": {
    "type": "string",
    "description": "用户问题"
  },
  "user_id": {
    "type": "string",
    "description": "用户ID"
  }
}'
              />
            </el-form-item>
            <el-alert type="info" :closable="false" show-icon>
              <template #title>
                输入参数将在后续节点中通过 {input.参数名} 引用
              </template>
            </el-alert>
          </template>

          <!-- LLM节点配置 -->
          <template v-if="selectedNode.data.nodeType === 'llm'">
            <el-form-item label="选择模型">
              <el-select v-model="selectedNode.data.llmModel" placeholder="请选择LLM模型" filterable>
                <el-option-group label="OpenAI">
                  <el-option label="GPT-4" value="gpt-4" />
                  <el-option label="GPT-3.5 Turbo" value="gpt-3.5-turbo" />
                </el-option-group>
                <el-option-group label="通义千问">
                  <el-option label="Qwen-Max" value="qwen-max" />
                  <el-option label="Qwen-Plus" value="qwen-plus" />
                  <el-option label="Qwen-Turbo" value="qwen-turbo" />
                </el-option-group>
                <el-option-group label="智谱AI">
                  <el-option label="GLM-4" value="glm-4" />
                  <el-option label="GLM-3-Turbo" value="glm-3-turbo" />
                </el-option-group>
              </el-select>
            </el-form-item>

            <el-form-item label="系统提示词">
              <el-input
                v-model="selectedNode.data.systemPrompt"
                type="textarea"
                :rows="4"
                placeholder='定义AI的角色和行为:
你是一个专业的客服助手，需要：
1. 态度友好，回答准确
2. 遇到不清楚的问题要诚实说明'
              />
            </el-form-item>

            <el-form-item label="用户提示词">
              <el-input
                v-model="selectedNode.data.userPrompt"
                type="textarea"
                :rows="6"
                placeholder='输入提示词，支持变量引用:
用户问题: {input.query}
上一节点结果: {node-id.response}
知识库内容: {kb-node.results}

示例：
根据以下信息回答用户问题：
问题：{input.query}
参考资料：{kb-node.results}'
              />
            </el-form-item>

            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="温度参数">
                  <el-slider v-model="selectedNode.data.temperature" :min="0" :max="2" :step="0.1" show-input />
                  <el-text size="small" type="info">值越高，输出越随机创新</el-text>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="最大Token数">
                  <el-input-number v-model="selectedNode.data.maxTokens" :min="100" :max="8000" :step="100" style="width: 100%" />
                  <el-text size="small" type="info">控制回复长度</el-text>
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="Top P">
              <el-slider v-model="selectedNode.data.topP" :min="0" :max="1" :step="0.05" show-input />
              <el-text size="small" type="info">核采样参数，控制输出多样性</el-text>
            </el-form-item>

            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="频率惩罚">
                  <el-slider v-model="selectedNode.data.frequencyPenalty" :min="0" :max="2" :step="0.1" show-input />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="存在惩罚">
                  <el-slider v-model="selectedNode.data.presencePenalty" :min="0" :max="2" :step="0.1" show-input />
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item>
              <el-checkbox v-model="selectedNode.data.streamMode">流式输出（逐字返回）</el-checkbox>
            </el-form-item>

            <el-form-item>
              <el-checkbox v-model="selectedNode.data.jsonMode">JSON模式（返回结构化数据）</el-checkbox>
            </el-form-item>

            <el-alert type="info" :closable="false" show-icon style="margin-top: 12px;">
              <template #title>
                变量引用格式：{node-id.字段名} 或 {input.参数名}
              </template>
            </el-alert>
          </template>

          <!-- HTTP节点配置 -->
          <template v-if="selectedNode.data.nodeType === 'http'">
            <el-form-item label="请求URL">
              <el-input
                v-model="selectedNode.data.url"
                placeholder="https://api.example.com/endpoint"
              >
                <template #prepend>
                  <el-select v-model="selectedNode.data.method" style="width: 100px">
                    <el-option label="GET" value="GET" />
                    <el-option label="POST" value="POST" />
                    <el-option label="PUT" value="PUT" />
                    <el-option label="DELETE" value="DELETE" />
                  </el-select>
                </template>
              </el-input>
            </el-form-item>

            <el-form-item label="请求头">
              <el-input
                v-model="selectedNode.data.headers"
                type="textarea"
                :rows="4"
                placeholder='JSON格式:
{
  "Content-Type": "application/json",
  "Authorization": "Bearer {input.token}"
}'
              />
            </el-form-item>

            <el-form-item label="请求体">
              <el-input
                v-model="selectedNode.data.body"
                type="textarea"
                :rows="6"
                placeholder='JSON格式，支持变量:
{
  "query": "{input.query}",
  "context": "{llm-node.response}"
}'
              />
            </el-form-item>

            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="超时时间(秒)">
                  <el-input-number v-model="selectedNode.data.timeout" :min="1" :max="300" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="重试次数">
                  <el-input-number v-model="selectedNode.data.retryCount" :min="0" :max="5" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item>
              <el-checkbox v-model="selectedNode.data.validateSSL">验证SSL证书</el-checkbox>
              <el-checkbox v-model="selectedNode.data.followRedirect">跟随重定向</el-checkbox>
            </el-form-item>
          </template>

          <!-- 知识库节点配置 -->
          <template v-if="selectedNode.data.nodeType === 'knowledge'">
            <el-form-item label="选择知识库">
              <el-select v-model="selectedNode.data.kbUuid" placeholder="请选择知识库" filterable>
                <el-option label="产品知识库" value="kb-1" />
                <el-option label="技术文档库" value="kb-2" />
              </el-select>
            </el-form-item>

            <el-form-item label="查询文本">
              <el-input
                v-model="selectedNode.data.query"
                type="textarea"
                :rows="3"
                placeholder="支持变量: {input.query}"
              />
            </el-form-item>

            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="返回数量">
                  <el-input-number v-model="selectedNode.data.topK" :min="1" :max="20" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="相似度阈值">
                  <el-slider v-model="selectedNode.data.similarityThreshold" :min="0" :max="1" :step="0.05" show-input />
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="检索模式">
              <el-radio-group v-model="selectedNode.data.searchMode">
                <el-radio label="vector">向量检索</el-radio>
                <el-radio label="hybrid">混合检索</el-radio>
                <el-radio label="keyword">关键词检索</el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="文档过滤">
              <el-input
                v-model="selectedNode.data.filters"
                placeholder='可选，JSON格式: {"category": "产品", "status": "published"}'
              />
            </el-form-item>
          </template>

          <!-- 意图识别节点配置 -->
          <template v-if="selectedNode.data.nodeType === 'intent'">
            <el-form-item label="输入文本">
              <el-input
                v-model="selectedNode.data.inputText"
                placeholder="支持变量: {input.query}"
              />
            </el-form-item>

            <el-form-item label="意图类别">
              <el-select
                v-model="selectedNode.data.intentCategories"
                multiple
                filterable
                allow-create
                placeholder="输入意图类别后回车添加"
                style="width: 100%"
              >
                <el-option label="问答" value="qa" />
                <el-option label="闲聊" value="chat" />
                <el-option label="查询" value="query" />
                <el-option label="命令" value="command" />
              </el-select>
            </el-form-item>

            <el-form-item label="识别方式">
              <el-radio-group v-model="selectedNode.data.recognitionMode">
                <el-radio label="llm">LLM识别</el-radio>
                <el-radio label="keyword">关键词匹配</el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item v-if="selectedNode.data.recognitionMode === 'llm'" label="使用模型">
              <el-select v-model="selectedNode.data.llmModel" placeholder="选择LLM模型">
                <el-option label="GPT-4" value="gpt-4" />
                <el-option label="GPT-3.5" value="gpt-3.5-turbo" />
                <el-option label="Qwen-Max" value="qwen-max" />
                <el-option label="Qwen-Plus" value="qwen-plus" />
              </el-select>
            </el-form-item>

            <el-form-item v-if="selectedNode.data.recognitionMode === 'keyword'" label="关键词映射">
              <el-input
                v-model="selectedNode.data.keywordMapping"
                type="textarea"
                :rows="6"
                placeholder='JSON格式:
{
  "问答": ["问题", "怎么", "如何"],
  "闲聊": ["你好", "天气", "聊天"],
  "查询": ["查询", "查看", "搜索"]
}'
              />
            </el-form-item>

            <el-form-item label="置信度阈值">
              <el-slider v-model="selectedNode.data.confidenceThreshold" :min="0" :max="1" :step="0.05" show-input />
            </el-form-item>
          </template>

          <!-- 字符串处理节点配置 -->
          <template v-if="selectedNode.data.nodeType === 'string'">
            <el-form-item label="操作类型">
              <el-select v-model="selectedNode.data.operation" placeholder="选择操作">
                <el-option label="拼接字符串" value="concat" />
                <el-option label="替换文本" value="replace" />
                <el-option label="截取字符串" value="substring" />
                <el-option label="格式化" value="format" />
                <el-option label="去除空格" value="trim" />
                <el-option label="转大写" value="upper" />
                <el-option label="转小写" value="lower" />
                <el-option label="分割字符串" value="split" />
                <el-option label="提取正则" value="regex" />
              </el-select>
            </el-form-item>

            <el-form-item label="输入字符串">
              <el-input
                v-model="selectedNode.data.inputString"
                placeholder="支持变量: {input.text} 或 {node-id.result}"
              />
            </el-form-item>

            <!-- 拼接 -->
            <template v-if="selectedNode.data.operation === 'concat'">
              <el-form-item label="拼接字符串列表">
                <el-input
                  v-model="selectedNode.data.concatStrings"
                  type="textarea"
                  :rows="4"
                  placeholder='每行一个字符串:
{input.text}
{llm-node.response}
固定文本'
                />
              </el-form-item>
              <el-form-item label="分隔符">
                <el-input v-model="selectedNode.data.separator" placeholder="如: 空格、逗号、换行等" />
              </el-form-item>
            </template>

            <!-- 替换 -->
            <template v-if="selectedNode.data.operation === 'replace'">
              <el-form-item label="查找文本">
                <el-input v-model="selectedNode.data.findText" placeholder="要替换的文本" />
              </el-form-item>
              <el-form-item label="替换为">
                <el-input v-model="selectedNode.data.replaceText" placeholder="新文本" />
              </el-form-item>
              <el-form-item>
                <el-checkbox v-model="selectedNode.data.replaceAll">替换所有</el-checkbox>
                <el-checkbox v-model="selectedNode.data.caseSensitive">区分大小写</el-checkbox>
              </el-form-item>
            </template>

            <!-- 截取 -->
            <template v-if="selectedNode.data.operation === 'substring'">
              <el-row :gutter="16">
                <el-col :span="12">
                  <el-form-item label="开始位置">
                    <el-input-number v-model="selectedNode.data.startIndex" :min="0" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="结束位置">
                    <el-input-number v-model="selectedNode.data.endIndex" :min="0" />
                  </el-form-item>
                </el-col>
              </el-row>
            </template>

            <!-- 正则提取 -->
            <template v-if="selectedNode.data.operation === 'regex'">
              <el-form-item label="正则表达式">
                <el-input v-model="selectedNode.data.regexPattern" placeholder="如: \d+, [a-z]+" />
              </el-form-item>
              <el-form-item label="提取组">
                <el-input-number v-model="selectedNode.data.regexGroup" :min="0" />
              </el-form-item>
            </template>
          </template>

          <!-- 结束节点配置 -->
          <template v-if="selectedNode.data.nodeType === 'end'">
            <el-form-item label="输出配置">
              <el-input
                v-model="selectedNode.data.outputMapping"
                type="textarea"
                :rows="8"
                placeholder='定义工作流输出 (JSON):
{
  "answer": "{llm-node.response}",
  "sources": "{kb-node.results}",
  "intent": "{intent-node.intent}",
  "timestamp": "{system.timestamp}"
}'
              />
            </el-form-item>
            <el-alert type="info" :closable="false" show-icon>
              <template #title>
                可以引用任何节点的输出结果组装最终返回
              </template>
            </el-alert>
          </template>

          <el-divider />

          <el-button type="primary" @click="saveNodeConfig" style="width: 100%">
            保存配置
          </el-button>
        </el-form>
      </div>
    </el-drawer>
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
  InfoFilled
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

const route = useRoute()
const router = useRouter()
const { fitView: vueFlowFitView, project, viewport, vueFlowRef } = useVueFlow()

// 基础数据
const workflowName = ref('')
const workflowUuid = ref(route.params.uuid)
const saving = ref(false)
const selectedNodeId = ref(null)
const showConfigDrawer = ref(false)

// 节点和边
const nodes = ref([])
const edges = ref([])

let nodeIdCounter = 1

// 节点类型定义
const nodeTypes = [
  { type: 'start', label: '开始', icon: 'VideoPlay', color: '#67c23a' },
  { type: 'llm', label: 'LLM调用', icon: 'ChatDotRound', color: '#409eff' },
  { type: 'http', label: 'HTTP请求', icon: 'Link', color: '#e6a23c' },
  { type: 'knowledge', label: '知识库检索', icon: 'Document', color: '#909399' },
  { type: 'intent', label: '意图识别', icon: 'QuestionFilled', color: '#9c27b0' },
  { type: 'string', label: '字符串处理', icon: 'Setting', color: '#00bcd4' },
  { type: 'end', label: '结束', icon: 'SuccessFilled', color: '#f56c6c' }
]

// 选中的节点
const selectedNode = computed(() => {
  return nodes.value.find(n => n.id === selectedNodeId.value)
})

// 检查是否已有某类型节点
const hasNodeType = (type) => {
  return nodes.value.some(n => n.data.nodeType === type)
}

// 添加节点
const addNodeToCenter = (nodeType) => {
  if ((nodeType.type === 'start' || nodeType.type === 'end') && hasNodeType(nodeType.type)) {
    ElMessage.warning(`${nodeType.label}节点只能有一个`)
    return
  }

  // 计算当前视口中心位置
  let centerX = 400
  let centerY = 300
  
  try {
    // 获取画布容器尺寸
    const flowElement = vueFlowRef.value?.$el
    if (flowElement) {
      const rect = flowElement.getBoundingClientRect()
      const screenCenterX = rect.width / 2
      const screenCenterY = rect.height / 2
      
      // 将屏幕坐标转换为画布坐标
      const canvasPosition = project({ x: screenCenterX, y: screenCenterY })
      centerX = canvasPosition.x - 80 // 节点宽度160px的一半
      centerY = canvasPosition.y - 25 // 节点高度50px的一半
    }
  } catch (error) {
    console.warn('无法获取视口中心，使用默认位置', error)
  }

  const newNode = {
    id: `${nodeType.type}-${nodeIdCounter++}`,
    type: 'custom',
    position: {
      x: centerX,
      y: centerY
    },
      data: {
        nodeType: nodeType.type,
        label: nodeType.label,
        icon: nodeType.icon,
        color: nodeType.color,
        configured: false,
        // 默认配置
        description: '',
        // LLM配置
        llmModel: '',
        systemPrompt: '',
        userPrompt: '',
        temperature: 0.7,
        maxTokens: 2000,
        topP: 0.9,
        frequencyPenalty: 0,
        presencePenalty: 0,
        streamMode: false,
        jsonMode: false,
        // HTTP配置
        method: 'POST',
        timeout: 30,
        retryCount: 0,
        validateSSL: true,
        followRedirect: true,
        // 知识库配置
        topK: 5,
        similarityThreshold: 0.7,
        searchMode: 'vector',
        // 意图识别配置
        recognitionMode: 'llm',
        confidenceThreshold: 0.6,
        intentCategories: [],
        // 字符串处理配置
        operation: 'concat',
        separator: '',
        replaceAll: true,
        caseSensitive: false,
        startIndex: 0
      }
  }

  nodes.value.push(newNode)
  
  // 自动选中新添加的节点
  nextTick(() => {
    selectedNodeId.value = newNode.id
    showConfigDrawer.value = true
  })
  
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
      showConfigDrawer.value = false
    }
    ElMessage.success('节点已删除')
  }).catch(() => {})
}

// 节点点击
const onNodeClick = ({ node }) => {
  selectedNodeId.value = node.id
  showConfigDrawer.value = true
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

  const startNodes = nodes.value.filter(n => n.data.nodeType === 'start')
  if (startNodes.length === 0) {
    ElMessage.warning('请先添加开始节点')
    return
  }

  const layers = []
  const visited = new Set()
  const nodeMap = new Map(nodes.value.map(n => [n.id, n]))
  const edgeMap = new Map()

  edges.value.forEach(e => {
    if (!edgeMap.has(e.source)) edgeMap.set(e.source, [])
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
          if (!visited.has(neighbor)) nextQueue.push(neighbor)
        })
      }
    })
    queue = [...new Set(nextQueue)]
    layer++
  }

  layers.forEach((layerNodes, layerIndex) => {
    layerNodes.forEach((nodeId, nodeIndex) => {
      const node = nodeMap.get(nodeId)
      if (node) {
        node.position = {
          x: layerIndex * 250 + 100,
          y: nodeIndex * 100 + 150
        }
      }
    })
  })

  nextTick(() => fitView())
  ElMessage.success('自动排列完成')
}

// 居中显示
const fitView = () => {
  vueFlowFitView({ duration: 300, padding: 0.2 })
}

// 保存节点配置
const saveNodeConfig = () => {
  if (selectedNode.value) {
    selectedNode.value.data.configured = true
    ElMessage.success('配置已保存')
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

  if (!hasStart || !hasEnd) {
    ElMessage.warning('工作流必须有开始和结束节点')
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
    }).then(() => router.push('/workflows')).catch(() => {})
  } else {
    router.push('/workflows')
  }
}

// 加载工作流
const loadWorkflow = async () => {
  if (!workflowUuid.value) return
  try {
    const response = await getWorkflow(workflowUuid.value)
    const workflow = response.data
    workflowName.value = workflow.name
    nodes.value = (workflow.nodes || []).map(node => {
      const nodeType = nodeTypes.find(n => n.type === node.type)
      return {
        ...node,
        type: 'custom',
        data: {
          ...node.data,
          nodeType: node.type,
          icon: nodeType?.icon || 'Setting',
          color: nodeType?.color || '#409eff'
        }
      }
    })
    edges.value = (workflow.edges || []).map(edge => ({
      ...edge,
      type: 'smoothstep',
      animated: true,
      style: { stroke: '#409eff', strokeWidth: 2 }
    }))
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
  }
}

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

.top-toolbar {
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  z-index: 100;
}

.toolbar-row {
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.toolbar-main {
  height: 56px;
  border-bottom: 1px solid #f0f0f0;
}

.toolbar-nodes {
  height: 52px;
  background: #fafafa;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.node-toolbar {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 16px;
}

.toolbar-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #606266;
  font-weight: 500;
  white-space: nowrap;
}

.node-buttons {
  flex: 1;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}

.node-add-btn {
  padding: 0;
  border: none;
  background: transparent;
  transition: all 0.3s;
}

.node-add-btn .btn-content {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  background: #fff;
  border: 1.5px solid #e4e7ed;
  border-left-width: 4px;
  border-radius: 6px;
  transition: all 0.3s;
}

.node-add-btn:hover:not(:disabled) .btn-content {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.15);
  transform: translateY(-1px);
}

.node-add-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.node-add-btn .btn-content span {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
}

.canvas-container {
  flex: 1;
  position: relative;
}

.vue-flow-wrapper {
  width: 100%;
  height: 100%;
}

.empty-hint {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  z-index: 5;
  pointer-events: none;
}

.empty-hint p {
  margin-top: 16px;
  color: #909399;
  font-size: 14px;
}

.operation-tips {
  position: absolute;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(255, 255, 255, 0.95);
  padding: 10px 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #606266;
  z-index: 10;
}

.workflow-node {
  width: 160px;
  height: 50px;
  background: #fff;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  overflow: visible;
  transition: all 0.3s;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
}

.workflow-node:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  transform: translateY(-1px);
}

.workflow-node.selected {
  border-color: #409eff;
  border-width: 2px;
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.2);
}

.node-content {
  width: 100%;
  height: 100%;
}

.node-header {
  height: 100%;
  padding: 0 12px;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 8px;
  border-radius: 6px;
}

.node-title {
  flex: 1;
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-tag {
  border: none;
  font-weight: bold;
  min-width: 22px;
  height: 22px;
  padding: 0 6px;
}

.node-handle {
  width: 12px;
  height: 12px;
  border: 2px solid #fff;
  background: #409eff;
  transition: all 0.3s;
  border-radius: 50%;
}

.node-handle:hover {
  width: 16px;
  height: 16px;
  border-width: 3px;
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.3);
}

.config-content {
  padding-bottom: 20px;
}

/* 连接线样式 */
:deep(.vue-flow__edge-path) {
  stroke: #409eff;
  stroke-width: 2;
}

:deep(.vue-flow__edge.selected .vue-flow__edge-path) {
  stroke: #f56c6c;
  stroke-width: 3;
}

:deep(.vue-flow__edge:hover .vue-flow__edge-path) {
  stroke: #66b1ff;
  stroke-width: 3;
}

:deep(.vue-flow__connection-path) {
  stroke: #409eff;
  stroke-width: 2;
  stroke-dasharray: 8, 4;
  animation: dash 0.8s linear infinite;
}

@keyframes dash {
  to {
    stroke-dashoffset: -12;
  }
}

/* 边的文本 */
:deep(.vue-flow__edge-text) {
  font-size: 12px;
  fill: #606266;
}

/* 边的删除按钮 */
:deep(.vue-flow__edge-textbg) {
  fill: #fff;
}

:deep(.el-drawer__body) {
  padding: 20px;
}
</style>
