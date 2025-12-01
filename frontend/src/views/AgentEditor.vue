<template>
  <div class="agent-editor">
    <el-page-header @back="goBack" :content="pageTitle">
      <template #extra>
        <el-button type="primary" @click="saveAgent" :loading="saving">
          <el-icon><Document /></el-icon>
          保存
        </el-button>
      </template>
    </el-page-header>

    <div class="editor-content" v-loading="loading">
      <!-- 基本信息卡片 -->
      <el-card class="section-card">
        <template #header>
          <div class="card-header">
            <span class="card-title">基本信息</span>
          </div>
        </template>
        <el-form :model="agentForm" :rules="rules" ref="formRef" label-width="120px">
          <el-form-item label="智能体名称" prop="name">
            <el-input v-model="agentForm.name" placeholder="请输入智能体名称" style="max-width: 500px;" />
          </el-form-item>
          <el-form-item label="描述" prop="description">
            <el-input
              v-model="agentForm.description"
              type="textarea"
              :rows="3"
              placeholder="请输入智能体描述"
              style="max-width: 800px;"
            />
          </el-form-item>
          <el-form-item label="大模型" prop="llm_model_id">
            <el-select 
              v-model="agentForm.llm_model_id" 
              placeholder="选择大模型" 
              style="max-width: 500px;"
              clearable
              filterable
            >
              <el-option
                v-for="model in availableModels"
                :key="model.id"
                :label="model.display_name"
                :value="model.id"
              >
                <span style="float: left">{{ model.display_name }}</span>
                <span style="float: right; color: var(--el-text-color-secondary); font-size: 13px">
                  {{ model.provider }}
                </span>
              </el-option>
            </el-select>
            <div style="margin-top: 5px; font-size: 12px; color: #909399;">
              选择智能体使用的大语言模型，留空则使用系统默认模型
            </div>
          </el-form-item>
          <el-form-item label="状态" prop="is_active">
            <el-radio-group v-model="agentForm.is_active">
              <el-radio :label="1">激活</el-radio>
              <el-radio :label="0">禁用</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 系统提示词卡片 -->
      <el-card class="section-card">
        <template #header>
          <div class="card-header">
            <span class="card-title">系统提示词配置</span>
            <el-button text @click="showPromptTemplates">
              <el-icon><Document /></el-icon>
              使用模板
            </el-button>
          </div>
        </template>
        <div class="prompt-editor">
          <el-input
            v-model="agentForm.system_prompt"
            type="textarea"
            :rows="16"
            placeholder="请输入系统提示词，用于指导 AI 智能体的行为和角色定位

示例：
你是一个专业的物联网助手，擅长帮助用户管理和控制智能设备。
你的主要职责包括：
1. 解答用户关于设备使用的问题
2. 帮助用户控制智能设备（如开关灯、调节温度等）
3. 分析传感器数据并提供建议
4. 设置自动化场景

