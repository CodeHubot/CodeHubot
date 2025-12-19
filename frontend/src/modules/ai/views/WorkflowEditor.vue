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
          <el-select v-model="edgeType" placeholder="连线样式" style="width: 140px;" @change="changeEdgeType">
            <el-option label="🎯 平滑直角" value="smoothstep" />
            <el-option label="📐 直角折线" value="step" />
            <el-option label="〰️ 贝塞尔曲线" value="default" />
            <el-option label="➖ 直线" value="straight" />
            <el-option label="🌊 简单曲线" value="simplebezier" />
          </el-select>
          
          <el-button-group>
            <el-button @click="autoLayout" icon="MagicStick">自动排列</el-button>
            <el-button @click="fitView" icon="FullScreen">居中显示</el-button>
          </el-button-group>
          <el-button @click="handleRun" type="success" icon="VideoPlay" :loading="running">
            运行
          </el-button>
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
            <div
              v-for="nodeType in draggableNodeTypes"
              :key="nodeType.type"
              draggable="true"
              @dragstart="onDragStart($event, nodeType)"
              class="node-add-btn"
            >
              <div class="btn-content" :style="{ borderLeftColor: nodeType.color }">
                <el-icon :size="18" :color="nodeType.color">
                  <component :is="nodeType.icon" />
                </el-icon>
                <span>{{ nodeType.label }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 画布区域 -->
    <div 
      class="canvas-container"
      @drop="onDrop"
      @dragover="onDragOver"
    >
      <VueFlow
        v-model:nodes="nodes"
        v-model:edges="edges"
        :default-viewport="{ zoom: 1 }"
        :min-zoom="0.4"
        :max-zoom="1.8"
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

            <div class="node-header" :style="{ background: data.color }">
              <el-icon :size="16">
                <component :is="data.icon" />
              </el-icon>
              <span class="node-title">{{ data.label }}</span>
              <div class="node-actions">
                <span v-if="data.configured" class="status-icon success" title="已配置">✓</span>
                <span v-else class="status-icon warning" title="待配置">!</span>
                <el-button
                  v-if="data.nodeType !== 'start' && data.nodeType !== 'end'"
                  type="danger"
                  size="small"
                  circle
                  class="delete-btn"
                  @click.stop="deleteNode(id)"
                  title="删除节点"
                >
                  <el-icon :size="12"><Close /></el-icon>
                </el-button>
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
        <span>💡 拖拽节点到画布添加 | 拖动节点间圆点连线 | 单击节点配置 | 悬停显示删除 ✕</span>
      </div>

      <!-- 右侧执行面板 (暂时禁用) -->
      <!-- <transition name="slide-fade">
        <div v-if="showExecutionPanel" class="execution-panel-wrapper">
          <ExecutionPanel
            :nodes="nodes"
            :start-node-params="startNodeParams"
            :running="running"
            :run-result="runResult"
            @close="showExecutionPanel = false"
            @run="confirmRun"
          />
        </div>
      </transition> -->
    </div>

    <!-- 右侧配置抽屉 -->
    <el-drawer
      v-model="showConfigDrawer"
      :title="selectedNode ? `配置: ${selectedNode.data.label}` : selectedEdge ? '连线条件配置' : '配置'"
      size="500px"
      direction="rtl"
    >
      <!-- 边的配置 -->
      <div v-if="selectedEdge && !selectedNode" class="config-content">
        <el-form label-position="top">
          <el-divider content-position="left">连线信息</el-divider>
          
          <el-form-item label="连线标签">
            <el-input 
              v-model="selectedEdge.label" 
              placeholder="可选，显示在连线上的文字"
              clearable
            />
            <div style="color: #909399; font-size: 12px; margin-top: 4px;">
              例如："是"、"否"、"查询天气"等
            </div>
          </el-form-item>

          <el-divider content-position="left">条件配置</el-divider>
          
          <el-form-item label="条件类型">
            <el-select 
              v-model="selectedEdge.condition" 
              placeholder="选择条件类型" 
              @change="onConditionTypeChange"
              clearable
            >
              <el-option label="无条件（默认）" :value="null" />
              <el-option label="意图匹配" value="intent_match" />
              <el-option label="字段值相等" value="field_equals" />
              <el-option label="字段包含文本" value="field_contains" />
              <el-option label="总是执行" value="always" />
            </el-select>
            <div style="color: #909399; font-size: 12px; margin-top: 4px;">
              用于条件分支，根据上一个节点的输出决定是否执行此路径
            </div>
          </el-form-item>

          <!-- 意图匹配配置 -->
          <template v-if="selectedEdge.condition === 'intent_match'">
            <el-form-item label="字段名">
              <el-input v-model="selectedEdge.conditionField" placeholder="默认: intent" />
            </el-form-item>
            <el-form-item label="匹配值">
              <el-input 
                v-model="selectedEdge.conditionValue" 
                placeholder="例如: 查询天气" 
                required
              />
              <div style="color: #909399; font-size: 12px; margin-top: 4px;">
                当上一个节点输出的意图等于此值时，执行此路径
              </div>
            </el-form-item>
          </template>

          <!-- 字段相等配置 -->
          <template v-if="selectedEdge.condition === 'field_equals'">
            <el-form-item label="字段名">
              <el-input 
                v-model="selectedEdge.conditionField" 
                placeholder="例如: status" 
                required
              />
            </el-form-item>
            <el-form-item label="匹配值">
              <el-input 
                v-model="selectedEdge.conditionValue" 
                placeholder="例如: success" 
                required
              />
            </el-form-item>
          </template>

          <!-- 字段包含配置 -->
          <template v-if="selectedEdge.condition === 'field_contains'">
            <el-form-item label="字段名">
              <el-input 
                v-model="selectedEdge.conditionField" 
                placeholder="例如: result" 
                required
              />
            </el-form-item>
            <el-form-item label="包含文本">
              <el-input 
                v-model="selectedEdge.conditionValue" 
                placeholder="例如: error" 
                required
              />
            </el-form-item>
          </template>

          <el-divider />

          <div style="display: flex; gap: 12px;">
            <el-button type="danger" @click="deleteSelectedEdge" style="flex: 1;">
              <el-icon><Delete /></el-icon>
              删除连线
            </el-button>
            <el-button @click="showConfigDrawer = false; selectedEdgeId = null" style="flex: 1;">
              关闭
            </el-button>
          </div>
        </el-form>
      </div>

      <!-- 节点的配置 -->
      <div v-if="selectedNode" class="config-content">
        <el-form :model="selectedNode.data" label-position="top">
          <!-- 基础信息 -->
          <el-divider content-position="left">基础信息</el-divider>
          
          <el-form-item label="节点名称">
            <el-input 
              v-model="selectedNode.data.label" 
              placeholder="输入节点名称" 
              :disabled="selectedNode.data.nodeType === 'start' || selectedNode.data.nodeType === 'end'"
            />
          </el-form-item>

          <el-form-item label="节点说明" v-if="selectedNode.data.nodeType !== 'start' && selectedNode.data.nodeType !== 'end'">
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
            <el-form-item label="输入参数配置" class="no-label-margin">
              <div class="params-container">
                <!-- 表头 -->
                <div class="params-header" v-if="selectedNode.data.parameters?.length > 0">
                  <div class="col-main">参数名 & 描述</div>
                  <div class="col-type">类型</div>
                  <div class="col-req">必填</div>
                  <div class="col-action"></div>
                </div>

                <!-- 列表内容 -->
                <div v-for="(param, index) in selectedNode.data.parameters" :key="index" class="param-row-item">
                  <div class="col-main">
                    <el-input 
                      v-model="param.name" 
                      placeholder="参数名 (如 query)" 
                      class="param-name-input"
                    />
                    <el-input 
                      v-model="param.description" 
                      placeholder="描述 (可选)" 
                      size="small" 
                      class="param-desc-input"
                    />
                  </div>
                  <div class="col-type">
                    <el-select v-model="param.type" placeholder="类型" size="small">
                      <el-option label="String" value="string" />
                      <el-option label="Number" value="number" />
                      <el-option label="Boolean" value="boolean" />
                    </el-select>
                  </div>
                  <div class="col-req">
                    <el-switch v-model="param.required" size="small" />
                  </div>
                  <div class="col-action">
                    <el-button 
                      type="danger" 
                      link 
                      @click="removeStartParameter(index)"
                      class="row-delete-btn"
                    >
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </div>
                </div>

                <!-- 空状态 -->
                <div v-if="!selectedNode.data.parameters || selectedNode.data.parameters.length === 0" class="empty-state">
                  <el-icon><InfoFilled /></el-icon>
                  <span>暂无输入参数，点击下方按钮添加</span>
                </div>

                <!-- 添加按钮 -->
                <el-button class="add-param-btn" @click="addStartParameter" plain icon="Plus">
                  添加参数
                </el-button>
              </div>
            </el-form-item>
            <el-alert type="info" :closable="false" show-icon class="mt-2">
              <template #title>
                通过 {input.参数名} 引用这些参数
              </template>
            </el-alert>
          </template>

          <!-- LLM节点配置 -->
          <template v-if="selectedNode.data.nodeType === 'llm'">
            <el-form-item label="选择模型">
              <el-select v-model="selectedNode.data.llmModel" placeholder="留空则使用系统默认模型" filterable clearable>
                <el-option-group
                  v-for="group in llmModelOptions"
                  :key="group.label"
                  :label="group.label"
                >
                  <el-option
                    v-for="item in group.options"
                    :key="item.name"
                    :label="item.display_name"
                    :value="item.name"
                  />
                </el-option-group>
              </el-select>
            </el-form-item>

            <el-form-item label="系统提示词">
              <div class="input-with-var">
                <el-input
                  v-model="selectedNode.data.systemPrompt"
                  type="textarea"
                  :rows="4"
                  placeholder='定义AI的角色和行为...'
                />
                <el-button class="var-trigger" size="small" @click="openVarSelector(selectedNode.data, 'systemPrompt')">
                  {x}
                </el-button>
              </div>
            </el-form-item>

            <el-form-item label="用户提示词">
              <div class="input-with-var">
                <el-input
                  v-model="selectedNode.data.userPrompt"
                  type="textarea"
                  :rows="6"
                  placeholder='输入提示词，支持变量引用...'
                />
                <el-button class="var-trigger" size="small" @click="openVarSelector(selectedNode.data, 'userPrompt')">
                  {x}
                </el-button>
              </div>
            </el-form-item>

            <el-collapse>
              <el-collapse-item title="高级参数设置" name="1">
                <el-row :gutter="16">
                  <el-col :span="12">
                    <el-form-item label="温度参数">
                      <el-slider v-model="selectedNode.data.temperature" :min="0" :max="2" :step="0.1" show-input :show-input-controls="false" />
                      <el-text size="small" type="info">值越高，输出越随机</el-text>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="最大Token数">
                      <el-input-number v-model="selectedNode.data.maxTokens" :min="100" :max="8000" :step="100" style="width: 100%" />
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-form-item label="Top P">
                  <el-slider v-model="selectedNode.data.topP" :min="0" :max="1" :step="0.05" show-input :show-input-controls="false" />
                  <el-text size="small" type="info">核采样参数，控制输出多样性</el-text>
                </el-form-item>

                <el-row :gutter="16">
                  <el-col :span="12">
                    <el-form-item label="频率惩罚">
                      <el-slider v-model="selectedNode.data.frequencyPenalty" :min="0" :max="2" :step="0.1" show-input :show-input-controls="false" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="存在惩罚">
                      <el-slider v-model="selectedNode.data.presencePenalty" :min="0" :max="2" :step="0.1" show-input :show-input-controls="false" />
                    </el-form-item>
                  </el-col>
                </el-row>

                <div style="margin-top: 10px; display: flex; gap: 20px;">
                  <el-checkbox v-model="selectedNode.data.streamMode">流式输出</el-checkbox>
                  <el-checkbox v-model="selectedNode.data.jsonMode">JSON模式</el-checkbox>
                </div>
              </el-collapse-item>
            </el-collapse>

            <el-alert type="info" :closable="false" show-icon style="margin-top: 12px;">
              <template #title>
                变量引用格式：{node-id.字段名} 或 {input.参数名}
              </template>
            </el-alert>
          </template>

          <!-- HTTP节点配置 -->
          <template v-if="selectedNode.data.nodeType === 'http'">
            <el-form-item label="请求URL">
              <div class="input-with-var">
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
                <el-button class="var-trigger" size="small" @click="openVarSelector(selectedNode.data, 'url')">
                  {x}
                </el-button>
              </div>
            </el-form-item>

            <el-form-item label="请求头配置" class="no-label-margin">
              <div class="params-container">
                <div class="params-header" v-if="selectedNode.data.headerParams?.length > 0">
                  <div class="col-main" style="flex: 1">Key</div>
                  <div class="col-main" style="flex: 1">Value</div>
                  <div class="col-action"></div>
                </div>

                <div v-for="(param, index) in selectedNode.data.headerParams" :key="index" class="param-row-item">
                  <div class="col-main" style="flex: 1; padding-right: 8px;">
                    <el-input v-model="param.key" placeholder="Key" />
                  </div>
                  <div class="col-main" style="flex: 1; position: relative;">
                    <el-input v-model="param.value" placeholder="Value" style="padding-right: 32px" />
                    <el-button class="cell-var-trigger" size="small" link @click="openVarSelector(param, 'value')">
                      {x}
                    </el-button>
                  </div>
                  <div class="col-action">
                    <el-button 
                      type="danger" 
                      link 
                      @click="removeHeaderParam(index)"
                      class="row-delete-btn"
                    >
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </div>
                </div>
                
                <div v-if="!selectedNode.data.headerParams || selectedNode.data.headerParams.length === 0" class="empty-state">
                  <el-icon><InfoFilled /></el-icon>
                  <span>暂无请求头，点击下方按钮添加</span>
                </div>

                <el-button class="add-param-btn" @click="addHeaderParam" plain icon="Plus">
                  添加请求头
                </el-button>
              </div>
            </el-form-item>

            <el-form-item label="请求体">
              <div class="input-with-var">
                <el-input
                  v-model="selectedNode.data.body"
                  type="textarea"
                  :rows="6"
                  placeholder='JSON格式，支持变量...'
                />
                <el-button class="var-trigger" size="small" @click="openVarSelector(selectedNode.data, 'body')">
                  {x}
                </el-button>
              </div>
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
              <el-select v-model="selectedNode.data.kb_uuid" placeholder="请选择知识库" filterable>
                <el-option
                  v-for="kb in knowledgeBases"
                  :key="kb.uuid"
                  :label="`${kb.name} (${kb.document_count}篇文档, ${kb.chunk_count}个片段)`"
                  :value="kb.uuid"
                >
                  <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span>{{ kb.name }}</span>
                    <span style="color: #909399; font-size: 12px;">{{ kb.scope_type }}</span>
                  </div>
                </el-option>
              </el-select>
              <div class="help-text" v-if="knowledgeBases.length === 0">
                暂无可用知识库，请先在知识库管理中创建
              </div>
            </el-form-item>

            <el-form-item label="查询文本">
              <div class="input-with-var">
                <el-input
                  v-model="selectedNode.data.query"
                  type="textarea"
                  :rows="3"
                  placeholder="输入查询文本，支持变量: {input.query}"
                />
                <el-button class="var-trigger" size="small" @click="openVarSelector(selectedNode.data, 'query')">
                  {x}
                </el-button>
              </div>
            </el-form-item>

            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="返回数量">
                  <el-input-number v-model="selectedNode.data.top_k" :min="1" :max="20" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="相似度阈值">
                  <el-slider v-model="selectedNode.data.similarity_threshold" :min="0" :max="1" :step="0.05" show-input />
                </el-form-item>
              </el-col>
            </el-row>
          </template>

          <!-- 意图识别节点配置 -->
          <template v-if="selectedNode.data.nodeType === 'intent'">
            <el-alert type="info" :closable="false" style="margin-bottom: 16px;">
              <template #title>
                <div style="font-size: 13px;">
                  🎯 意图识别用于条件分支：根据用户输入识别意图，然后通过设置不同的<strong>连线条件</strong>执行不同的路径
                </div>
              </template>
            </el-alert>

            <el-form-item label="输入文本" required>
              <div class="input-with-var">
                <el-input
                  v-model="selectedNode.data.input_text"
                  placeholder="例如: {input.query} 或 {start-1.user_input}"
                />
                <el-button class="var-trigger" size="small" @click="openVarSelector(selectedNode.data, 'input_text')">
                  {x}
                </el-button>
              </div>
              <div style="color: #909399; font-size: 12px; margin-top: 4px;">
                待识别的文本内容，通常来自用户输入或上一个节点的输出
              </div>
            </el-form-item>

            <el-form-item label="意图类别" required>
              <el-select
                v-model="selectedNode.data.intent_categories"
                multiple
                filterable
                allow-create
                placeholder="输入意图类别后按回车添加，例如：查询天气、播放音乐、控制设备"
                style="width: 100%"
              >
                <el-option label="🌤️ 查询天气" value="查询天气" />
                <el-option label="🎵 播放音乐" value="播放音乐" />
                <el-option label="💡 控制设备" value="控制设备" />
                <el-option label="❓ 问答查询" value="问答查询" />
                <el-option label="💬 闲聊对话" value="闲聊对话" />
                <el-option label="🔍 搜索信息" value="搜索信息" />
              </el-select>
              <div style="color: #909399; font-size: 12px; margin-top: 4px;">
                支持自定义意图，输入后按回车即可添加。添加后需要在<strong>连线上配置对应的条件</strong>
              </div>
            </el-form-item>

            <el-form-item label="识别方式">
              <el-radio-group v-model="selectedNode.data.recognition_mode">
                <el-radio value="llm">🤖 LLM智能识别（推荐）</el-radio>
                <el-radio value="keyword">🔑 关键词匹配</el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item v-if="selectedNode.data.recognition_mode === 'llm'" label="使用智能体" required>
              <el-select v-model="selectedNode.data.agent_uuid" placeholder="选择智能体" filterable>
                <el-option
                  v-for="agent in agents"
                  :key="agent.uuid"
                  :label="`${agent.name} ${agent.llm_model_name ? `(${agent.llm_model_name})` : ''}`"
                  :value="agent.uuid"
                >
                  <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span>{{ agent.name }}</span>
                    <span style="color: #909399; font-size: 12px;">{{ agent.llm_model_name }}</span>
                  </div>
                </el-option>
              </el-select>
              <div style="color: #909399; font-size: 12px; margin-top: 4px;">
                使用智能体的LLM模型进行意图识别，准确度更高
              </div>
            </el-form-item>

            <el-form-item v-if="selectedNode.data.recognition_mode === 'keyword'" label="关键词映射" required>
              <el-input
                v-model="selectedNode.data.keyword_mapping"
                type="textarea"
                :rows="8"
                placeholder='JSON格式，将意图类别映射到关键词：
{
  "查询天气": ["天气", "气温", "下雨", "晴天"],
  "播放音乐": ["播放", "音乐", "歌曲", "听歌"],
  "控制设备": ["打开", "关闭", "控制", "设备"]
}'
              />
              <div style="color: #909399; font-size: 12px; margin-top: 4px;">
                当输入文本包含某个意图的关键词时，识别为该意图
              </div>
            </el-form-item>

            <el-divider content-position="left">高级选项</el-divider>

            <el-form-item label="置信度阈值">
              <el-slider v-model="selectedNode.data.confidence_threshold" :min="0" :max="1" :step="0.05" show-input />
              <div style="color: #909399; font-size: 12px; margin-top: 4px;">
                识别结果的置信度低于此值时，判定为"未知"意图
              </div>
            </el-form-item>

            <el-divider />

            <el-alert type="success" :closable="false">
              <template #title>
                <div style="font-size: 12px;">
                  <strong>💡 使用提示</strong><br />
                  1. 配置好意图类别后，点击节点出来的<strong>连线</strong><br />
                  2. 在连线上设置<strong>条件</strong>，例如"意图匹配=查询天气"<br />
                  3. 这样就能根据不同意图执行不同的节点路径
                </div>
              </template>
            </el-alert>
          </template>

          <!-- 字符串处理节点配置 -->
          <template v-if="selectedNode.data.nodeType === 'string'">
            <el-form-item label="操作类型">
              <el-select v-model="selectedNode.data.operation" placeholder="选择操作">
                <el-option label="📝 文本模板（推荐）" value="template" />
                <el-option label="➕ 拼接字符串" value="concat" />
                <el-option label="🔄 替换文本" value="replace" />
                <el-option label="✂️ 分割字符串" value="split" />
                <el-option label="📏 截取字符串" value="substring" />
                <el-option label="🧹 去除空格" value="trim" />
                <el-option label="🔠 转大写" value="upper" />
                <el-option label="🔡 转小写" value="lower" />
                <el-option label="🔍 正则提取" value="regex" />
              </el-select>
            </el-form-item>

            <!-- 模板模式（最简单） -->
            <template v-if="selectedNode.data.operation === 'template'">
              <el-form-item label="文本模板">
                <div class="input-with-var">
                  <el-input
                    v-model="selectedNode.data.template"
                    type="textarea"
                    :rows="6"
                    placeholder="直接编写文本，支持变量引用：
你好，{input.name}！

根据你的问题：{input.query}

我的回答是：{llm-1.response}"
                  />
                  <el-button class="var-trigger" size="small" @click="openVarSelector(selectedNode.data, 'template')">
                    {x}
                  </el-button>
                </div>
                <div class="help-text">最简单的方式：直接编写文本，用 {变量名} 引用其他节点的输出</div>
              </el-form-item>
            </template>

            <!-- 其他操作需要输入 -->
            <el-form-item label="输入文本" v-if="selectedNode.data.operation !== 'template'">
              <div class="input-with-var">
                <el-input
                  v-model="selectedNode.data.input"
                  placeholder="支持变量: {input.text} 或 {llm-1.response}"
                />
                <el-button class="var-trigger" size="small" @click="openVarSelector(selectedNode.data, 'input')">
                  {x}
                </el-button>
              </div>
            </el-form-item>

            <!-- 拼接 -->
            <template v-if="selectedNode.data.operation === 'concat'">
              <el-form-item label="要拼接的文本">
                <div class="input-with-var">
                  <el-input
                    v-model="selectedNode.data.texts"
                    type="textarea"
                    :rows="5"
                    placeholder="每行一个文本，支持变量：
{input.text}
{llm-1.response}
固定文本内容"
                  />
                  <el-button class="var-trigger" size="small" @click="openVarSelector(selectedNode.data, 'texts')">
                    {x}
                  </el-button>
                </div>
              </el-form-item>
              <el-form-item label="分隔符">
                <el-input v-model="selectedNode.data.separator" placeholder="如: 空格、逗号、换行 (\n)" />
              </el-form-item>
            </template>

            <!-- 替换 -->
            <template v-if="selectedNode.data.operation === 'replace'">
              <el-form-item label="查找内容">
                <el-input v-model="selectedNode.data.find" placeholder="要查找的文本" />
              </el-form-item>
              <el-form-item label="替换为">
                <el-input v-model="selectedNode.data.replace_with" placeholder="替换成的文本" />
              </el-form-item>
              <el-form-item>
                <el-checkbox v-model="selectedNode.data.replace_all">替换所有匹配</el-checkbox>
                <el-checkbox v-model="selectedNode.data.case_sensitive">区分大小写</el-checkbox>
              </el-form-item>
            </template>

            <!-- 分割 -->
            <template v-if="selectedNode.data.operation === 'split'">
              <el-form-item label="分隔符">
                <el-input v-model="selectedNode.data.separator" placeholder="如: 逗号、空格、换行(\n)" />
                <div class="help-text">将文本按分隔符分割成列表</div>
              </el-form-item>
              <el-form-item label="最大分割次数">
                <el-input-number v-model="selectedNode.data.max_split" :min="-1" />
                <div class="help-text">-1 表示不限制</div>
              </el-form-item>
            </template>

            <!-- 截取 -->
            <template v-if="selectedNode.data.operation === 'substring'">
              <el-row :gutter="16">
                <el-col :span="12">
                  <el-form-item label="开始位置">
                    <el-input-number v-model="selectedNode.data.start" :min="0" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="结束位置">
                    <el-input-number v-model="selectedNode.data.end" :min="0" />
                    <div class="help-text">0 表示到末尾</div>
                  </el-form-item>
                </el-col>
              </el-row>
            </template>

            <!-- 正则提取 -->
            <template v-if="selectedNode.data.operation === 'regex'">
              <el-form-item label="正则表达式">
                <el-input v-model="selectedNode.data.pattern" placeholder="如: \d+, [a-zA-Z]+" />
              </el-form-item>
              <el-form-item label="提取组">
                <el-input-number v-model="selectedNode.data.group" :min="0" />
                <div class="help-text">0 表示整个匹配，1+ 表示捕获组</div>
              </el-form-item>
              <el-form-item>
                <el-checkbox v-model="selectedNode.data.find_all">查找所有匹配</el-checkbox>
              </el-form-item>
            </template>
          </template>

          <!-- 结束节点配置 -->
          <template v-if="selectedNode.data.nodeType === 'end'">
            <el-form-item label="最终输出内容" class="no-label-margin">
              <div class="input-with-var">
                <el-input
                  v-model="selectedNode.data.outputContent"
                  type="textarea"
                  :rows="10"
                  placeholder="在此编辑工作流的最终返回内容。
例如：
智能助手回复：{llm.response}
参考文档：{kb.results}"
                />
                <el-button class="var-trigger" size="small" @click="openVarSelector(selectedNode.data, 'outputContent')">
                  {x}
                </el-button>
              </div>
            </el-form-item>
            <el-alert type="info" :closable="false" show-icon class="mt-2">
              <template #title>
                这是工作流运行结束后返回给用户的最终结果
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

    <!-- 变量选择器弹窗 -->
    <el-dialog
      v-model="showVarSelector"
      title="插入变量"
      width="500px"
      class="var-selector-dialog"
    >
      <div v-if="!showVarConfig">
        <div class="var-list">
          <div 
            v-for="variable in availableVars" 
            :key="variable.reference" 
            class="var-item"
            @click="selectVariable(variable)"
          >
            <div class="var-info">
              <div class="var-header">
                <el-tag size="small" effect="plain">{{ variable.type }}</el-tag>
                <span class="var-name">{{ variable.name }}</span>
              </div>
              <div class="var-desc">{{ variable.desc }}</div>
            </div>
            <div class="var-source">
              来自: {{ variable.nodeLabel }}
            </div>
          </div>
        </div>
      </div>
      
      <!-- 变量高级配置 -->
      <div v-else class="var-config">
        <div class="config-header">
          <el-button link @click="showVarConfig = false" icon="ArrowLeft">返回列表</el-button>
          <span class="selected-var-name">{{ selectedVariable?.name }}</span>
        </div>
        
        <div class="config-body">
          <el-alert
            type="info"
            :closable="false"
            class="mb-3"
            show-icon
          >
            <template #title>
              该变量为对象类型，您可以指定子属性进行访问
            </template>
          </el-alert>
          
          <div class="current-ref">
            <div class="label">当前引用:</div>
            <div class="value">{{ getFullReference() }}</div>
          </div>

          <div v-if="selectedVariable?.children?.length" style="margin-bottom: 16px;">
            <div style="margin-bottom: 8px; font-size: 14px; color: #606266;">可选属性:</div>
            <div style="display: flex; flex-wrap: wrap; gap: 8px;">
              <el-tag 
                v-for="child in selectedVariable.children"
                :key="child.name"
                style="cursor: pointer;"
                :effect="subPropertyPath === child.name ? 'dark' : 'plain'"
                @click="subPropertyPath = child.name"
              >
                {{ child.label || child.name }}
              </el-tag>
            </div>
          </div>
          
          <el-form-item label="子属性路径 (可选)">
            <el-input 
              v-model="subPropertyPath" 
              placeholder="例如: user.name 或 data.id"
              @keyup.enter="confirmInsertVar"
            >
              <template #prepend>.</template>
            </el-input>
            <div class="form-tip">
              使用点号分隔访问对象内部属性。留空则引用整个对象。
            </div>
          </el-form-item>
        </div>
        
        <div class="config-footer">
          <el-button @click="showVarConfig = false">取消</el-button>
          <el-button type="primary" @click="confirmInsertVar">确认插入</el-button>
        </div>
      </div>
    </el-dialog>

    <!-- 运行配置弹窗 -->
    <el-dialog
      v-model="showRunDialog"
      title="运行工作流"
      width="500px"
    >
      <el-form :model="runParams" label-position="top">
        <template v-if="startNodeParams.length > 0">
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
        </template>
        <div v-else class="empty-params">
          <el-icon color="#909399"><InfoFilled /></el-icon>
          <span style="margin-left: 8px; color: #909399;">该工作流无需输入参数</span>
        </div>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showRunDialog = false">取消</el-button>
          <el-button type="primary" @click="confirmRun" :loading="running">
            开始运行
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 运行结果弹窗 -->
    <el-dialog
      v-model="showResultDialog"
      title="运行结果"
      width="600px"
    >
      <div v-if="runResult" class="run-result">
        <div class="result-header">
          <el-tag :type="runResult.status === 'completed' ? 'success' : 'danger'">
            {{ runResult.status === 'completed' ? '执行成功' : '执行失败' }}
          </el-tag>
          <span class="time">耗时: {{ runResult.execution_time }}ms</span>
        </div>
        
        <div class="result-section">
          <div class="section-title">输出结果</div>
          <div class="code-block">
            <pre>{{ JSON.stringify(runResult.output, null, 2) }}</pre>
          </div>
        </div>

        <div v-if="runResult.error_message" class="result-section">
          <div class="section-title error">错误信息</div>
          <div class="error-msg">{{ runResult.error_message }}</div>
        </div>

        <el-collapse style="margin-top: 16px;">
          <el-collapse-item title="节点执行详情" name="1">
            <el-timeline>
              <el-timeline-item
                v-for="node in runResult.node_executions"
                :key="node.node_id"
                :type="node.status === 'success' ? 'success' : 'danger'"
                :timestamp="`${node.execution_time}ms`"
                placement="top"
              >
                <div class="node-exec-card">
                  <div class="node-exec-header">
                    <span class="node-id">{{ node.node_id }}</span>
                    <span class="node-type">{{ node.node_type }}</span>
                  </div>
                  <div v-if="node.output" class="node-output">
                    <pre>{{ JSON.stringify(node.output, null, 2) }}</pre>
                  </div>
                  <div v-if="node.error_message" class="node-error">
                    {{ node.error_message }}
                  </div>
                </div>
              </el-timeline-item>
            </el-timeline>
          </el-collapse-item>
        </el-collapse>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  Delete,
  Plus,
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
  updateWorkflow,
  executeWorkflow
} from '@device/api/workflow'
import { getActiveLLMModels } from '@/api/llm-model'
import { getKnowledgeBases } from '@device/api/knowledgeBases'
import { getAgents } from '@device/api/agent'
// import ExecutionPanel from '@device/components/workflow/ExecutionPanel.vue' // 组件暂时不可用

const route = useRoute()
const router = useRouter()
const { fitView: vueFlowFitView, project, viewport, vueFlowRef } = useVueFlow()

// 基础数据
const workflowName = ref('')
const workflowUuid = ref(route.params.uuid)
const saving = ref(false)
const running = ref(false)
const selectedNodeId = ref(null)
const selectedEdgeId = ref(null)
const showConfigDrawer = ref(false)
const showExecutionPanel = ref(false)

// 运行相关
const showRunDialog = ref(false)
const showResultDialog = ref(false)
const runParams = ref({})
const startNodeParams = ref([])
const runResult = ref(null)
const llmModelOptions = ref([])
const knowledgeBases = ref([])
const agents = ref([])

// 节点和边
const nodes = ref([])
const edges = ref([])

// 连线类型
const edgeType = ref('simplebezier')

let nodeIdCounter = 1

// 获取某个节点的输出定义
const getNodeOutputs = (node) => {
  const type = node.data.nodeType
  const outputs = []
  
  switch (type) {
    case 'start':
      // Start 节点的输出就是它定义的参数
      (node.data.parameters || []).forEach(p => {
        outputs.push({
          name: p.name,
          type: p.type,
          label: p.description || p.name,
          desc: `开始节点参数`
        })
      })
      break
    case 'llm':
      outputs.push({ name: 'response', type: 'string', label: 'LLM回复', desc: 'AI生成的文本' })
      outputs.push({
        name: 'usage',
        type: 'object',
        label: 'Token消耗',
        desc: 'Token使用统计',
        children: [
          { name: 'prompt_tokens', label: '提示词Token' },
          { name: 'completion_tokens', label: '生成Token' },
          { name: 'total_tokens', label: '总Token' }
        ]
      })
      break
    case 'http':
      outputs.push({ name: 'status_code', type: 'number', label: '状态码', desc: 'HTTP状态码' })
      outputs.push({ name: 'status', type: 'number', label: '状态码', desc: 'HTTP状态码（别名）' })
      outputs.push({ name: 'success', type: 'boolean', label: '成功标志', desc: '请求是否成功（2xx状态码）' })
      outputs.push({ name: 'body', type: 'any', label: '响应体', desc: 'HTTP响应体原始数据' })
      outputs.push({ name: 'data', type: 'any', label: '响应数据', desc: 'HTTP响应数据（body别名）' })
      outputs.push({ name: 'headers', type: 'object', label: '响应头', desc: 'HTTP响应头' })
      outputs.push({ name: 'url', type: 'string', label: '请求URL', desc: '实际请求的URL' })
      outputs.push({ name: 'method', type: 'string', label: '请求方法', desc: 'HTTP请求方法' })
      break
    case 'knowledge':
      outputs.push({ name: 'results', type: 'array', label: '检索结果列表', desc: '匹配的知识片段数组' })
      outputs.push({ name: 'total', type: 'number', label: '结果数量', desc: '检索到的结果总数' })
      outputs.push({ name: 'top_content', type: 'string', label: '最相似内容', desc: '相似度最高的片段内容' })
      outputs.push({ name: 'top_similarity', type: 'number', label: '最高相似度', desc: '最高相似度分数（0-1）' })
      outputs.push({ name: 'combined_content', type: 'string', label: '合并内容', desc: '所有结果合并的文本（适合传给LLM）' })
      outputs.push({ name: 'kb_name', type: 'string', label: '知识库名称', desc: '检索的知识库名称' })
      break
    case 'intent':
      outputs.push({ name: 'intent', type: 'string', label: '意图类别', desc: '识别出的意图' })
      outputs.push({ name: 'category', type: 'string', label: '意图分类', desc: 'intent的别名' })
      outputs.push({ name: 'confidence', type: 'number', label: '置信度', desc: '识别可信度(0-1)' })
      outputs.push({ name: 'is_match', type: 'boolean', label: '是否匹配', desc: '是否匹配到意图' })
      outputs.push({ name: 'method', type: 'string', label: '识别方法', desc: 'llm或keyword' })
      outputs.push({ name: 'input_text', type: 'string', label: '输入文本', desc: '原始输入' })
      break
    case 'string':
      outputs.push({ name: 'result', type: 'string', label: '处理结果', desc: '字符串操作后的结果' })
      outputs.push({ name: 'text', type: 'string', label: '文本内容', desc: 'result的别名' })
      outputs.push({ name: 'length', type: 'number', label: '文本长度', desc: '字符数量' })
      outputs.push({ name: 'is_empty', type: 'boolean', label: '是否为空', desc: '文本是否为空' })
      outputs.push({ name: 'list', type: 'array', label: '列表结果', desc: '分割后的列表（split操作）' })
      outputs.push({ name: 'count', type: 'number', label: '列表长度', desc: '分割后的项目数' })
      outputs.push({ name: 'first', type: 'string', label: '第一项', desc: '列表的第一项' })
      outputs.push({ name: 'last', type: 'string', label: '最后一项', desc: '列表的最后一项' })
      break
  }
  
  return outputs
}