请用友好、专业的语气与用户交流。"
            class="prompt-textarea"
          />
          <div class="prompt-tips">
            <el-alert
              title="提示"
              type="info"
              :closable="false"
              show-icon
            >
              <ul>
                <li>系统提示词用于定义智能体的角色、能力和行为规范</li>
                <li>清晰的提示词能让智能体更好地理解用户需求</li>
                <li>建议包含：角色定位、主要功能、交互风格等</li>
              </ul>
            </el-alert>
          </div>
        </div>
      </el-card>

      <!-- 插件配置卡片 -->
      <el-card class="section-card">
        <template #header>
          <div class="card-header">
            <span class="card-title">插件配置 ({{ agentForm.plugin_ids.length }})</span>
            <el-button type="primary" @click="showPluginSelector">
              <el-icon><Plus /></el-icon>
              添加插件
            </el-button>
          </div>
        </template>
        <div class="plugins-config">
          <el-empty v-if="selectedPlugins.length === 0" description="暂未关联任何插件">
            <el-button type="primary" @click="showPluginSelector">添加插件</el-button>
          </el-empty>

          <div v-else class="plugins-list">
            <el-card
              v-for="plugin in selectedPlugins"
              :key="plugin.id"
              class="plugin-card"
              shadow="hover"
            >
              <template #header>
                <div class="plugin-card-header">
                  <span class="plugin-name">{{ plugin.name }}</span>
                  <el-button
                    type="danger"
                    size="small"
                    text
                    @click="removePlugin(plugin.id)"
                  >
                    <el-icon><Delete /></el-icon>
                    移除
                  </el-button>
                </div>
              </template>
              <div class="plugin-description">{{ plugin.description || '暂无描述' }}</div>
              <div class="plugin-meta">
                <el-tag size="small">{{ plugin.plugin_type }}</el-tag>
                <el-tag size="small" :type="plugin.is_active ? 'success' : 'info'">
                  {{ plugin.is_active ? '激活' : '禁用' }}
                </el-tag>
              </div>
            </el-card>
          </div>
        </div>
      </el-card>

      <!-- 知识库配置卡片 -->
      <el-card class="section-card">
        <template #header>
          <div class="card-header">
            <span class="card-title">知识库配置 ({{ knowledgeBases.length }})</span>
            <el-button type="primary" @click="showKnowledgeBaseSelector">
              <el-icon><Plus /></el-icon>
              添加知识库
            </el-button>
          </div>
        </template>
        <div class="knowledge-bases-config">
          <el-empty v-if="knowledgeBases.length === 0" description="暂未关联任何知识库">
            <el-button type="primary" @click="showKnowledgeBaseSelector">添加知识库</el-button>
          </el-empty>

          <div v-else class="knowledge-bases-list">
            <el-card
              v-for="kb in knowledgeBases"
              :key="kb.id"
              class="kb-card"
              shadow="hover"
            >
              <template #header>
                <div class="kb-card-header">
                  <div>
                    <span class="kb-name">{{ kb.knowledge_base_name }}</span>
                    <el-tag size="small" style="margin-left: 10px">{{ scopeTypeLabel(kb.scope_type) }}</el-tag>
                  </div>
                  <el-button
                    type="danger"
                    size="small"
                    text
                    @click="removeKnowledgeBase(kb.knowledge_base_uuid)"
                  >
                    <el-icon><Delete /></el-icon>
                    移除
                  </el-button>
                </div>
              </template>
              <div class="kb-info">
                <div class="kb-row">
                  <span class="kb-label">优先级:</span>
                  <el-input-number
                    v-model="kb.priority"
                    :min="1"
                    :max="10"
                    size="small"
                    @change="updateKBConfig(kb)"
                  />
                  <span class="kb-tip">（1-10，数字越大越优先）</span>
                </div>
                <div class="kb-row">
                  <span class="kb-label">启用:</span>
                  <el-switch
                    v-model="kb.is_enabled"
                    @change="updateKBConfig(kb)"
                  />
                </div>
                <div class="kb-row">
                  <span class="kb-label">返回结果数:</span>
                  <el-input-number
                    v-model="kb.top_k"
                    :min="1"
                    :max="20"
                    size="small"
                    @change="updateKBConfig(kb)"
                  />
                  <span class="kb-tip">（返回最相关的N条）</span>
                </div>
                <div class="kb-row">
                  <span class="kb-label">相似度阈值:</span>
                  <el-slider
                    v-model="kb.similarity_threshold"
                    :min="0.3"
                    :max="1.0"
                    :step="0.05"
                    :format-tooltip="(val) => `${(val * 100).toFixed(0)}%`"
                    style="width: 150px; margin: 0 10px;"
                    @change="updateKBConfig(kb)"
                  />
                  <span class="kb-value">{{ (kb.similarity_threshold * 100).toFixed(0) }}%</span>
                  <el-popover
                    placement="top"
                    width="250"
                    trigger="hover"
                  >
                    <template #reference>
                      <el-icon style="margin-left: 5px; cursor: help;"><QuestionFilled /></el-icon>
                    </template>
                    <div style="font-size: 13px; line-height: 1.6;">
                      <p><strong>相似度阈值说明：</strong></p>
                      <p>• 80-100%：极高相关（严格）</p>
                      <p>• 70-80%：高相关（推荐）</p>
                      <p>• 60-70%：中等相关</p>
                      <p>• <60%：低相关（宽松）</p>
                    </div>
                  </el-popover>
                </div>
                <div class="kb-row">
                  <span class="kb-label">文档:</span>
                  <span>{{ kb.document_count || 0 }} 个</span>
                </div>
              </div>
            </el-card>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 插件选择对话框 -->
    <el-dialog
      v-model="pluginSelectorVisible"
      title="选择插件"
      width="800px"
    >
      <el-input
        v-model="pluginSearchQuery"
        placeholder="搜索插件名称"
        clearable
        style="margin-bottom: 20px;"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>

      <el-table
        :data="filteredPlugins"
        @selection-change="handlePluginSelectionChange"
        max-height="400px"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="插件名称" width="180" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="plugin_type" label="类型" width="100" />
        <el-table-column label="状态" width="80">
          <template #default="scope">
            <el-tag size="small" :type="scope.row.is_active ? 'success' : 'info'">
              {{ scope.row.is_active ? '激活' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <template #footer>
        <el-button @click="pluginSelectorVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmPluginSelection">确定</el-button>
      </template>
    </el-dialog>

    <!-- 提示词模板对话框 -->
    <el-dialog
      v-model="templateDialogVisible"
      title="选择提示词模板"
      width="700px"
    >
      <div class="template-list">
        <el-card
          v-for="template in promptTemplates"
          :key="template.id"
          class="template-card"
          shadow="hover"
          @click="useTemplate(template)"
        >
          <div class="template-name">{{ template.name }}</div>
          <div class="template-desc">{{ template.description }}</div>
        </el-card>
      </div>
    </el-dialog>

    <!-- 知识库选择对话框 -->
    <el-dialog
      v-model="kbSelectorVisible"
      title="选择知识库"
      width="900px"
    >
      <div style="margin-bottom: 15px;">
        <el-alert
          title="批量添加知识库，优先级将自动从高到低分配"
          type="info"
          :closable="false"
        />
      </div>

      <el-table
        :data="availableKnowledgeBases"
        @selection-change="handleKBSelectionChange"
        max-height="400px"
        v-loading="kbLoading"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="知识库名称" min-width="200" />
        <el-table-column label="类型" width="100">
          <template #default="scope">
            <el-tag size="small">{{ scopeTypeLabel(scope.row.scope_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="document_count" label="文档数" width="80" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
      </el-table>

      <template #footer>
        <el-button @click="kbSelectorVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmKBSelection" :disabled="selectedKBUuids.length === 0">
          确定 (已选 {{ selectedKBUuids.length }} 个)
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, Plus, Delete, Search, QuestionFilled } from '@element-plus/icons-vue'
import { getAgent, updateAgent } from '@/api/agent'
import { getPlugins } from '@/api/plugin'
import { getActiveLLMModels } from '@/api/llm-model'
import { getPromptTemplates } from '@/api/prompt-template'
import { 
  getAvailableKnowledgeBases,
  getAgentKnowledgeBases, 
  batchAddAgentKnowledgeBases,
  updateAgentKnowledgeBase,
  removeAgentKnowledgeBase
} from '@/api/knowledgeBases'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const saving = ref(false)
const formRef = ref(null)
const pluginSelectorVisible = ref(false)
const templateDialogVisible = ref(false)
const pluginSearchQuery = ref('')
const availablePlugins = ref([])
const availableModels = ref([])
const selectedPluginIds = ref([])

// 知识库相关
const kbSelectorVisible = ref(false)
const kbLoading = ref(false)
const availableKnowledgeBases = ref([])
const knowledgeBases = ref([])
const selectedKBUuids = ref([])

const agentUuid = computed(() => route.params.uuid)
const pageTitle = computed(() => agentForm.name || '智能体编排')

const agentForm = reactive({
  id: null,
  uuid: null,
  name: '',
  description: '',
  system_prompt: '',
  plugin_ids: [],
  llm_model_id: null,
  is_active: 1
})

const rules = {
  name: [
    { required: true, message: '请输入智能体名称', trigger: 'blur' },
    { min: 1, max: 100, message: '长度在 1 到 100 个字符', trigger: 'blur' }
  ]
}

// 提示词模板（从后端动态加载）
const promptTemplates = ref([])

// 已选中的插件详情
const selectedPlugins = computed(() => {
  return availablePlugins.value.filter(plugin => 
    agentForm.plugin_ids.includes(plugin.id)
  )
})

// 筛选后的插件列表
const filteredPlugins = computed(() => {
  if (!pluginSearchQuery.value) {
    return availablePlugins.value
  }
  const query = pluginSearchQuery.value.toLowerCase()
  return availablePlugins.value.filter(plugin =>
    plugin.name.toLowerCase().includes(query) ||
    (plugin.description && plugin.description.toLowerCase().includes(query))
  )
})

// 返回上一页
const goBack = () => {
  router.push('/agents')
}

// 加载智能体详情
const loadAgent = async () => {
  if (!agentUuid.value) return
  
  loading.value = true
  try {
    const response = await getAgent(agentUuid.value)
    const agent = response.data
    Object.assign(agentForm, {
      id: agent.id,
      uuid: agent.uuid,
      name: agent.name,
      description: agent.description,
      system_prompt: agent.system_prompt || '',
      plugin_ids: agent.plugin_ids || [],
      llm_model_id: agent.llm_model_id || null,
      is_active: agent.is_active
    })
  } catch (error) {
    ElMessage.error('加载智能体信息失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 加载可用插件
const loadPlugins = async () => {
  try {
    const response = await getPlugins({ limit: 1000 })
    availablePlugins.value = response.data.items
  } catch (error) {
    ElMessage.error('加载插件列表失败')
    console.error(error)
  }
}

// 加载可用模型
const loadModels = async () => {
  try {
    const response = await getActiveLLMModels()
    availableModels.value = response.data || response || []
  } catch (error) {
    console.error('加载模型列表失败', error)
  }
}

// 保存智能体
const saveAgent = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
  } catch {
    ElMessage.warning('请检查基本信息是否填写正确')
    activeTab.value = 'basic'
    return
  }
  
  saving.value = true
  try {
    await updateAgent(agentUuid.value, agentForm)
    ElMessage.success('保存成功')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
    console.error(error)
  } finally {
    saving.value = false
  }
}

// 显示插件选择器
const showPluginSelector = () => {
  pluginSearchQuery.value = ''
  selectedPluginIds.value = [...agentForm.plugin_ids]
  pluginSelectorVisible.value = true
}

// 处理插件选择变化
const handlePluginSelectionChange = (selection) => {
  selectedPluginIds.value = selection.map(item => item.id)
}

// 确认插件选择
const confirmPluginSelection = () => {
  agentForm.plugin_ids = [...selectedPluginIds.value]
  pluginSelectorVisible.value = false
  ElMessage.success('插件配置已更新')
}

// 移除插件
const removePlugin = (pluginId) => {
  ElMessageBox.confirm('确定要移除此插件吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    agentForm.plugin_ids = agentForm.plugin_ids.filter(id => id !== pluginId)
    ElMessage.success('插件已移除')
  }).catch(() => {})
}

// 加载提示词模板
const loadPromptTemplates = async () => {
  try {
    const response = await getPromptTemplates({
      is_active: true,
      page: 1,
      page_size: 100
    })
    promptTemplates.value = response.data.items
  } catch (error) {
    console.error('加载提示词模板失败:', error)
    ElMessage.error('加载提示词模板失败')
  }
}

// 显示提示词模板
const showPromptTemplates = async () => {
  // 如果模板还未加载，先加载
  if (promptTemplates.value.length === 0) {
    await loadPromptTemplates()
  }
  templateDialogVisible.value = true
}

// 使用模板
const useTemplate = (template) => {
  ElMessageBox.confirm(
    '使用模板将覆盖当前的系统提示词，是否继续？',
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    agentForm.system_prompt = template.content
    templateDialogVisible.value = false
    ElMessage.success('模板已应用')
  }).catch(() => {})
}

// ============================================================================
// 知识库相关方法
// ============================================================================

// 作用域类型标签
const scopeTypeLabel = (scopeType) => {
  const labels = {
    system: '系统级',
    school: '学校级',
    course: '课程级',
    personal: '个人级'
  }
  return labels[scopeType] || scopeType
}

// 加载智能体的知识库列表
const loadKnowledgeBases = async () => {
  if (!agentUuid.value) return
  
  try {
    const response = await getAgentKnowledgeBases(agentUuid.value)
    const kbs = response.data.knowledge_bases || []
    // 确保每个知识库都有必要的配置字段
    knowledgeBases.value = kbs.map(kb => ({
      ...kb,
      top_k: kb.top_k || 5,
      similarity_threshold: kb.similarity_threshold || 0.70,
      retrieval_mode: kb.retrieval_mode || 'hybrid'
    }))
  } catch (error) {
    console.error('加载知识库列表失败:', error)
  }
}

// 显示知识库选择器
const showKnowledgeBaseSelector = async () => {
  kbLoading.value = true
  kbSelectorVisible.value = true
  selectedKBUuids.value = []
  
  try {
    const response = await getAvailableKnowledgeBases(agentUuid.value)
    availableKnowledgeBases.value = response.data.knowledge_bases || []
  } catch (error) {
    console.error('加载可用知识库失败:', error)
    ElMessage.error('加载可用知识库失败')
  } finally {
    kbLoading.value = false
  }
}

// 知识库选择变化
const handleKBSelectionChange = (selection) => {
  selectedKBUuids.value = selection.map(kb => kb.uuid)
}

// 确认知识库选择
const confirmKBSelection = async () => {
  if (selectedKBUuids.value.length === 0) {
    return
  }
  
  // 构建批量添加数据，优先级从10递减（简化：只配置必要参数）
  const data = selectedKBUuids.value.map((uuid, index) => ({
    knowledge_base_uuid: uuid,
    priority: Math.max(1, 10 - index),  // 1-10范围
    is_enabled: true,
    // 其他参数使用后端默认值
    top_k: 5,
    similarity_threshold: 0.70,
    retrieval_mode: 'hybrid'
  }))
  
  try {
    await batchAddAgentKnowledgeBases(agentUuid.value, data)
    ElMessage.success(`成功添加 ${selectedKBUuids.value.length} 个知识库`)
    kbSelectorVisible.value = false
    await loadKnowledgeBases()
  } catch (error) {
    console.error('添加知识库失败:', error)
    ElMessage.error('添加知识库失败')
  }
}

// 更新知识库配置
const updateKBConfig = async (kb) => {
  try {
    await updateAgentKnowledgeBase(agentUuid.value, kb.knowledge_base_uuid, {
      priority: kb.priority,
      is_enabled: kb.is_enabled,
      top_k: kb.top_k,
      similarity_threshold: kb.similarity_threshold,
      retrieval_mode: kb.retrieval_mode
    })
    ElMessage.success('配置已更新')
  } catch (error) {
    console.error('更新配置失败:', error)
    ElMessage.error('更新配置失败')
    // 重新加载以恢复原值
    await loadKnowledgeBases()
  }
}

// 移除知识库
const removeKnowledgeBase = (kbUuid) => {
  ElMessageBox.confirm('确定要移除此知识库吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await removeAgentKnowledgeBase(agentUuid.value, kbUuid)
      ElMessage.success('知识库已移除')
      await loadKnowledgeBases()
    } catch (error) {
      console.error('移除知识库失败:', error)
      ElMessage.error('移除知识库失败')
    }
  }).catch(() => {})
}

onMounted(() => {
  loadAgent()
  loadPlugins()
  loadModels()
  loadPromptTemplates()
  loadKnowledgeBases()
})
</script>

<style scoped>
.agent-editor {
  padding: 20px;
}

.editor-content {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section-card {
  transition: box-shadow 0.3s;
}

.section-card:hover {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.prompt-editor {
  padding: 10px 0;
}

.prompt-textarea :deep(.el-textarea__inner) {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  line-height: 1.6;
}

.prompt-tips {
  margin-top: 15px;
}

.prompt-tips ul {
  margin: 10px 0 0 0;
  padding-left: 20px;
}

.prompt-tips li {
  margin: 5px 0;
}

.plugins-config {
  padding: 10px 0;
}

.plugins-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 15px;
}

.plugin-card {
  cursor: default;
}

.plugin-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.plugin-name {
  font-weight: 500;
  font-size: 15px;
}

.plugin-description {
  margin-bottom: 10px;
  color: #606266;
  font-size: 13px;
}

.plugin-meta {
  display: flex;
  gap: 8px;
}

.template-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 15px;
}

.template-card {
  cursor: pointer;
  transition: all 0.3s;
}

.template-card:hover {
  transform: translateY(-2px);
  border-color: #409eff;
}

.template-name {
  font-weight: 500;
  font-size: 15px;
  margin-bottom: 8px;
  color: #303133;
}

.template-desc {
  font-size: 13px;
  color: #909399;
}

/* 知识库配置相关样式 */
.knowledge-bases-config {
  min-height: 100px;
}

.knowledge-bases-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 15px;
}

.kb-card {
  cursor: default;
}

.kb-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.kb-name {
  font-weight: 500;
  font-size: 15px;
}

.kb-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.kb-row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  margin-bottom: 12px;
}

.kb-row:last-child {
  margin-bottom: 0;
}

.kb-label {
  font-weight: 500;
  color: #606266;
  min-width: 60px;
}

.kb-tip {
  font-size: 12px;
  color: #909399;
  margin-left: 5px;
}

.kb-value {
  font-weight: 600;
  color: #409eff;
  font-size: 14px;
  min-width: 40px;
  text-align: right;
}

.kb-status {
  margin-left: 5px;
  color: #67c23a;
}

.kb-status:not(.is-enabled) {
  color: #909399;
}
</style>