// 获取当前节点可用的所有上游变量
const getAvailableVariables = (currentNodeId) => {
  if (!currentNodeId) return []

  const predecessors = new Set()
  const queue = [currentNodeId]
  const visited = new Set()
  
  // 构建反向图：target -> [source1, source2...]
  const reverseEdgeMap = new Map()
  edges.value.forEach(e => {
    if (!reverseEdgeMap.has(e.target)) reverseEdgeMap.set(e.target, [])
    reverseEdgeMap.get(e.target).push(e.source)
  })
  
  // BFS 查找所有上游节点
  while(queue.length > 0) {
    const current = queue.shift()
    if (visited.has(current)) continue
    visited.add(current)
    
    const parents = reverseEdgeMap.get(current) || []
    parents.forEach(p => {
      if (!visited.has(p)) {
        predecessors.add(p)
        queue.push(p)
      }
    })
  }
  
  // 收集变量
  const variables = []
  predecessors.forEach(nodeId => {
    const node = nodes.value.find(n => n.id === nodeId)
    if (node) {
      const nodeOutputs = getNodeOutputs(node)
      nodeOutputs.forEach(out => {
        variables.push({
          ...out,
          nodeId: node.id,
          nodeLabel: node.data.label,
          // 构造引用字符串，如 {node-1.response}
          reference: `{${node.id}.${out.name}}` 
        })
      })
    }
  })
  
  return variables
}

// 变量选择器相关
const showVarSelector = ref(false)
const currentVarTarget = ref(null) // { object: dataObject, field: 'fieldName' }
const availableVars = ref([])
// 新增：变量配置相关状态
const showVarConfig = ref(false)
const selectedVariable = ref(null)
const subPropertyPath = ref('')

// 打开变量选择器
const openVarSelector = (targetObj, fieldName) => {
  if (!selectedNodeId.value) return
  
  // 重置状态
  showVarConfig.value = false
  selectedVariable.value = null
  subPropertyPath.value = ''
  
  // 计算可用变量
  availableVars.value = getAvailableVariables(selectedNodeId.value)
  
  if (availableVars.value.length === 0) {
    ElMessage.warning('当前节点没有前序节点，或前序节点无可用输出')
    return
  }
  
  currentVarTarget.value = { object: targetObj, field: fieldName }
  showVarSelector.value = true
}

// 选择变量
const selectVariable = (variable) => {
  selectedVariable.value = variable
  // 如果是对象或Any类型，或者有定义子属性，进入配置模式
  if (['object', 'any', 'array'].includes(variable.type) || variable.children?.length > 0) {
    subPropertyPath.value = ''
    showVarConfig.value = true
  } else {
    // 简单类型直接插入
    doInsert(variable.reference)
  }
}

// 获取完整引用字符串
const getFullReference = () => {
  if (!selectedVariable.value) return ''
  let ref = selectedVariable.value.reference
  if (subPropertyPath.value) {
    // 去掉末尾的 }
    ref = ref.slice(0, -1)
    // 添加属性路径
    ref += `.${subPropertyPath.value}}`
  }
  return ref
}

// 确认插入变量
const confirmInsertVar = () => {
  if (selectedVariable.value) {
    doInsert(getFullReference())
  }
}

// 执行插入操作
const doInsert = (reference) => {
  if (currentVarTarget.value) {
    const { object, field } = currentVarTarget.value
    // 简单追加到末尾
    const currentVal = object[field] || ''
    object[field] = currentVal + reference
    ElMessage.success(`已插入变量`)
  }
  showVarSelector.value = false
  showVarConfig.value = false
}

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

// 可拖拽的节点类型（排除开始和结束节点）
const draggableNodeTypes = computed(() => {
  return nodeTypes.filter(t => t.type !== 'start' && t.type !== 'end')
})

// 选中的节点
const selectedNode = computed(() => {
  return nodes.value.find(n => n.id === selectedNodeId.value)
})

// 选中的边
const selectedEdge = computed(() => {
  return edges.value.find(e => e.id === selectedEdgeId.value)
})

// 检查是否已有某类型节点
const hasNodeType = (type) => {
  return nodes.value.some(n => n.data.nodeType === type)
}

// 初始化默认节点（开始 + 结束）
const initDefaultNodes = () => {
  if (nodes.value.length === 0 && !workflowUuid.value) {
    console.log('初始化默认节点...')
    // 只在新建工作流时添加默认节点
    const startNodeType = nodeTypes.find(t => t.type === 'start')
    const endNodeType = nodeTypes.find(t => t.type === 'end')
    
    if (startNodeType) {
      console.log('添加开始节点')
      // 直接创建节点，不经过检查（因为是初始化）
      createNode(startNodeType, 150, 200)
    }
    
    if (endNodeType) {
      console.log('添加结束节点')
      // 直接创建节点，不经过检查（因为是初始化）
      createNode(endNodeType, 650, 200)
    }
    
    // 添加节点后，居中显示
    nextTick(() => {
      console.log('居中显示画布，节点数量:', nodes.value.length)
      fitView()
    })
  }
}

// 创建节点（不做重复检查）
const createNode = (nodeType, x, y) => {
  const newNode = {
    id: `${nodeType.type}-${nodeIdCounter++}`,
    type: 'custom',
    position: { x: Math.round(x), y: Math.round(y) },
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
      url: '',
      method: 'GET',
      headers: {},
      headerParams: [],
      body: '',
      timeout: 10,
      retryCount: 0,
      validateSSL: true,
      followRedirect: true,
      // 知识库配置
      kb_uuid: '',
      query: '',
      top_k: 5,
      similarity_threshold: 0.7,
      // 意图识别配置
      recognition_mode: 'llm',
      confidence_threshold: 0.6,
      intent_categories: [],
      input_text: '',
      agent_uuid: '',
      keyword_mapping: '',
      // 字符串处理配置
      operation: 'template',
      template: '',
      input: '',
      texts: '',
      separator: '',
      find: '',
      replace_with: '',
      replace_all: true,
      case_sensitive: true,
      start: 0,
      end: 0,
      max_split: -1,
      pattern: '',
      group: 0,
      find_all: false
    }
  }

  nodes.value.push(newNode)
  console.log('节点已创建:', nodeType.label, '当前总数:', nodes.value.length)
}

// 组件挂载后初始化
onMounted(() => {
  loadWorkflow()
  loadLLMModels()
  loadKnowledgeBases()
  loadAgents()
})

// 加载 LLM 模型
const loadLLMModels = async () => {
  try {
    const res = await getActiveLLMModels()
    // 分组处理
    const groups = {}
    // res.data 可能是数组或 { items: [] }，根据API定义应该是数组
    const models = Array.isArray(res) ? res : (res.data || [])
    
    models.forEach(model => {
      const provider = model.provider || 'unknown'
      if (!groups[provider]) {
        groups[provider] = []
      }
      groups[provider].push(model)
    })
    
    llmModelOptions.value = Object.keys(groups).map(provider => ({
      label: getProviderLabel(provider),
      options: groups[provider]
    }))
  } catch (e) {
    console.error('加载LLM模型失败', e)
  }
}

const getProviderLabel = (provider) => {
    const map = {
        'openai': 'OpenAI',
        'qwen': '通义千问',
        'zhipu': '智谱AI',
        'moonshot': 'Moonshot (Kimi)',
        'deepseek': 'DeepSeek',
        'doubao': '豆包 (Doubao)'
    }
    return map[provider.toLowerCase()] || provider
}

// 加载知识库列表
const loadKnowledgeBases = async () => {
  try {
    const res = await getKnowledgeBases({ page: 1, page_size: 100 })
    // 根据API返回格式提取知识库列表
    const kbs = res.data?.knowledge_bases || res.data || []
    
    knowledgeBases.value = kbs.map(kb => ({
      uuid: kb.uuid,
      name: kb.name,
      description: kb.description,
      scope_type: kb.scope_type,
      document_count: kb.document_count || 0,
      chunk_count: kb.chunk_count || 0
    }))
    
    console.log('知识库加载完成:', knowledgeBases.value.length, '个')
  } catch (error) {
    console.error('加载知识库失败:', error)
    ElMessage.warning('加载知识库列表失败，请检查网络连接')
  }
}

// 加载智能体列表
const loadAgents = async () => {
  try {
    const res = await getAgents({ page: 1, page_size: 100 })
    // 提取智能体列表
    const agentList = res.data?.agents || res.data?.items || res.data || []
    
    agents.value = agentList.map(agent => ({
      uuid: agent.uuid,
      name: agent.name,
      description: agent.description,
      llm_model_name: agent.llm_model_name || '未配置模型',
      llm_model_id: agent.llm_model_id
    }))
    
    console.log('智能体加载完成:', agents.value.length, '个')
  } catch (error) {
    console.error('加载智能体失败:', error)
    // 不显示错误消息，可能是权限问题
  }
}

// 拖拽相关
let draggedNodeType = null
let dropNodeCounter = 0  // 拖放节点计数器

// 开始拖拽
const onDragStart = (event, nodeType) => {
  if ((nodeType.type === 'start' || nodeType.type === 'end') && hasNodeType(nodeType.type)) {
    event.preventDefault()
    return
  }
  draggedNodeType = nodeType
  event.dataTransfer.effectAllowed = 'copy'
  event.dataTransfer.setData('application/nodeType', JSON.stringify(nodeType))
}

// 拖拽经过画布
const onDragOver = (event) => {
  event.preventDefault()
  event.dataTransfer.dropEffect = 'copy'
}

// 放置到画布
const onDrop = (event) => {
  event.preventDefault()
  event.stopPropagation()
  
  if (!draggedNodeType) {
    console.warn('没有拖拽的节点类型')
    return
  }
  
  try {
    // 获取画布的边界矩形
    const { left, top } = vueFlowRef.value.getBoundingClientRect()
    
    // 计算鼠标相对于画布左上角的坐标
    const x = event.clientX - left
    const y = event.clientY - top
    
    // 将屏幕坐标转换为画布坐标
    const position = project({ x, y })
    
    console.log('放置节点到位置:', {
      屏幕坐标: { x: event.clientX, y: event.clientY },
      相对坐标: { x, y },
      画布坐标: position
    })
    
    // 创建节点
    addNodeAtPosition(draggedNodeType, position.x, position.y)
    
    // 增加计数器
    dropNodeCounter++
    
  } catch (error) {
    console.error('拖放节点失败:', error, error.stack)
    // 降级方案：使用固定位置
    addNodeAtPosition(draggedNodeType, 400, 200)
  } finally {
    draggedNodeType = null
  }
}

// 在指定位置添加节点（拖拽时使用）
const addNodeAtPosition = (nodeType, x, y) => {
  if ((nodeType.type === 'start' || nodeType.type === 'end') && hasNodeType(nodeType.type)) {
    ElMessage.warning(`${nodeType.label}节点只能有一个`)
    return
  }

  console.log('添加节点:', nodeType.label, '位置:', { x, y })

  // 创建节点
  createNode(nodeType, x, y)
  
  // 获取刚创建的节点
  const newNode = nodes.value[nodes.value.length - 1]
  
  // 自动选中新添加的节点
  nextTick(() => {
    selectedNodeId.value = newNode.id
    showConfigDrawer.value = true
    console.log('节点已选中，配置抽屉已打开')
  })
  
  ElMessage.success(`已添加${nodeType.label}节点`)
}

// 删除节点
const deleteNode = (nodeId) => {
  const node = nodes.value.find(n => n.id === nodeId)
  if (!node) return

  if (node.data.nodeType === 'start' || node.data.nodeType === 'end') {
    ElMessage.warning('开始和结束节点不能删除')
    return
  }

  const nodeName = node?.data.label || '该节点'
  
  ElMessageBox.confirm(
    `确定要删除「${nodeName}」吗？相关的连接线也会被删除。`,
    '删除节点',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
      center: true
    }
  ).then(() => {
    nodes.value = nodes.value.filter(n => n.id !== nodeId)
    edges.value = edges.value.filter(e => e.source !== nodeId && e.target !== nodeId)
    if (selectedNodeId.value === nodeId) {
      selectedNodeId.value = null
      showConfigDrawer.value = false
    }
    ElMessage.success(`「${nodeName}」已删除`)
  }).catch(() => {})
}

// 节点点击
const onNodeClick = ({ node }) => {
  selectedNodeId.value = node.id
  
  // Start 节点：尝试解析 inputSchema 到 parameters
  if (node.data.nodeType === 'start') {
    if (!node.data.parameters && node.data.inputSchema) {
      try {
        const schema = JSON.parse(node.data.inputSchema)
        const params = []
        if (schema.properties) {
          for (const [key, value] of Object.entries(schema.properties)) {
            params.push({
              name: key,
              type: value.type || 'string',
              description: value.description || '',
              required: (schema.required || []).includes(key)
            })
          }
        }
        node.data.parameters = params
      } catch (e) {
        console.warn('解析 Start 节点 Schema 失败', e)
        node.data.parameters = []
      }
    } else if (!node.data.parameters) {
      node.data.parameters = []
    }
  }

  // End 节点：尝试解析 outputMapping 到 outputContent
  if (node.data.nodeType === 'end') {
    if (node.data.outputMapping) {
      try {
        const mapping = JSON.parse(node.data.outputMapping)
        // 兼容旧数据：如果有多字段，取第一个，或者取名为 'output' 的字段
        node.data.outputContent = mapping.output || Object.values(mapping)[0] || ''
      } catch (e) {
        // 如果解析失败，可能是旧的直接字符串格式？或者直接置空
        console.warn('解析 End 节点 Mapping 失败', e)
        node.data.outputContent = ''
      }
    } else {
      node.data.outputContent = ''
    }
  }

  // HTTP 节点：尝试解析 headers 到 headerParams
  if (node.data.nodeType === 'http') {
    if (!node.data.headerParams && node.data.headers) {
      try {
        const headers = JSON.parse(node.data.headers)
        const params = []
        for (const [key, value] of Object.entries(headers)) {
          params.push({ key, value: String(value) })
        }
        node.data.headerParams = params
      } catch (e) {
        console.warn('解析 HTTP Headers 失败', e)
        node.data.headerParams = []
      }
    } else if (!node.data.headerParams) {
      node.data.headerParams = []
    }
  }

  showConfigDrawer.value = true
}

// 边点击（选中边进行配置）
const onEdgeClick = ({ edge }) => {
  selectedNodeId.value = null  // 清空节点选择
  selectedEdgeId.value = edge.id  // 选中边
  
  // 确保边有条件数据结构
  const edgeData = edges.value.find(e => e.id === edge.id)
  if (edgeData && !edgeData.condition) {
    edgeData.condition = null  // 初始化为无条件
  }
  if (edgeData && !edgeData.label) {
    edgeData.label = null  // 初始化标签
  }
  
  showConfigDrawer.value = true
}

// 条件类型改变时初始化字段
const onConditionTypeChange = (value) => {
  if (!selectedEdge.value) return
  
  if (value === null || value === 'always') {
    // 无条件或总是执行，清空字段
    selectedEdge.value.conditionField = ''
    selectedEdge.value.conditionValue = ''
  } else if (value === 'intent_match') {
    // 意图匹配，默认字段为intent
    selectedEdge.value.conditionField = 'intent'
    selectedEdge.value.conditionValue = selectedEdge.value.conditionValue || ''
  } else {
    // 其他条件，清空字段让用户填写
    selectedEdge.value.conditionField = selectedEdge.value.conditionField || ''
    selectedEdge.value.conditionValue = selectedEdge.value.conditionValue || ''
  }
}

// 删除选中的边
const deleteSelectedEdge = () => {
  if (!selectedEdge.value) return
  
  const sourceNode = nodes.value.find(n => n.id === selectedEdge.value.source)
  const targetNode = nodes.value.find(n => n.id === selectedEdge.value.target)
  const fromName = sourceNode?.data.label || '节点'
  const toName = targetNode?.data.label || '节点'
  
  ElMessageBox.confirm(
    `确定要删除从「${fromName}」到「${toName}」的连线吗？`,
    '删除连线',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
      center: true
    }
  ).then(() => {
    edges.value = edges.value.filter(e => e.id !== selectedEdge.value.id)
    selectedEdgeId.value = null
    showConfigDrawer.value = false
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
    type: edgeType.value,
    animated: false, // 默认静态
    style: { stroke: '#b1b3b8', strokeWidth: 2 } // 默认灰色
  }

  edges.value.push(newEdge)
  ElMessage.success('连接创建成功')
}

// 切换连线样式
const changeEdgeType = () => {
  // 更新所有现有连线的类型
  edges.value.forEach(edge => {
    edge.type = edgeType.value
  })
  ElMessage.success(`已切换到${getEdgeTypeName(edgeType.value)}样式`)
}

// 获取连线类型名称
const getEdgeTypeName = (type) => {
  const names = {
    'smoothstep': '平滑直角',
    'step': '直角折线',
    'default': '贝塞尔曲线',
    'straight': '直线',
    'simplebezier': '简单曲线'
  }
  return names[type] || type
}

// 自动布局
const autoLayout = () => {
  if (nodes.value.length === 0) {
    ElMessage.info('画布为空')
    return
  }

  const startNodes = nodes.value.filter(n => n.data.nodeType === 'start')
  const endNodes = nodes.value.filter(n => n.data.nodeType === 'end')
  
  if (startNodes.length === 0) {
    ElMessage.warning('请先添加开始节点')
    return
  }

  const nodeMap = new Map(nodes.value.map(n => [n.id, n]))
  const edgeMap = new Map() // source -> targets
  const reverseEdgeMap = new Map() // target -> sources

  // 构建边的映射
  edges.value.forEach(e => {
    if (!edgeMap.has(e.source)) edgeMap.set(e.source, [])
    edgeMap.get(e.source).push(e.target)
    
    if (!reverseEdgeMap.has(e.target)) reverseEdgeMap.set(e.target, [])
    reverseEdgeMap.get(e.target).push(e.source)
  })

  // 计算每个节点的层级（从开始节点开始）
  const nodeLayer = new Map()
  const visited = new Set()
  
  // 第一层：开始节点（固定在最左边）
  startNodes.forEach(n => {
    nodeLayer.set(n.id, 0)
    visited.add(n.id)
  })

  // BFS 计算其他节点的层级
  let queue = startNodes.map(n => n.id)
  
  while (queue.length > 0) {
    const nodeId = queue.shift()
    const currentLayer = nodeLayer.get(nodeId)
    const neighbors = edgeMap.get(nodeId) || []
    
    neighbors.forEach(neighborId => {
      const newLayer = currentLayer + 1
      // 更新层级（取最大值，确保节点在所有前驱节点之后）
      if (!nodeLayer.has(neighborId) || nodeLayer.get(neighborId) < newLayer) {
        nodeLayer.set(neighborId, newLayer)
      }
      
      if (!visited.has(neighborId)) {
        visited.add(neighborId)
        queue.push(neighborId)
      }
    })
  }

  // 如果有结束节点，确保它们在最右边（最后一层）
  if (endNodes.length > 0) {
    const maxLayer = Math.max(...Array.from(nodeLayer.values()))
    endNodes.forEach(n => {
      if (nodeLayer.has(n.id)) {
        nodeLayer.set(n.id, maxLayer)
      }
    })
  }

  // 按层级分组节点
  const layers = []
  nodeLayer.forEach((layer, nodeId) => {
    if (!layers[layer]) layers[layer] = []
    layers[layer].push(nodeId)
  })

  // 布局节点
  const layerWidth = 280 // 层间距
  const nodeHeight = 120 // 节点间距
  const startX = 150 // 起始X坐标
  const startY = 200 // 起始Y坐标

  layers.forEach((layerNodes, layerIndex) => {
    // 计算这一层的总高度
    const totalHeight = (layerNodes.length - 1) * nodeHeight
    // 计算起始Y坐标使整层垂直居中
    const layerStartY = startY - totalHeight / 2
    
    layerNodes.forEach((nodeId, nodeIndex) => {
      const node = nodeMap.get(nodeId)
      if (node) {
        node.position = {
          x: startX + layerIndex * layerWidth,
          y: layerStartY + nodeIndex * nodeHeight
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
    // Start 节点特殊处理：验证参数名并生成 inputSchema
    if (selectedNode.value.data.nodeType === 'start') {
      const params = selectedNode.value.data.parameters || []
      
      // 验证参数名
      for (const p of params) {
        if (!p.name || !p.name.trim()) {
          ElMessage.warning('参数名不能为空')
          return
        }
        if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(p.name)) {
          ElMessage.warning(`参数名 "${p.name}" 不合法，只能包含字母、数字和下划线，且不能以数字开头`)
          return
        }
      }

      // 检查重复参数名
      const names = params.map(p => p.name)
      if (new Set(names).size !== names.length) {
        ElMessage.warning('参数名不能重复')
        return
      }

      const schema = {
        type: 'object',
        properties: {},
        required: []
      }
      
      params.forEach(p => {
        if (p.name) {
          schema.properties[p.name] = {
            type: p.type,
            description: p.description
          }
          if (p.required) {
            schema.required.push(p.name)
          }
        }
      })
      
      selectedNode.value.data.inputSchema = JSON.stringify(schema, null, 2)
    }

    // End 节点特殊处理：直接保存 outputContent 到 outputMapping
    // 为了兼容后端，我们将内容包装成一个 JSON 对象，或者直接作为 text 返回
    // 这里我们约定：End 节点的 outputMapping 存储为一个包含 'output' 字段的 JSON，或者直接存字符串
    // 为了简单且通用，我们将单一内容存入一个固定的字段 "output" 中，方便后端统一取用
    if (selectedNode.value.data.nodeType === 'end') {
      if (!selectedNode.value.data.outputContent) {
        // 允许为空？通常不建议，给个默认值或允许空
        selectedNode.value.data.outputContent = ''
      }
      
      // 构造符合后端预期的 JSON 结构
      const mapping = {
        output: selectedNode.value.data.outputContent
      }
      
      selectedNode.value.data.outputMapping = JSON.stringify(mapping, null, 2)
    }

    // HTTP 节点特殊处理：从 headerParams 生成 headers
    if (selectedNode.value.data.nodeType === 'http') {
      const headers = {}
      const params = selectedNode.value.data.headerParams || []
      params.forEach(p => {
        if (p.key) headers[p.key] = p.value
      })
      selectedNode.value.data.headers = JSON.stringify(headers, null, 2)
    }

    selectedNode.value.data.configured = true
    ElMessage.success('配置已保存')
  }
}

// 添加开始节点参数
const addStartParameter = () => {
  if (!selectedNode.value.data.parameters) {
    selectedNode.value.data.parameters = []
  }
  selectedNode.value.data.parameters.push({
    name: '',
    type: 'string',
    description: '',
    required: true
  })
}

// 删除开始节点参数
const removeStartParameter = (index) => {
  selectedNode.value.data.parameters.splice(index, 1)
}

// 添加HTTP Header
const addHeaderParam = () => {
  if (!selectedNode.value.data.headerParams) {
    selectedNode.value.data.headerParams = []
  }
  selectedNode.value.data.headerParams.push({ key: '', value: '' })
}

// 删除HTTP Header
const removeHeaderParam = (index) => {
  selectedNode.value.data.headerParams.splice(index, 1)
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

    const apiEdges = edges.value.map(edge => {
      const edgeData = {
        id: edge.id,
        source: edge.source,
        target: edge.target
      }
      
      // 添加标签
      if (edge.label) {
        edgeData.label = edge.label
      }
      
      // 添加条件（从UI字段转换为条件对象）
      if (edge.condition && edge.condition !== null) {
        edgeData.condition = {
          type: edge.condition,
          field: edge.conditionField || (edge.condition === 'intent_match' ? 'intent' : ''),
          value: edge.conditionValue || ''
        }
      } else if (typeof edge.condition === 'object' && edge.condition !== null) {
        // 如果condition已经是对象，直接使用
        edgeData.condition = edge.condition
      }
      
      return edgeData
    })

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

// 处理运行点击
const handleRun = async () => {
  // 先保存
  await saveWorkflow()
  
  // 检查保存是否成功（必须有UUID才能执行）
  if (!workflowUuid.value) {
    ElMessage.error('工作流保存失败，无法执行')
    return
  }
  
  // 找到开始节点
  const startNode = nodes.value.find(n => n.data.nodeType === 'start')
  if (!startNode) {
    ElMessage.warning('找不到开始节点')
    return
  }

  // 解析参数
  startNodeParams.value = startNode.data.parameters || []
  runResult.value = null // 重置结果
  
  // 使用对话框而不是执行面板
  showRunDialog.value = true
}

// 确认运行
const confirmRun = async () => {
  // 检查工作流是否已保存
  if (!workflowUuid.value) {
    ElMessage.error('工作流尚未保存，无法执行')
    return
  }
  
  // 验证必填参数
  for (const param of startNodeParams.value) {
    if (param.required && !runParams.value[param.name] && runParams.value[param.name] !== 0 && runParams.value[param.name] !== false) {
      ElMessage.warning(`请输入 ${param.name}`)
      return
    }
  }

  running.value = true
  runResult.value = null
  
  // 重置所有连线样式
  edges.value.forEach(edge => {
    edge.animated = false
    edge.style = { stroke: '#b1b3b8', strokeWidth: 2 }
  })
  
  try {
    const res = await executeWorkflow(workflowUuid.value, {
      input: runParams.value
    })
    
    runResult.value = res.data
    
    // 高亮执行路径
    if (runResult.value?.node_executions) {
      highlightExecutionPath(runResult.value.node_executions)
    }
    
    // 关闭运行对话框，显示结果对话框
    showRunDialog.value = false
    showResultDialog.value = true
    
    ElMessage.success('执行完成')
  } catch (error) {
    runResult.value = {
      status: 'failed',
      error_message: error.response?.data?.message || error.message,
      output: null,
      execution_time: 0,
      node_executions: []
    }
    
    // 关闭运行对话框，显示结果对话框
    showRunDialog.value = false
    showResultDialog.value = true
    
    ElMessage.error('执行失败: ' + (error.response?.data?.message || error.message))
  } finally {
    running.value = false
  }
}

// 高亮执行路径
const highlightExecutionPath = (executions) => {
  // 获取所有执行过的节点ID
  const executedNodeIds = new Set(executions.map(n => n.node_id))
  // 获取失败的节点ID
  const failedNodeIds = new Set(executions.filter(n => n.status === 'failed').map(n => n.node_id))
  
  // 遍历边，如果source和target都在executedNodeIds中，则高亮
  // 简单的逻辑：如果是线性或简单分支，两端都执行意味着边被经过
  // 对于复杂条件分支，这种逻辑通常也是正确的（未执行的分支节点不在executedNodeIds中）
  
  edges.value.forEach(edge => {
    if (executedNodeIds.has(edge.source) && executedNodeIds.has(edge.target)) {
      // 检查target是否失败，如果是，这条路径也算走了，但可能用不同颜色？
      // 这里简化处理，统一高亮为“流过”
      edge.animated = true
      edge.style = { stroke: '#409eff', strokeWidth: 3 } // 蓝色高亮
      
      // 如果路径上有失败节点，可以用红色
      if (failedNodeIds.has(edge.target) || failedNodeIds.has(edge.source)) {
        edge.style = { stroke: '#f56c6c', strokeWidth: 3 }
      }
    }
  })
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
  if (!workflowUuid.value) {
    // 新建工作流，添加默认节点
    initDefaultNodes()
    return
  }
  
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
    edges.value = (workflow.edges || []).map(edge => {
      const edgeData = {
        ...edge,
        type: edgeType.value,
        animated: false, // 默认静态
        style: { stroke: '#b1b3b8', strokeWidth: 2 } // 默认灰色
      }
      
      // 将条件对象转换为UI字段
      if (edge.condition && typeof edge.condition === 'object') {
        edgeData.condition = edge.condition.type
        edgeData.conditionField = edge.condition.field || ''
        edgeData.conditionValue = edge.condition.value || ''
      } else {
        edgeData.condition = null
        edgeData.conditionField = ''
        edgeData.conditionValue = ''
      }
      
      return edgeData
    })
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
  cursor: move;
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
  user-select: none;
}

.node-add-btn:hover:not(.disabled) .btn-content {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.15);
  transform: translateY(-1px);
}

.node-add-btn:active:not(.disabled) .btn-content {
  transform: scale(0.98);
}

.node-add-btn.disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.node-add-btn.disabled .btn-content {
  background: #f5f7fa;
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
  width: 180px;
  height: 48px;
  background: transparent;
  border: none;
  border-radius: 8px;
  overflow: visible;
  transition: all 0.3s;
  cursor: pointer;
}

.workflow-node:hover {
  transform: translateY(-2px);
}

.workflow-node.selected .node-header {
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.3);
  border: 2px solid #409eff;
}

.node-header {
  width: 100%;
  height: 100%;
  padding: 0 12px;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 8px;
  border-radius: 8px;
  border: 2px solid transparent;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  transition: all 0.3s;
}

.node-header:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.18);
}

.node-title {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.node-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-icon {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
  background: rgba(255, 255, 255, 0.9);
  cursor: help;
}

.status-icon.success {
  color: #67c23a;
}

.status-icon.warning {
  color: #e6a23c;
}

.delete-btn {
  width: 22px;
  height: 22px;
  padding: 0;
  background: rgba(255, 255, 255, 0.95);
  border: none;
  opacity: 0;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #f56c6c;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}

.workflow-node:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  background: #f56c6c;
  color: #fff;
  transform: scale(1.15);
  box-shadow: 0 2px 8px rgba(245, 108, 108, 0.4);
}

.node-handle {
  width: 10px;
  height: 10px;
  border: 2px solid #fff;
  background: #909399;
  transition: all 0.3s;
  border-radius: 50%;
  opacity: 0.8;
}

.node-handle:hover {
  width: 14px;
  height: 14px;
  background: #409eff;
  border-width: 3px;
  box-shadow: 0 0 0 4px rgba(64, 158, 255, 0.2);
  opacity: 1;
}

.config-content {
  padding-bottom: 20px;
}

/* 参数列表容器 */
.params-container {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  overflow: hidden;
}

/* 表头 */
.params-header {
  display: flex;
  align-items: center;
  background: #f5f7fa;
  padding: 8px 12px;
  font-size: 12px;
  color: #909399;
  border-bottom: 1px solid #ebeef5;
}

/* 列表项 */
.param-row-item {
  display: flex;
  align-items: flex-start;
  padding: 12px;
  border-bottom: 1px solid #ebeef5;
  transition: background 0.2s;
  gap: 12px;
}

.param-row-item:last-child {
  border-bottom: none;
}

.param-row-item:hover {
  background-color: #f9fafc;
}

/* 列宽控制 */
.col-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0; /* 防止 input 撑开 */
}

.col-type {
  width: 90px;
  flex-shrink: 0;
}

.col-req {
  width: 50px;
  flex-shrink: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  padding-top: 6px;
}

.col-action {
  width: 30px;
  flex-shrink: 0;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding-top: 6px;
}

/* 输入框样式微调 */
.param-name-input :deep(.el-input__wrapper) {
  box-shadow: none;
  border-bottom: 1px solid #dcdfe6;
  border-radius: 0;
  padding-left: 0;
}

.param-name-input :deep(.el-input__wrapper:hover) {
  border-bottom-color: #409eff;
}

.param-name-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: none;
  border-bottom-color: #409eff;
}

.param-desc-input :deep(.el-input__wrapper) {
  box-shadow: none;
  background: transparent;
  padding-left: 0;
}

.param-desc-input :deep(.el-input__inner) {
  font-size: 12px;
  color: #909399;
}

/* 删除按钮 */
.row-delete-btn {
  opacity: 0;
  transition: opacity 0.2s;
}

.param-row-item:hover .row-delete-btn {
  opacity: 1;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px 0;
  color: #909399;
  font-size: 13px;
  gap: 8px;
  background: #fff;
}

/* 添加按钮 */
.add-param-btn {
  width: 100%;
  border: none;
  border-top: 1px solid #ebeef5;
  border-radius: 0;
  height: 40px;
  color: #409eff;
}

.add-param-btn:hover {
  background-color: #f0f9eb;
  color: #67c23a;
}

/* 变量插入相关 */
.input-with-var {
  position: relative;
  width: 100%;
}

:deep(.el-form-item__content) {
  width: 100%; /* 确保表单内容占满宽度 */
}

.params-container {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  overflow: hidden;
  width: 100%; /* 强制占满 */
  box-sizing: border-box;
}

.var-trigger {
  position: absolute;
  right: 8px;
  top: 8px;
  padding: 4px 8px;
  font-size: 12px;
  color: #409eff;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #dcdfe6;
  z-index: 2;
}

.var-trigger:hover {
  background: #ecf5ff;
  border-color: #c6e2ff;
}

.cell-var-trigger {
  position: absolute;
  right: 4px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 12px;
  padding: 2px 6px;
}

.cell-var-trigger.small {
  top: 12px;
}

.desc-var-input {
  position: relative;
}

/* 变量选择器列表 */
.var-list {
  max-height: 400px;
  overflow-y: auto;
}

.var-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-bottom: 1px solid #f0f2f5;
  cursor: pointer;
  transition: background 0.2s;
}

.var-item:hover {
  background: #f5f7fa;
}

.var-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.var-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.var-name {
  font-weight: 500;
  color: #303133;
}

.var-desc {
  font-size: 12px;
  color: #909399;
}

.var-source {
  font-size: 12px;
  color: #909399;
  background: #f4f4f5;
  padding: 2px 6px;
  border-radius: 4px;
}

.no-label-margin :deep(.el-form-item__label) {
  padding-bottom: 8px;
}

.mt-2 {
  margin-top: 12px;
}

/* 连接线样式 */
:deep(.vue-flow__edge-path) {
  stroke: #909399;
  stroke-width: 2;
  opacity: 0.6;
}

:deep(.vue-flow__edge.selected .vue-flow__edge-path) {
  stroke: #409eff;
  stroke-width: 3;
  opacity: 1;
}

:deep(.vue-flow__edge:hover .vue-flow__edge-path) {
  stroke: #409eff;
  stroke-width: 2.5;
  opacity: 1;
}

:deep(.vue-flow__connection-path) {
  stroke: #409eff;
  stroke-width: 2;
  stroke-dasharray: 5, 5;
  animation: dash 0.5s linear infinite;
}

@keyframes dash {
  to {
    stroke-dashoffset: -10;
  }
}

:deep(.el-drawer__body) {
  padding: 20px;
}

/* 强制表单项占满容器宽度 */
:deep(.el-form-item) {
  display: block; /* 确保 label 和 content 上下排列时占满 */
  margin-bottom: 24px;
}

.run-result {
  padding: 10px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.result-section {
  margin-bottom: 20px;
}

.section-title {
  font-size: 14px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 8px;
}

.section-title.error {
  color: #f56c6c;
}

.code-block {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
  color: #606266;
  overflow-x: auto;
}

.code-block pre {
  margin: 0;
}

.error-msg {
  color: #f56c6c;
  font-size: 13px;
  background: #fef0f0;
  padding: 10px;
  border-radius: 4px;
}

.node-exec-card {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 10px;
  background: #fff;
}

.node-exec-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 12px;
}

.node-id {
  font-weight: bold;
  color: #303133;
}

.node-type {
  color: #909399;
}

.node-output {
  background: #fafafa;
  padding: 8px;
  border-radius: 4px;
  font-size: 12px;
  color: #606266;
  overflow-x: auto;
}

.node-output pre {
  margin: 0;
}

.empty-params {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 30px 0;
}

.execution-panel-wrapper {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 500px;
  z-index: 10;
  background: #fff;
  box-shadow: -5px 0 15px rgba(0, 0, 0, 0.05);
  border-left: 1px solid #e4e7ed;
}

.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: transform 0.3s ease;
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateX(100%);
}

.var-config {
  padding: 0 10px;
}

.config-header {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 10px;
}

.selected-var-name {
  font-weight: bold;
  margin-left: 10px;
  font-size: 14px;
}

.config-body {
  margin-bottom: 20px;
}

.mb-3 {
  margin-bottom: 12px;
}

.current-ref {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 20px;
  border: 1px dashed #dcdfe6;
}

.current-ref .label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.current-ref .value {
  font-family: monospace;
  color: #409eff;
  font-weight: bold;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.config-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 10px;
}
</style>
